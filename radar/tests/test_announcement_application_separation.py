import importlib

from django.apps import apps
from django.test import TestCase

from radar.models import RecruitmentBatch
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
        self.tencent_source.save(update_fields=["adapter_name"])

        first_group_migration.admit_first_official_site_group(apps, None)
        tencent_migration.add_tencent_internship_batches(apps, None)
        separation_migration.separate_announcement_urls(apps, None)

    def test_distinct_official_announcements_do_not_replace_application_pages(self):
        expected = {
            "理想汽车": (
                {
                    "official-project:lixiang:25",
                    "official-project:lixiang:24",
                    "official-project:lixiang:23",
                },
                "https://www.lixiang.com/employ/campus/preach.html?type=1&fromJob=1",
            ),
            "美的集团": (
                {
                    "official-project:midea:2027-star",
                    "official-project:midea:2027-doctor",
                    "phase-02:p17",
                },
                "https://careers.midea.com/schoolOut/home",
            ),
            "腾讯": (
                {
                    "official-project:tencent:project:2",
                    "official-project:tencent:projects:4-12",
                    "official-project:tencent:project:20",
                },
                "https://join.qq.com/",
            ),
        }
        for company, (identities, announcement_url) in expected.items():
            batches = RecruitmentBatch.objects.filter(
                organization__name=company,
                identity_key__in=identities,
            ).select_related(
                "primary_announcement",
                "source",
                "source__organization",
            )
            self.assertEqual(
                set(batches.values_list("identity_key", flat=True)),
                identities,
            )
            for batch in batches:
                with self.subTest(company=company, batch=batch.identity_key):
                    application_url = configured_batch_application_url(
                        batch.source,
                        batch.identity_key,
                    )
                    self.assertEqual(
                        batch.primary_announcement.url,
                        announcement_url,
                    )
                    self.assertNotEqual(application_url, announcement_url)
                    self.assertEqual(
                        batch.primary_announcement.verification_method,
                        "browser",
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
