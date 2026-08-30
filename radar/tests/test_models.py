from django.db import IntegrityError
from django.test import TestCase

from radar.models import ApplicationProgress, OfficialSource, Organization, RecruitmentBatch, RecruitmentPosition, UpdateRun


class RecruitmentModelTests(TestCase):
    def setUp(self) -> None:
        self.organization = Organization.objects.create(
            name="示例互联网公司", company_type="internet", industry="互联网", official_domain="careers.example.com"
        )
        self.source = OfficialSource.objects.create(organization=self.organization, source_type="website", source_url="https://careers.example.com", admission_evidence="reviewed")

    def test_one_portal_url_can_support_two_batches_with_distinct_identities(self) -> None:
        RecruitmentBatch.objects.create(
            organization=self.organization,
            source=self.source,
            identity_key="batch-2027",
            title="2027 校园招聘",
            official_page_url="https://careers.example.com/2027",
        )
        RecruitmentBatch.objects.create(
            organization=self.organization,
            source=self.source,
            identity_key="special-program-2027",
            title="同一门户中的专项计划",
            official_page_url="https://careers.example.com/2027",
        )
        self.assertEqual(RecruitmentBatch.objects.count(), 2)

    def test_same_source_and_identity_still_cannot_create_two_batches(self) -> None:
        RecruitmentBatch.objects.create(
            organization=self.organization,
            source=self.source,
            identity_key="batch-2027",
            title="2027 校园招聘",
            official_page_url="https://careers.example.com/2027",
        )
        with self.assertRaises(IntegrityError):
            RecruitmentBatch.objects.create(
                organization=self.organization,
                source=self.source,
                identity_key="batch-2027",
                title="重复身份",
                official_page_url="https://careers.example.com/another",
            )

    def test_new_notice_progress_defaults_to_not_applied(self) -> None:
        batch = RecruitmentBatch.objects.create(
            organization=self.organization,
            source=self.source,
            identity_key="batch-another",
            title="2027 校园招聘",
            official_page_url="https://careers.example.com/another",
        )
        progress = ApplicationProgress.objects.create(batch=batch)
        self.assertEqual(progress.status, ApplicationProgress.Status.NOT_APPLIED)

    def test_partial_failure_is_a_successful_update_run(self) -> None:
        self.assertTrue(UpdateRun(trigger="scheduled", status="partial_failure").is_successful)
