import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from radar.management.commands.configure_midea_availability_gate import (
    AVAILABILITY_PROBE,
    PROBE_PENDING_ERROR,
)
from radar.models import OfficialSource, Organization, SourceAdmissionEvent
from radar.services.admission import source_is_admitted, transition_source
from tools.build_t4_source_catalog import build_rows


class MideaAvailabilityGateConfigurationTests(TestCase):
    def setUp(self) -> None:
        row = next(
            item
            for item in build_rows()
            if item["organization_name"] == "美的集团"
        )
        organization = Organization.objects.create(
            name=row["organization_name"],
            company_type=row["company_type"],
            industry=row["industry"],
            official_domain=row["official_domain"],
        )
        self.source = OfficialSource.objects.create(
            organization=organization,
            source_type=row["source_type"],
            source_url=row["source_url"],
            admission_evidence=row["admission_evidence"],
            adapter_name=row["adapter_name"],
            parser_config=json.loads(row["parser_config"]),
        )
        transition_source(
            self.source,
            to_state=OfficialSource.AdmissionState.VERIFIED,
            actor_label="test-owner",
            reason="verified",
            evidence="official Midea recruitment source",
        )
        transition_source(
            self.source,
            to_state=OfficialSource.AdmissionState.ENABLED,
            actor_label="test-owner",
            reason="enabled",
            evidence="offline adapter contract passed",
        )

    def test_default_preview_does_not_change_source(self) -> None:
        output = StringIO()

        call_command("configure_midea_availability_gate", stdout=output)

        self.source.refresh_from_db()
        self.assertNotIn("availability_probe", self.source.parser_config)
        self.assertTrue(source_is_admitted(self.source))
        self.assertEqual(SourceAdmissionEvent.objects.count(), 2)
        self.assertIn("would_append_events=3", output.getvalue())
        self.assertIn("network_requests=0", output.getvalue())

    def test_apply_from_suspended_configures_and_reenables_source(self) -> None:
        transition_source(
            self.source,
            to_state=OfficialSource.AdmissionState.SUSPENDED,
            actor_label="test-owner",
            reason="official page closed",
            evidence="owner screenshot",
        )

        output = StringIO()
        call_command(
            "configure_midea_availability_gate",
            "--apply",
            stdout=output,
        )

        self.source.refresh_from_db()
        self.assertEqual(
            self.source.parser_config["availability_probe"],
            AVAILABILITY_PROBE,
        )
        self.assertEqual(self.source.last_error, PROBE_PENDING_ERROR)
        self.assertEqual(
            self.source.admission_state,
            OfficialSource.AdmissionState.ENABLED,
        )
        self.assertTrue(source_is_admitted(self.source))
        self.assertEqual(SourceAdmissionEvent.objects.count(), 5)
        self.assertIn("admission_events_appended=2", output.getvalue())

        second_output = StringIO()
        call_command(
            "configure_midea_availability_gate",
            "--apply",
            stdout=second_output,
        )
        self.assertEqual(SourceAdmissionEvent.objects.count(), 5)
        self.assertIn("already_current=1", second_output.getvalue())

    def test_apply_does_not_modify_other_midea_source(self) -> None:
        other = OfficialSource.objects.create(
            organization=self.source.organization,
            source_type=OfficialSource.SourceType.API,
            source_url="https://careers.midea.com/schoolOut/post?type=1",
            admission_evidence="separate campus source",
            adapter_name="local_demo_disabled",
            parser_config={"marker": "campus"},
        )

        call_command("configure_midea_availability_gate", "--apply")

        other.refresh_from_db()
        self.assertEqual(other.parser_config, {"marker": "campus"})
        self.assertEqual(
            other.admission_state,
            OfficialSource.AdmissionState.CANDIDATE,
        )
