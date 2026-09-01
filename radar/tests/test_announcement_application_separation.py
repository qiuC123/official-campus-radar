import importlib

from django.apps import apps
from django.test import TestCase

from radar.models import RecruitmentAnnouncement, RecruitmentBatch
from radar.services.application_pages import configured_batch_application_url
from radar.tests.helpers import create_enabled_source


first_group_migration = importlib.import_module(
    "radar.migrations.0031_admit_first_official_site_group"
)
tencent_migration = importlib.import_module(
    "radar.migrations.0030_add_tencent_internship_batches"
)
separation_migration = importlib.import_module(
    "radar.migrations.0032_separate_announcement_and_application_urls"
)
specific_migration = importlib.import_module(
    "radar.migrations.0033_use_specific_recruitment_announcements"
)


class AnnouncementApplicationSeparationTests(TestCase):
    def setUp(self):
        fixtures = (
            ("理想汽车", "lixiang.com", "json_api", "phase-02:p20"),
            ("吉利控股", "geely.com", "moka_public_api", "phase-02:p16"),
            ("美的集团", "midea.com", "json_api", "phase-02:p17"),
            ("博世中国", "bosch.com.cn", "ats_json_api", "phase-02:f05"),
        )
        for name, domain, adapter, old_identity in fixtures:
            source = create_enabled_source(name=name, host=domain)
            source.adapter_name = adapter
            source.save(update_fields=["adapter_name"])
            RecruitmentBatch.objects.create(
                organization=source.organization,
                source=source,
                identity_key=old_identity,
                title=f"{name}旧批次",
                official_page_url=source.source_url,
                recruitment_type="campus_recruitment",
                target_audience="应届毕业生/实习生",
                announcement_admission="excluded",
            )
        self.tencent_source = create_enabled_source(name="腾讯", host="qq.com")
        self.tencent_source.adapter_name = "json_api"
        self.tencent_source.source_url = "https://join.qq.com/"
        self.tencent_source.save(update_fields=["adapter_name", "source_url"])

        for identity_key, title in (
            (
                "official-project:tencent:project:1",
                "腾讯应届毕业生招聘",
            ),
            (
                "official-project:tencent:project:14",
                "腾讯青云计划（应届生）",
            ),
            (
                "official-project:tencent:project:9",
                "腾讯 AI 产品经理培训生",
            ),
        ):
            announcement = RecruitmentAnnouncement.objects.create(
                organization=self.tencent_source.organization,
                source=self.tencent_source,
                source_kind="recruiting_system",
                identity_key=f"{identity_key}:announcement",
                title=title,
                url="https://join.qq.com/",
                identity_evidence="腾讯校招首页测试证据",
            )
            RecruitmentBatch.objects.create(
                organization=self.tencent_source.organization,
                source=self.tencent_source,
                identity_key=identity_key,
                title=title,
                official_page_url="https://join.qq.com/",
                primary_announcement=announcement,
                announcement_admission="admitted",
                recruitment_type="autumn",
                target_audience="2027届",
            )

        first_group_migration.admit_first_official_site_group(apps, None)
        tencent_migration.add_tencent_internship_batches(apps, None)
        separation_migration.separate_announcement_urls(apps, None)
        specific_migration.use_specific_recruitment_announcements(apps, None)

    def test_specific_notices_are_used_only_for_the_batches_they_cover(self):
        expected = {
            "official-project:tencent:project:1": (
                "https://join.qq.com/detail.html?id=288"
            ),
            "official-project:midea:2027-star": (
                "https://careers.midea.com/schoolOut/noticeDetail"
                "?noticeId=8b8b3421a048420201a048aa9e0501dc"
            ),
            "official-project:midea:2027-doctor": (
                "https://careers.midea.com/schoolOut/noticeDetail"
                "?noticeId=8b8b3421a048420201a048aa9e0501dc"
            ),
        }
        for identity_key, announcement_url in expected.items():
            batch = RecruitmentBatch.objects.select_related(
                "primary_announcement",
                "source",
                "source__organization",
            ).get(identity_key=identity_key)
            application_url = configured_batch_application_url(
                batch.source,
                batch.identity_key,
            )
            self.assertEqual(batch.primary_announcement.url, announcement_url)
            self.assertNotEqual(batch.primary_announcement.url, application_url)

    def test_projects_without_matching_notices_use_their_application_pages(self):
        identities = {
            "official-project:tencent:project:2",
            "official-project:tencent:projects:4-12",
            "official-project:tencent:project:14",
            "official-project:tencent:project:20",
            "official-project:tencent:project:9",
            "phase-02:p17",
        }
        batches = RecruitmentBatch.objects.filter(
            identity_key__in=identities,
        ).select_related("primary_announcement", "source")
        self.assertEqual(
            set(batches.values_list("identity_key", flat=True)),
            identities,
        )
        for batch in batches:
            with self.subTest(batch=batch.identity_key):
                self.assertEqual(
                    batch.primary_announcement.url,
                    configured_batch_application_url(
                        batch.source,
                        batch.identity_key,
                    ),
                )

    def test_lixiang_keeps_the_user_confirmed_recruitment_updates_page(self):
        batches = RecruitmentBatch.objects.filter(
            organization__name="理想汽车",
            identity_key__in={
                "official-project:lixiang:25",
                "official-project:lixiang:24",
                "official-project:lixiang:23",
            },
        ).select_related("primary_announcement", "source")
        self.assertEqual(batches.count(), 3)
        for batch in batches:
            self.assertEqual(
                batch.primary_announcement.url,
                "https://www.lixiang.com/employ/campus/"
                "preach.html?type=1&fromJob=1",
            )
            self.assertNotEqual(
                batch.primary_announcement.url,
                configured_batch_application_url(batch.source, batch.identity_key),
            )

    def test_bosch_keeps_the_job_page_fallback_without_a_current_notice(self):
        batch = RecruitmentBatch.objects.get(
            organization__name="博世中国",
            identity_key="phase-02:f05",
        )

        self.assertEqual(
            batch.primary_announcement.url,
            configured_batch_application_url(batch.source, batch.identity_key),
        )

    def test_reverse_restores_the_previous_fallback_urls(self):
        separation_migration.restore_previous_announcement_urls(apps, None)

        for _, identity, _ in separation_migration.ANNOUNCEMENT_MAPPINGS:
            batch = RecruitmentBatch.objects.get(identity_key=identity)
            self.assertEqual(
                batch.primary_announcement.url,
                separation_migration.PREVIOUS_URLS[identity],
            )

    def test_specific_notice_reverse_restores_general_recruitment_pages(self):
        specific_migration.restore_general_recruitment_pages(apps, None)

        for identity_key, expected_url in specific_migration.PREVIOUS_URLS.items():
            batch = RecruitmentBatch.objects.get(identity_key=identity_key)
            self.assertEqual(batch.primary_announcement.url, expected_url)
