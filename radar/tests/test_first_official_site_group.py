import importlib

from django.apps import apps
from django.test import TestCase

from radar.collectors.registry import AdapterRegistry
from radar.models import (
    AnnouncementFieldEvidence,
    OfficialSource,
    RecruitmentBatch,
)
from radar.services.admission import source_is_admitted
from radar.services.application_pages import configured_batch_application_url
from radar.tests.helpers import create_enabled_source


migration = importlib.import_module(
    "radar.migrations.0031_admit_first_official_site_group"
)


class FirstOfficialSiteGroupMigrationTests(TestCase):
    def setUp(self):
        self.sources = {}
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
                title=f"{name}旧混合批次",
                official_page_url=source.source_url,
                recruitment_type="campus_recruitment",
                target_audience="应届毕业生/实习生",
                announcement_admission="excluded",
            )
            self.sources[name] = source

    def test_forward_creates_exact_admitted_batches_and_project_sources(self):
        migration.admit_first_official_site_group(apps, None)

        expected = {
            "理想汽车": {
                "official-project:lixiang:25",
                "official-project:lixiang:24",
                "official-project:lixiang:23",
            },
            "吉利控股": {
                "official-project:geely:2027-autumn",
                "official-project:geely:2027-internship",
            },
            "美的集团": {
                "official-project:midea:2027-star",
                "official-project:midea:2027-doctor",
                "phase-02:p17",
            },
            "博世中国": {"phase-02:f05"},
        }
        for company, identities in expected.items():
            with self.subTest(company=company):
                batches = RecruitmentBatch.objects.filter(
                    organization__name=company,
                    identity_key__in=identities,
                ).select_related("primary_announcement")
                self.assertEqual(
                    set(batches.values_list("identity_key", flat=True)),
                    identities,
                )
                self.assertTrue(
                    all(
                        batch.announcement_admission == "admitted"
                        and batch.primary_announcement.verification_status
                        == "verified"
                        for batch in batches
                    )
                )
                self.assertEqual(
                    AnnouncementFieldEvidence.objects.filter(
                        batch__in=batches
                    ).count(),
                    len(identities) * 4,
                )

        self.assertEqual(
            OfficialSource.objects.filter(
                organization__name="理想汽车", adapter_name="json_api"
            ).count(),
            3,
        )
        self.assertEqual(
            OfficialSource.objects.filter(
                organization__name="美的集团", adapter_name="json_api"
            ).count(),
            3,
        )

    def test_forward_is_idempotent_and_configs_validate(self):
        migration.admit_first_official_site_group(apps, None)
        migration.admit_first_official_site_group(apps, None)

        batches = RecruitmentBatch.objects.filter(
            announcement_admission="admitted",
            organization__name__in=self.sources,
        )
        self.assertEqual(batches.count(), 9)
        self.assertEqual(
            AnnouncementFieldEvidence.objects.filter(batch__in=batches).count(),
            36,
        )
        sources = OfficialSource.objects.filter(
            organization__name__in=self.sources,
            admission_state="enabled",
        ).select_related("organization")
        self.assertEqual(sources.count(), 8)
        for source in sources:
            with self.subTest(source=source.pk):
                self.assertIsNone(AdapterRegistry.validate_source_config(source))

    def test_application_pages_are_scoped_to_each_batch(self):
        migration.admit_first_official_site_group(apps, None)

        batches = RecruitmentBatch.objects.filter(
            announcement_admission="admitted",
            organization__name__in=self.sources,
        ).select_related("source", "source__organization")
        for batch in batches:
            with self.subTest(batch=batch.identity_key):
                url = configured_batch_application_url(
                    batch.source, batch.identity_key
                )
                self.assertIsNotNone(url)
                self.assertIn("https://", url)

    def test_reverse_hides_the_newly_admitted_batches(self):
        migration.admit_first_official_site_group(apps, None)
        migration.exclude_first_official_site_group(apps, None)

        self.assertFalse(
            RecruitmentBatch.objects.filter(
                organization__name__in=self.sources,
                announcement_admission="admitted",
            ).exists()
        )


class GeelyProjectPartitionAdmissionTests(TestCase):
    def test_live_model_accepts_a_reverified_geely_partition_source(self):
        source = create_enabled_source(name="吉利控股", host="geely.com")
        source.adapter_name = "moka_public_api"
        source.source_type = "website"
        source.source_url = (
            "https://campus.geely.com/campus-recruitment/geely/78436"
            "?locale=zh-CN#/jobs"
        )
        source.official_entrypoint_url = "https://campus.geely.com/"
        source.parser_config = migration._geely_config()
        source.save()

        self.assertIsNone(AdapterRegistry.validate_source_config(source))
        self.assertTrue(source_is_admitted(source))
