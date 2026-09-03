import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from radar.models import (
    OfficialSource,
    Organization,
    RecruitmentBatch,
    SourceAdmissionEvent,
)
from radar.services.admission import (
    approve_application_host,
    source_is_admitted,
    transition_source,
)
from tools.build_t4_source_catalog import build_rows


class FawVw2027SourceUpgradeTests(TestCase):
    def setUp(self) -> None:
        row = next(
            item
            for item in build_rows()
            if item["organization_name"] == "一汽-大众汽车有限公司"
        )
        organization = Organization.objects.create(
            name=row["organization_name"],
            company_type=row["company_type"],
            industry=row["industry"],
            official_domain=row["official_domain"],
        )
        source = OfficialSource.objects.create(
            organization=organization,
            source_type=row["source_type"],
            source_url=row["source_url"],
            official_entrypoint_url=row["official_entrypoint_url"],
            admission_evidence=row["admission_evidence"],
            adapter_name=row["adapter_name"],
            parser_config=json.loads(row["parser_config"]),
            last_etag="stale-etag",
        )
        transition_source(
            source,
            to_state=OfficialSource.AdmissionState.VERIFIED,
            actor_label="test-owner",
            reason="verified",
            evidence="official careers entrypoint linked to the ATS",
        )
        approve_application_host(
            source,
            host="faw-vw.hotjob.cn",
            actor_label="test-owner",
            evidence="official careers entrypoint linked to the ATS",
        )
        transition_source(
            source,
            to_state=OfficialSource.AdmissionState.ENABLED,
            actor_label="test-owner",
            reason="enabled",
            evidence="offline adapter contract passed",
        )
        RecruitmentBatch.objects.create(
            organization=organization,
            source=source,
            identity_key="phase-02:j02",
            title="一汽-大众汽车有限公司校园招聘",
            official_page_url=row["source_url"],
            target_audience="2026届",
            announcement_admission=RecruitmentBatch.AnnouncementAdmission.EXCLUDED,
        )

    def test_default_preview_does_not_change_config_or_events(self) -> None:
        output = StringIO()

        call_command("upgrade_faw_vw_2027_source", stdout=output)

        source = OfficialSource.objects.get(
            organization__name="一汽-大众汽车有限公司"
        )
        self.assertEqual(source.parser_config["batch"]["target_audience"], "2026届")
        self.assertEqual(SourceAdmissionEvent.objects.count(), 2)
        self.assertIn("network_requests=0", output.getvalue())

    def test_apply_is_audited_idempotent_and_preserves_old_batch(self) -> None:
        call_command("upgrade_faw_vw_2027_source", "--apply")

        source = OfficialSource.objects.get(
            organization__name="一汽-大众汽车有限公司"
        )
        self.assertEqual(
            source.parser_config["batch"]["identity_key"],
            "phase-02:j02:2027-campus",
        )
        self.assertEqual(source.parser_config["batch"]["target_audience"], "2027届")
        self.assertEqual(
            source.parser_config["row_filters"],
            [{"path": "projectName", "equals_any": ["2027校园招聘"]}],
        )
        self.assertEqual(source.last_etag, "")
        self.assertEqual(SourceAdmissionEvent.objects.count(), 5)
        self.assertTrue(source_is_admitted(source))
        self.assertTrue(
            RecruitmentBatch.objects.filter(
                source=source,
                identity_key="phase-02:j02",
                target_audience="2026届",
            ).exists()
        )

        output = StringIO()
        call_command("upgrade_faw_vw_2027_source", "--apply", stdout=output)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 5)
        self.assertIn("already_current=1", output.getvalue())

    def test_unexpected_campaign_config_is_rejected(self) -> None:
        source = OfficialSource.objects.get(
            organization__name="一汽-大众汽车有限公司"
        )
        source.parser_config["row_filters"] = []
        source.save(update_fields=["parser_config"])

        with self.assertRaisesMessage(
            CommandError,
            "unexpected FAW-VW campaign config",
        ):
            call_command("upgrade_faw_vw_2027_source")
