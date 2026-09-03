import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from radar.models import (
    ApplicationLink,
    OfficialSource,
    Organization,
    RecruitmentBatch,
    RecruitmentPosition,
    SourceAdmissionEvent,
)
from radar.services.admission import source_is_admitted, transition_source
from tools.build_t4_source_catalog import build_rows


class MideaClosedInternshipRetirementTests(TestCase):
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
        self.batch = RecruitmentBatch.objects.create(
            organization=organization,
            source=self.source,
            identity_key="phase-02:p17",
            title="美的集团日常实习生招聘",
            official_page_url=row["source_url"],
            recruitment_type=RecruitmentBatch.RecruitmentType.INTERNSHIP,
            target_audience="在校生",
            status=RecruitmentBatch.Status.ACTIVE,
            announcement_admission=(
                RecruitmentBatch.AnnouncementAdmission.ADMITTED
            ),
        )
        self.position = RecruitmentPosition.objects.create(
            batch=self.batch,
            position_key="intern-1",
            title="实习生",
            location_text="佛山",
        )
        self.link = ApplicationLink.objects.create(
            batch=self.batch,
            position=self.position,
            url="https://careers.midea.com/schoolOut/post/details?id=intern-1",
            link_type=ApplicationLink.LinkType.APPLICATION,
            verification_evidence="official position link",
        )

    def test_default_preview_does_not_change_state(self) -> None:
        output = StringIO()

        call_command("retire_midea_closed_internship", stdout=output)

        self.source.refresh_from_db()
        self.batch.refresh_from_db()
        self.position.refresh_from_db()
        self.assertTrue(source_is_admitted(self.source))
        self.assertEqual(self.batch.status, RecruitmentBatch.Status.ACTIVE)
        self.assertTrue(self.position.is_current)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 2)
        self.assertIn("would_retire_positions=1", output.getvalue())
        self.assertIn("network_requests=0", output.getvalue())

    def test_apply_retires_only_the_internship_batch_and_is_idempotent(self) -> None:
        campus_source = OfficialSource.objects.create(
            organization=self.source.organization,
            source_type=OfficialSource.SourceType.API,
            source_url="https://careers.midea.com/schoolOut/post?type=1",
            admission_evidence="separate campus source",
            adapter_name="local_demo_disabled",
            parser_config={},
        )
        campus_batch = RecruitmentBatch.objects.create(
            organization=self.source.organization,
            source=campus_source,
            identity_key="official-project:midea:2027-star",
            title="美的集团 2027 届美的星校园招聘",
            official_page_url=campus_source.source_url,
            recruitment_type=RecruitmentBatch.RecruitmentType.AUTUMN,
            target_audience="2027届",
        )

        call_command("retire_midea_closed_internship", "--apply")

        self.source.refresh_from_db()
        self.batch.refresh_from_db()
        self.position.refresh_from_db()
        self.link.refresh_from_db()
        campus_source.refresh_from_db()
        campus_batch.refresh_from_db()
        self.assertEqual(
            self.source.admission_state,
            OfficialSource.AdmissionState.SUSPENDED,
        )
        self.assertFalse(self.source.is_active)
        self.assertEqual(self.batch.status, RecruitmentBatch.Status.EXPIRED)
        self.assertFalse(self.position.is_current)
        self.assertIsNotNone(self.position.removed_at)
        self.assertFalse(self.link.is_current)
        self.assertIsNotNone(self.link.removed_at)
        self.assertEqual(
            campus_source.admission_state,
            OfficialSource.AdmissionState.CANDIDATE,
        )
        self.assertEqual(campus_batch.status, RecruitmentBatch.Status.ACTIVE)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 3)

        output = StringIO()
        call_command("retire_midea_closed_internship", "--apply", stdout=output)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 3)
        self.assertIn("already_retired=1", output.getvalue())
