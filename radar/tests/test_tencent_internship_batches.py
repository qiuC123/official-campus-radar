import importlib

from django.apps import apps
from django.test import TestCase

from radar.models import AnnouncementFieldEvidence, RecruitmentBatch
from radar.tests.helpers import create_enabled_source


migration = importlib.import_module(
    "radar.migrations.0030_add_tencent_internship_batches"
)


class TencentInternshipBatchTests(TestCase):
    def setUp(self):
        self.source = create_enabled_source(name="腾讯", host="qq.com")
        self.source.adapter_name = "json_api"
        self.source.save(update_fields=["adapter_name"])

    def test_forward_creates_three_distinct_admitted_internship_batches(self):
        migration.add_tencent_internship_batches(apps, None)

        batches = RecruitmentBatch.objects.filter(source=self.source).order_by(
            "identity_key"
        )
        self.assertEqual(batches.count(), 3)
        self.assertEqual(
            set(batches.values_list("identity_key", flat=True)),
            {
                "official-project:tencent:project:2",
                "official-project:tencent:projects:4-12",
                "official-project:tencent:project:20",
            },
        )
        self.assertTrue(
            all(
                batch.recruitment_type
                == RecruitmentBatch.RecruitmentType.INTERNSHIP
                and batch.announcement_admission
                == RecruitmentBatch.AnnouncementAdmission.ADMITTED
                and batch.primary_announcement.verification_status == "verified"
                for batch in batches.select_related("primary_announcement")
            )
        )
        self.assertEqual(
            AnnouncementFieldEvidence.objects.filter(
                batch__in=batches,
            ).count(),
            12,
        )

    def test_forward_is_idempotent_and_reverse_preserves_history(self):
        migration.add_tencent_internship_batches(apps, None)
        migration.add_tencent_internship_batches(apps, None)
        self.assertEqual(RecruitmentBatch.objects.filter(source=self.source).count(), 3)
        self.assertEqual(AnnouncementFieldEvidence.objects.count(), 12)

        migration.exclude_tencent_internship_batches(apps, None)
        self.assertEqual(
            RecruitmentBatch.objects.filter(
                source=self.source,
                announcement_admission=(
                    RecruitmentBatch.AnnouncementAdmission.EXCLUDED
                ),
            ).count(),
            3,
        )
        self.assertEqual(AnnouncementFieldEvidence.objects.count(), 12)
