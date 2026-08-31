import importlib

from django.apps import apps
from django.test import TestCase

from radar.models import (
    AnnouncementFieldEvidence,
    RecruitmentAnnouncement,
    RecruitmentBatch,
)
from radar.tests.helpers import create_enabled_source


migration = importlib.import_module(
    "radar.migrations.0028_classify_tencent_2027_main_campaign_as_autumn"
)


class TencentSeasonClassificationTests(TestCase):
    def setUp(self):
        self.source = create_enabled_source(name="腾讯", host="qq.com")
        self.main_batch = self._create_batch(
            "official-project:tencent:project:1",
            "腾讯应届毕业生招聘",
            RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT,
        )
        self.qingyun_batch = self._create_batch(
            "official-project:tencent:project:14",
            "腾讯青云计划（应届生）",
            RecruitmentBatch.RecruitmentType.SPECIAL_PROGRAM,
        )
        self.ai_pm_batch = self._create_batch(
            "official-project:tencent:project:9",
            "腾讯 AI 产品经理培训生",
            RecruitmentBatch.RecruitmentType.SPECIAL_PROGRAM,
        )

    def _create_batch(self, identity_key, title, recruitment_type):
        announcement = RecruitmentAnnouncement.objects.create(
            organization=self.source.organization,
            source=self.source,
            identity_key=f"announcement:{identity_key}",
            source_kind=RecruitmentAnnouncement.SourceKind.WEBSITE,
            title=(
                "腾讯2027校园招聘启动公告&FAQ"
                if identity_key == migration.IDENTITY_KEY
                else title
            ),
            url=self.source.source_url,
            identity_evidence="腾讯官网校招公告列表",
            verification_status=(
                RecruitmentAnnouncement.VerificationStatus.VERIFIED
            ),
            verification_method=(
                RecruitmentAnnouncement.VerificationMethod.MANUAL_REVIEW
            ),
        )
        return RecruitmentBatch.objects.create(
            organization=self.source.organization,
            source=self.source,
            identity_key=identity_key,
            title=title,
            official_page_url=self.source.source_url,
            primary_announcement=announcement,
            announcement_admission=(
                RecruitmentBatch.AnnouncementAdmission.ADMITTED
            ),
            recruitment_type=recruitment_type,
        )

    def test_only_main_campaign_inherits_main_launch_announcement(self):
        migration.classify_tencent_main_campaign_as_autumn(apps, None)

        self.main_batch.refresh_from_db()
        self.qingyun_batch.refresh_from_db()
        self.ai_pm_batch.refresh_from_db()
        self.assertEqual(
            self.main_batch.recruitment_type,
            RecruitmentBatch.RecruitmentType.AUTUMN,
        )
        self.assertEqual(
            self.qingyun_batch.recruitment_type,
            RecruitmentBatch.RecruitmentType.SPECIAL_PROGRAM,
        )
        self.assertEqual(
            self.ai_pm_batch.recruitment_type,
            RecruitmentBatch.RecruitmentType.SPECIAL_PROGRAM,
        )

    def test_forward_is_idempotent_and_reverse_restores_main_type(self):
        migration.classify_tencent_main_campaign_as_autumn(apps, None)
        migration.classify_tencent_main_campaign_as_autumn(apps, None)

        evidence = AnnouncementFieldEvidence.objects.filter(
            batch=self.main_batch,
            field_name="recruitment_type",
            locator=migration.AUTUMN_LOCATOR,
            parsed_value=RecruitmentBatch.RecruitmentType.AUTUMN,
        )
        self.assertEqual(evidence.count(), 1)

        migration.restore_tencent_main_campaign_type(apps, None)
        self.main_batch.refresh_from_db()
        self.assertEqual(
            self.main_batch.recruitment_type,
            RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT,
        )
