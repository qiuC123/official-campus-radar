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
    "radar.migrations.0029_classify_shared_campaign_projects_and_dji_early_autumn"
)


class SharedCampaignSeasonClassificationTests(TestCase):
    def setUp(self):
        self.batch_ids = []
        sources = {}
        for index, item in enumerate(migration.SEASON_CLASSIFICATIONS):
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
                identity_key=f"season-announcement-{index}",
                source_kind=RecruitmentAnnouncement.SourceKind.WEBSITE,
                title=f"{item['company']}招聘公告",
                url=source.source_url,
                identity_evidence="官网招聘活动测试证据",
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
            self.batch_ids.append(batch.pk)

    def test_shared_campaign_projects_inherit_season_and_june_is_early(self):
        migration.classify_campaign_seasons(apps, None)

        values = dict(
            RecruitmentBatch.objects.filter(pk__in=self.batch_ids).values_list(
                "identity_key", "recruitment_type"
            )
        )
        self.assertEqual(
            values["official-project:tencent:project:14"],
            RecruitmentBatch.RecruitmentType.AUTUMN,
        )
        self.assertEqual(
            values["official-project:tencent:project:9"],
            RecruitmentBatch.RecruitmentType.AUTUMN,
        )
        self.assertEqual(
            values["official-project:dji:tuojiangzhe:2027"],
            RecruitmentBatch.RecruitmentType.AUTUMN_EARLY,
        )

    def test_forward_is_idempotent_and_reverse_restores_previous_types(self):
        migration.classify_campaign_seasons(apps, None)
        migration.classify_campaign_seasons(apps, None)

        self.assertEqual(
            AnnouncementFieldEvidence.objects.filter(
                batch_id__in=self.batch_ids,
                field_name="recruitment_type",
            ).count(),
            3,
        )

        migration.restore_previous_types(apps, None)
        for item, batch_id in zip(
            migration.SEASON_CLASSIFICATIONS, self.batch_ids
        ):
            self.assertEqual(
                RecruitmentBatch.objects.get(pk=batch_id).recruitment_type,
                item["previous_type"],
            )
