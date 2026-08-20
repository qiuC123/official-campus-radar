import hashlib
from dataclasses import replace
from unittest.mock import patch

from django.test import TestCase

from radar.collectors.base import PositionCandidate
from radar.models import ApplicationLink, Evidence, NoticePosition, RecruitmentNotice, SourceVersion
from radar.services.publication import publish_candidate
from radar.tests.helpers import (
    complete_candidate,
    create_enabled_source,
    field_evidence,
    publish_formal_notice,
)


class PublicationRemediationTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source(name="Publish Org")
        self.version_number = 0

    def version(self):
        self.version_number += 1
        return SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash=str(self.version_number) * 64,
        )

    def candidate(self, positions, *, withdrawn=False):
        candidate = complete_candidate(self.source, application_url=None)
        return replace(candidate, positions=tuple(positions), withdrawn=withdrawn)

    def position(self, key, title, city, application_url=None):
        evidence = {
            "position_title": field_evidence(title, f"#{key} .title"),
            "location": field_evidence(city, f"#{key} .location"),
        }
        if application_url:
            evidence["application_link"] = field_evidence(
                application_url, f"#{key} a.apply@href"
            )
        return PositionCandidate(
            title,
            city,
            f"{title} {city}",
            application_url,
            position_key=key,
            field_evidence=evidence,
        )

    def test_only_target_city_positions_enter_formal_notice_and_have_field_evidence(self) -> None:
        result = publish_candidate(
            self.source,
            self.candidate(
                [
                    self.position("beijing", "Beijing role", "北京", "https://official.test/apply/beijing"),
                    self.position("hangzhou", "Hangzhou role", "杭州", "https://official.test/apply/hangzhou"),
                ]
            ),
            self.version(),
        )
        notice = RecruitmentNotice.objects.get(pk=result.notice_id)
        self.assertEqual(list(notice.positions.values_list("title", flat=True)), ["Beijing role"])
        self.assertTrue(Evidence.objects.filter(notice=notice, field_name="title", locator__gt="").exists())
        self.assertTrue(Evidence.objects.filter(notice=notice, field_name="position_title", position__isnull=False, locator__gt="").exists())
        self.assertTrue(Evidence.objects.filter(notice=notice, field_name="application_link", application_link__isnull=False, locator__gt="").exists())

    def test_mid_publication_failure_rolls_back_every_written_record(self) -> None:
        candidate = self.candidate([self.position("beijing", "Beijing role", "北京")])
        with patch.object(Evidence.objects, "create", side_effect=RuntimeError("write failed")):
            with self.assertRaises(RuntimeError):
                publish_candidate(self.source, candidate, self.version())
        self.assertEqual(RecruitmentNotice.objects.count(), 0)
        self.assertEqual(NoticePosition.objects.count(), 0)
        self.assertEqual(Evidence.objects.count(), 0)

    def test_unpermitted_https_application_host_is_rejected(self) -> None:
        result = publish_candidate(
            self.source,
            self.candidate([self.position("beijing", "Beijing role", "北京", "https://untrusted.test/apply")]),
            self.version(),
        )
        self.assertEqual(result.action, "rejected")
        self.assertIn("untrusted_application_url", result.reasons)

    def test_removed_position_and_link_remain_historical_and_withdrawn_notice_can_reopen(self) -> None:
        first = self.candidate(
            [
                self.position("a", "A", "北京", "https://official.test/a"),
                self.position("b", "B", "上海", "https://official.test/b"),
            ]
        )
        result = publish_candidate(self.source, first, self.version())
        publish_candidate(
            self.source,
            replace(first, withdrawn=True, positions=(), field_evidence={}),
            self.version(),
        )
        notice = RecruitmentNotice.objects.get(pk=result.notice_id)
        self.assertEqual(notice.status, "withdrawn")
        self.assertFalse(NoticePosition.objects.get(notice=notice, position_key="b").is_current)
        self.assertFalse(ApplicationLink.objects.get(notice=notice, url="https://official.test/b").is_current)
        publish_candidate(
            self.source,
            self.candidate([self.position("a", "A", "北京", "https://official.test/a")]),
            self.version(),
        )
        notice.refresh_from_db()
        self.assertEqual(notice.status, "active")


class NormalizedLocationViewTests(TestCase):
    def test_city_filter_uses_normalized_locations_not_raw_text(self) -> None:
        source = create_enabled_source(name="View Org", host="view.test")
        notice = publish_formal_notice(source, location="北京")
        NoticePosition.objects.filter(notice=notice).update(location_text="华北地区")
        location_evidence = Evidence.objects.get(
            notice=notice,
            publication_event=notice.latest_publication_event,
            field_name="location",
        )
        Evidence.objects.filter(pk=location_evidence.pk).update(
            excerpt="华北地区",
            raw_value="华北地区",
            parsed_value="华北地区",
            value_hash=hashlib.sha256("华北地区".encode("utf-8")).hexdigest(),
        )
        response = self.client.get("/?city=北京")
        self.assertContains(response, notice.official_notice_url)
