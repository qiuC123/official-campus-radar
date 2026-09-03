import copy
import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from radar.collectors.registry import AdapterRegistry
from radar.management.commands.upgrade_vivo_project_coverage import PENDING_ERROR
from radar.models import (
    AnnouncementFieldEvidence,
    ApplicationProgress,
    OfficialSource,
    Organization,
    RecruitmentAnnouncement,
    RecruitmentBatch,
    SourceAdmissionEvent,
)
from radar.services.admission import source_is_admitted, transition_source
from radar.services.project_partitions import (
    VIVO_PORTAL,
    VIVO_PROJECT_URLS,
    partitioned_parser_config,
)
from tools.build_t4_source_catalog import build_rows


class VivoProjectCoverageUpgradeTests(TestCase):
    def setUp(self) -> None:
        row = next(
            item
            for item in build_rows()
            if item["organization_name"] == "vivo"
        )
        configured = partitioned_parser_config(
            "vivo",
            row["adapter_name"],
            json.loads(row["parser_config"]),
        )
        legacy = copy.deepcopy(configured)
        legacy.pop("batch_partitions")
        legacy.pop("partition_coverage")
        legacy["body"]["ClassificationOne"] = ["2"]
        legacy["body"]["DisplayFields"] = [
            value
            for value in legacy["body"]["DisplayFields"]
            if value != "ClassificationOne"
        ]
        organization = Organization.objects.create(
            name="vivo",
            company_type="private",
            industry="消费电子/科技",
            official_domain="vivo.com",
        )
        self.source = OfficialSource.objects.create(
            organization=organization,
            source_type=OfficialSource.SourceType.API,
            source_url=VIVO_PROJECT_URLS["phase-02:p13"],
            official_entrypoint_url=VIVO_PROJECT_URLS["phase-02:p13"],
            admission_evidence="legacy vivo autumn-only source",
            adapter_name="json_api",
            parser_config=legacy,
            last_etag="stale-etag",
        )
        transition_source(
            self.source,
            to_state=OfficialSource.AdmissionState.VERIFIED,
            actor_label="test-owner",
            reason="verified",
            evidence="official vivo source",
        )
        transition_source(
            self.source,
            to_state=OfficialSource.AdmissionState.ENABLED,
            actor_label="test-owner",
            reason="enabled",
            evidence="offline contract passed",
        )
        announcement = RecruitmentAnnouncement.objects.create(
            organization=organization,
            source=self.source,
            identity_key="legacy-vivo-autumn",
            source_kind=RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM,
            title="vivo 招聘",
            url=self.source.source_url,
            identity_evidence="official portal",
            verification_status=(
                RecruitmentAnnouncement.VerificationStatus.CANDIDATE
            ),
        )
        self.batch = RecruitmentBatch.objects.create(
            organization=organization,
            source=self.source,
            identity_key="phase-02:p13",
            title="vivo 2027 届秋季校园招聘",
            official_page_url=self.source.source_url,
            primary_announcement=announcement,
            announcement_admission=RecruitmentBatch.AnnouncementAdmission.PENDING,
            recruitment_type=RecruitmentBatch.RecruitmentType.AUTUMN,
            target_audience="2027届",
        )
        self.progress = ApplicationProgress.objects.create(
            batch=self.batch,
            status=ApplicationProgress.Status.APPLIED,
        )
        other = Organization.objects.create(
            name="对照企业",
            company_type="private",
            industry="测试",
            official_domain="example.com",
        )
        self.other_source = OfficialSource.objects.create(
            organization=other,
            source_type=OfficialSource.SourceType.WEBSITE,
            source_url="https://example.com/jobs",
            admission_evidence="control",
        )

    def test_default_preview_changes_nothing(self) -> None:
        output = StringIO()

        call_command("upgrade_vivo_project_coverage", stdout=output)

        self.source.refresh_from_db()
        self.assertNotEqual(self.source.source_url, VIVO_PORTAL)
        self.assertEqual(
            self.source.parser_config["body"]["ClassificationOne"],
            ["2"],
        )
        self.assertEqual(
            RecruitmentBatch.objects.filter(source=self.source).count(),
            1,
        )
        self.assertEqual(
            SourceAdmissionEvent.objects.filter(source=self.source).count(),
            2,
        )
        self.assertIn("network_requests=0", output.getvalue())

    def test_apply_preserves_autumn_progress_and_admits_all_projects(self) -> None:
        original_batch_pk = self.batch.pk

        call_command("upgrade_vivo_project_coverage", "--apply")

        self.source.refresh_from_db()
        self.batch.refresh_from_db()
        self.progress.refresh_from_db()
        self.other_source.refresh_from_db()
        self.assertEqual(self.source.source_url, VIVO_PORTAL)
        self.assertEqual(self.source.official_entrypoint_url, VIVO_PORTAL)
        self.assertEqual(
            self.source.parser_config["body"]["ClassificationOne"],
            [],
        )
        self.assertEqual(
            self.source.parser_config["partition_coverage"],
            {
                "request_path": "ClassificationOne",
                "row_path": "ClassificationOne",
            },
        )
        self.assertEqual(len(self.source.parser_config["batch_partitions"]), 4)
        self.assertEqual(self.source.last_etag, "")
        self.assertEqual(self.source.last_error, PENDING_ERROR)
        self.assertTrue(source_is_admitted(self.source))
        self.assertIsNone(AdapterRegistry.validate_source_config(self.source))
        self.assertEqual(self.batch.pk, original_batch_pk)
        self.assertEqual(self.progress.batch_id, original_batch_pk)
        self.assertEqual(self.progress.status, ApplicationProgress.Status.APPLIED)
        self.assertEqual(self.other_source.source_url, "https://example.com/jobs")
        batches = RecruitmentBatch.objects.filter(source=self.source)
        self.assertEqual(
            set(batches.values_list("identity_key", flat=True)),
            {
                "official-project:vivo:blue-star",
                "phase-02:p13",
                "official-project:vivo:daily-internship",
                "official-project:vivo:summer-internship",
            },
        )
        self.assertTrue(
            all(
                batch.announcement_admission
                == RecruitmentBatch.AnnouncementAdmission.ADMITTED
                and batch.primary_announcement.verification_status
                == RecruitmentAnnouncement.VerificationStatus.VERIFIED
                for batch in batches.select_related("primary_announcement")
            )
        )
        self.assertEqual(
            AnnouncementFieldEvidence.objects.filter(batch__in=batches).count(),
            16,
        )
        self.assertEqual(
            SourceAdmissionEvent.objects.filter(source=self.source).count(),
            5,
        )

    def test_apply_is_idempotent(self) -> None:
        call_command("upgrade_vivo_project_coverage", "--apply")
        event_count = SourceAdmissionEvent.objects.filter(source=self.source).count()
        output = StringIO()

        call_command("upgrade_vivo_project_coverage", "--apply", stdout=output)

        self.assertEqual(
            SourceAdmissionEvent.objects.filter(source=self.source).count(),
            event_count,
        )
        self.assertEqual(
            RecruitmentBatch.objects.filter(source=self.source).count(),
            4,
        )
        self.assertEqual(
            AnnouncementFieldEvidence.objects.filter(
                batch__source=self.source
            ).count(),
            16,
        )
        self.assertIn("already_current=1", output.getvalue())
