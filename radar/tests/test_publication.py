from datetime import date

from django.test import TestCase

from radar.models import (ApplicationProgress, OfficialSource, Organization,
                          SourceVersion)
from radar.services.publication import publish_candidate
from radar.tests.helpers import complete_candidate, create_enabled_source


class PublicationTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source(name="示例公司", host="careers.example.test")
        self.version = SourceVersion.objects.create(
            source=self.source, canonical_url="https://careers.example.test", content_hash="a" * 64
        )

    def candidate(self, *, title="2027 校园招聘", location="北京", url="https://careers.example.test/2027"):
        return complete_candidate(
            self.source,
            identity_key="notice-2027",
            title=title,
            location=location,
            notice_url=url,
        )

    def test_rejects_candidate_without_target_city(self) -> None:
        result = publish_candidate(self.source, self.candidate(location="杭州"), self.version)
        self.assertEqual(result.action, "rejected")
        self.assertIn("missing_target_location", result.reasons)

    def test_updates_notice_without_overwriting_personal_progress(self) -> None:
        created = publish_candidate(self.source, self.candidate(), self.version)
        progress = ApplicationProgress.objects.create(notice_id=created.notice_id, status="interviewed")
        updated = publish_candidate(self.source, self.candidate(title="2027 校招更新"), self.version)
        self.assertEqual(updated.action, "updated")
        progress.refresh_from_db()
        self.assertEqual(progress.status, "interviewed")
