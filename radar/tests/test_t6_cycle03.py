import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from radar.models import OfficialSource, Organization, SourceAdmissionEvent
from radar.services.admission import source_is_admitted, transition_source
from tools.build_t4_source_catalog import build_rows
from tools.t6_cycle03_unicom_config import COMPANY, MINIMAL_HEADERS, SUCCESS_GUARD


class T6Cycle03UnicomConfigTests(TestCase):
    def setUp(self) -> None:
        row = next(
            row for row in build_rows() if row["organization_name"] == COMPANY
        )
        self.original_config = json.loads(row["parser_config"])
        organization = Organization.objects.create(
            name=COMPANY,
            company_type="state_owned",
            industry="通信",
            official_domain="zhaopin.com",
        )
        source = OfficialSource.objects.create(
            organization=organization,
            source_type="api",
            source_url=row["source_url"],
            admission_evidence="T4 fixture",
            adapter_name="json_api",
            parser_config=self.original_config,
        )
        transition_source(
            source,
            to_state="verified",
            actor_label="test-owner",
            reason="verified",
            evidence="saved T4 evidence",
        )
        transition_source(
            source,
            to_state="enabled",
            actor_label="test-owner",
            reason="enabled",
            evidence="offline contract passed",
        )

    def test_dry_run_does_not_change_config_or_admission_chain(self) -> None:
        output = StringIO()

        call_command("apply_t6_cycle03_unicom_config", "--dry-run", stdout=output)

        source = OfficialSource.objects.get(organization__name=COMPANY)
        self.assertIn("network_requests=0", output.getvalue())
        self.assertEqual(source.parser_config, self.original_config)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 2)

    def test_apply_keeps_guard_and_records_three_audit_events(self) -> None:
        call_command("apply_t6_cycle03_unicom_config")

        source = OfficialSource.objects.get(organization__name=COMPANY)
        self.assertEqual(source.parser_config["headers"], MINIMAL_HEADERS)
        self.assertEqual(source.parser_config["success"], SUCCESS_GUARD)
        self.assertEqual(source.parser_config["pagination"]["page_size"], 100)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 5)
        self.assertTrue(source_is_admitted(source))

    def test_apply_refuses_an_unexpected_baseline(self) -> None:
        source = OfficialSource.objects.get(organization__name=COMPANY)
        source.parser_config["headers"] = {"Accept": "text/html"}
        source.save(update_fields=["parser_config"])

        with self.assertRaisesMessage(CommandError, "基线请求头"):
            call_command("apply_t6_cycle03_unicom_config")
