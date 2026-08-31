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
    "radar.migrations.0027_classify_verified_2027_autumn_batches"
)


class RecruitmentSeasonClassificationTests(TestCase):
    def test_review_covers_only_batches_with_autumn_window_evidence(self):
        identities = {
            item["identity_key"] for item in migration.AUTUMN_CLASSIFICATIONS
        }

        self.assertEqual(len(identities), 11)
        self.assertNotIn("official-project:dji:tuojiangzhe:2027", identities)
        self.assertFalse(
            any(
                identity.startswith("official-project:tencent:")
                for identity in identities
            )
        )

    def test_forward_is_idempotent_and_reverse_restores_previous_types(self):
        batch_ids = []
        sources = {}
        for index, item in enumerate(migration.AUTUMN_CLASSIFICATIONS):
            source = sources.get(item["company"])
            if source is None:
                source = create_enabled_source(
                    name=item["company"],
                    host=item["domain"],
                )
                sources[item["company"]] = source
            announcement = RecruitmentAnnouncement.objects.create(
                organization=source.organization,
                source=source,
                identity_key=f"season-review-{index}",
                source_kind=RecruitmentAnnouncement.SourceKind.WEBSITE,
                title=f"{item['company']}招聘公告",
                url=source.source_url,
                identity_evidence="官方招聘页测试证据",
                verification_status=(
                    RecruitmentAnnouncement.VerificationStatus.VERIFIED
                ),
                verification_method=(
                    RecruitmentAnnouncement.VerificationMethod.MANUAL_REVIEW
                ),
            )
            batch = RecruitmentBatch.objects.create(
                organization=source.organization,
                source=source,
                identity_key=item["identity_key"],
                title=f"{item['company']}招聘批次",
                official_page_url=source.source_url,
                primary_announcement=announcement,
                announcement_admission=(
                    RecruitmentBatch.AnnouncementAdmission.ADMITTED
                ),
                recruitment_type=item["previous_type"],
            )
            batch_ids.append(batch.pk)

        migration.classify_verified_2027_batches_as_autumn(apps, None)
        self.assertEqual(
            RecruitmentBatch.objects.filter(
                pk__in=batch_ids,
                recruitment_type=RecruitmentBatch.RecruitmentType.AUTUMN,
            ).count(),
            11,
        )
        self.assertEqual(
            AnnouncementFieldEvidence.objects.filter(
                batch_id__in=batch_ids,
                field_name="recruitment_type",
                parsed_value=RecruitmentBatch.RecruitmentType.AUTUMN,
            ).count(),
            11,
        )

        migration.classify_verified_2027_batches_as_autumn(apps, None)
        self.assertEqual(
            AnnouncementFieldEvidence.objects.filter(
                batch_id__in=batch_ids,
                field_name="recruitment_type",
                parsed_value=RecruitmentBatch.RecruitmentType.AUTUMN,
            ).count(),
            11,
        )

        migration.restore_previous_recruitment_types(apps, None)
        for item, batch_id in zip(migration.AUTUMN_CLASSIFICATIONS, batch_ids):
            self.assertEqual(
                RecruitmentBatch.objects.get(pk=batch_id).recruitment_type,
                item["previous_type"],
            )
