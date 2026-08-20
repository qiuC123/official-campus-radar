from dataclasses import replace

from django.test import TestCase

from radar.models import (
    ApplicationLink,
    ApplicationProgress,
    NoticePosition,
    RecruitmentNotice,
    SourceVersion,
)
from radar.services.publication import publish_candidates
from radar.tests.helpers import complete_candidate, create_enabled_source


class HistoricalProjectionTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source(name="Historical Projection")
        self.version_number = 0

    def version(self) -> SourceVersion:
        self.version_number += 1
        return SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash=str(self.version_number) * 64,
            is_applied=True,
        )

    def publish(self, *, identity_key: str, location: str = "北京"):
        candidate = complete_candidate(
            self.source,
            identity_key=identity_key,
            location=location,
            application_url=f"https://official.test/apply/{identity_key}",
        )
        result = publish_candidates(self.source, [candidate], self.version())[0]
        return candidate, RecruitmentNotice.objects.get(pk=result.notice_id)

    def test_withdrawn_history_filters_use_the_prior_trusted_event_projection(self) -> None:
        candidate, notice = self.publish(identity_key="withdrawn-history")
        progress = ApplicationProgress.objects.create(
            notice=notice,
            status=ApplicationProgress.Status.INTERVIEWED,
        )
        publish_candidates(
            self.source,
            [replace(candidate, withdrawn=True, positions=(), field_evidence={})],
            self.version(),
        )

        by_city = self.client.get(
            "/", {"status": RecruitmentNotice.Status.WITHDRAWN, "city": "北京"}
        )
        by_position = self.client.get(
            "/",
            {"status": RecruitmentNotice.Status.WITHDRAWN, "position": "Engineer"},
        )

        self.assertContains(by_city, notice.official_notice_url)
        self.assertContains(by_city, "Engineer")
        self.assertContains(by_position, notice.official_notice_url)
        progress.refresh_from_db()
        self.assertEqual(progress.status, ApplicationProgress.Status.INTERVIEWED)

    def test_expired_history_filters_use_the_trusted_event_projection(self) -> None:
        _, notice = self.publish(identity_key="expired-history", location="上海")
        notice.status = RecruitmentNotice.Status.EXPIRED
        notice.save(update_fields=["status"])

        by_city = self.client.get(
            "/", {"status": RecruitmentNotice.Status.EXPIRED, "city": "上海"}
        )
        by_position = self.client.get(
            "/",
            {"status": RecruitmentNotice.Status.EXPIRED, "position": "Engineer"},
        )

        self.assertContains(by_city, notice.official_notice_url)
        self.assertContains(by_position, notice.official_notice_url)

    def test_history_does_not_display_or_filter_by_children_outside_selected_event(self) -> None:
        candidate, notice = self.publish(identity_key="event-bound-history")
        publish_candidates(
            self.source,
            [replace(candidate, withdrawn=True, positions=(), field_evidence={})],
            self.version(),
        )
        unrelated_position = NoticePosition.objects.create(
            notice=notice,
            position_key="unrelated-position",
            title="Ghost Analyst",
            location_text="深圳",
            normalized_locations=["深圳"],
            raw_text="Ghost Analyst 深圳",
            is_current=True,
        )
        unrelated_url = "https://official.test/apply/unrelated"
        ApplicationLink.objects.create(
            notice=notice,
            position=unrelated_position,
            url=unrelated_url,
            link_type=ApplicationLink.LinkType.APPLICATION,
            is_current=True,
        )

        unfiltered = self.client.get(
            "/", {"status": RecruitmentNotice.Status.WITHDRAWN}
        )
        by_unrelated_city = self.client.get(
            "/", {"status": RecruitmentNotice.Status.WITHDRAWN, "city": "深圳"}
        )
        by_unrelated_position = self.client.get(
            "/",
            {"status": RecruitmentNotice.Status.WITHDRAWN, "position": "Ghost"},
        )

        self.assertContains(unfiltered, "Engineer")
        self.assertContains(unfiltered, "https://official.test/apply/event-bound-history")
        self.assertNotContains(unfiltered, unrelated_position.title)
        self.assertNotContains(unfiltered, unrelated_url)
        self.assertNotContains(by_unrelated_city, notice.official_notice_url)
        self.assertNotContains(by_unrelated_position, notice.official_notice_url)

    def test_current_filters_ignore_non_current_historical_positions(self) -> None:
        _, notice = self.publish(identity_key="current-projection")
        NoticePosition.objects.create(
            notice=notice,
            position_key="legacy-position",
            title="Legacy Analyst",
            location_text="深圳",
            normalized_locations=["深圳"],
            raw_text="Legacy Analyst 深圳",
            is_current=False,
        )

        current = self.client.get("/")
        by_legacy_city = self.client.get("/", {"city": "深圳"})
        by_legacy_position = self.client.get("/", {"position": "Legacy"})

        self.assertContains(current, notice.official_notice_url)
        self.assertNotContains(current, "Legacy Analyst")
        self.assertNotContains(by_legacy_city, notice.official_notice_url)
        self.assertNotContains(by_legacy_position, notice.official_notice_url)
