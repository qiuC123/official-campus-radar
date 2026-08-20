from django.db import IntegrityError
from django.test import TestCase

from radar.models import ApplicationProgress, OfficialSource, Organization, RecruitmentNotice, UpdateRun


class RecruitmentModelTests(TestCase):
    def setUp(self) -> None:
        self.organization = Organization.objects.create(
            name="示例互联网公司", company_type="internet", industry="互联网", official_domain="careers.example.com"
        )
        self.source = OfficialSource.objects.create(organization=self.organization, source_type="website", source_url="https://careers.example.com", admission_evidence="reviewed")

    def test_same_organization_and_official_url_cannot_create_two_notices(self) -> None:
        RecruitmentNotice.objects.create(
            organization=self.organization,
            source=self.source,
            identity_key="notice-2027",
            title="2027 校园招聘",
            official_notice_url="https://careers.example.com/2027",
        )
        with self.assertRaises(IntegrityError):
            RecruitmentNotice.objects.create(
                organization=self.organization,
                source=self.source,
                identity_key="notice-2027",
                title="重复标题不影响 URL 去重",
                official_notice_url="https://careers.example.com/2027",
            )

    def test_new_notice_progress_defaults_to_not_applied(self) -> None:
        notice = RecruitmentNotice.objects.create(
            organization=self.organization,
            source=self.source,
            identity_key="notice-another",
            title="2027 校园招聘",
            official_notice_url="https://careers.example.com/another",
        )
        progress = ApplicationProgress.objects.create(notice=notice)
        self.assertEqual(progress.status, ApplicationProgress.Status.NOT_APPLIED)

    def test_partial_failure_is_a_successful_update_run(self) -> None:
        self.assertTrue(UpdateRun(trigger="scheduled", status="partial_failure").is_successful)
