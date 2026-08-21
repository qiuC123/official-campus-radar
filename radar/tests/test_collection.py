from pathlib import Path
from unittest.mock import patch

import requests
from django.test import TestCase

from radar.collectors.base import FetchedPage
from radar.collectors.html import HtmlSourceAdapter
from radar.models import FetchRun, OfficialSource, Organization, SourceVersion


class HtmlCollectionTests(TestCase):
    def setUp(self) -> None:
        organization = Organization.objects.create(name="示例公司", company_type="internet", industry="互联网", official_domain="careers.example.test")
        self.source = OfficialSource.objects.create(
            organization=organization, source_type="website", source_url="https://careers.example.test/notices",
            admission_evidence="官网招聘入口", is_verified=True, is_active=True, parser_config={
                "adapter": "html_selector", "notice_selector": "article.job", "notice_url_selector": "a.notice", "title_selector": "h2", "recruitment_type_selector": ".type",
                "location_selector": ".location", "deadline_selector": ".deadline",
                "application_selector": "a.apply", "excerpt_selector": ".description",
            },
        )
        self.fixture_text = (Path(__file__).parent / "fixtures" / "official_notice.html").read_text(encoding="utf-8")

    @staticmethod
    def multi_position_config() -> dict:
        return {
            "notice_selector": "article.job",
            "notice_id_attribute": "data-notice-id",
            "notice_url_selector": "a.notice",
            "title_selector": "h2",
            "recruitment_type_selector": ".type",
            "target_audience_selector": ".audience",
            "published_on_selector": ".published",
            "deadline_selector": ".deadline",
            "excerpt_selector": ".description",
            "position_selector": ".position",
            "position_id_attribute": "data-position-id",
            "position_title_selector": ".position-title",
            "location_selector": ".location",
            "application_selector": "a.apply",
            "positions_complete": True,
        }

    def test_fetches_fixture_and_extracts_one_candidate(self) -> None:
        adapter = HtmlSourceAdapter()
        with patch("radar.collectors.html.requests.Session.get") as get:
            get.return_value.status_code = 200
            get.return_value.text = self.fixture_text
            get.return_value.url = self.source.source_url
            get.return_value.headers = {"ETag": '"fixture-v1"'}
            page = adapter.fetch(self.source)
        self.assertEqual(page.http_status, 200)
        self.assertFalse(page.not_modified)
        self.assertEqual(len(adapter.extract(self.source, page)), 1)
        self.assertEqual(FetchRun.objects.count(), 0)
        self.assertEqual(SourceVersion.objects.count(), 0)

    def test_304_marks_page_not_modified_and_writes_no_version(self) -> None:
        adapter = HtmlSourceAdapter()
        self.source.last_etag = '"old"'
        self.source.save(update_fields=["last_etag"])
        with patch("radar.collectors.html.requests.Session.get") as get:
            get.return_value.status_code = 304
            get.return_value.text = ""
            get.return_value.url = self.source.source_url
            get.return_value.headers = {}
            page = adapter.fetch(self.source)
        self.assertTrue(page.not_modified)
        self.assertEqual(SourceVersion.objects.count(), 0)
        self.assertEqual(FetchRun.objects.count(), 0)

    def test_request_failure_is_recorded_without_storing_sensitive_headers(self) -> None:
        adapter = HtmlSourceAdapter()
        with patch("radar.collectors.html.requests.Session.get", side_effect=requests.RequestException("network unavailable")):
            with self.assertRaises(requests.RequestException):
                adapter.fetch(self.source)
        self.assertEqual(FetchRun.objects.count(), 0)

    def test_extracts_multiple_position_nodes_under_one_notice(self) -> None:
        self.source.parser_config = self.multi_position_config()
        page = FetchedPage(
            self.source.source_url,
            """
            <article class="job" data-notice-id="notice-2027">
              <a class="notice" href="/notices/2027">notice</a>
              <h2>2027 Campus</h2><span class="type">campus_recruitment</span>
              <span class="audience">2027 graduates</span>
              <time class="published">2026-08-01</time>
              <time class="deadline">2026-09-01</time>
              <p class="description">Two open roles</p>
              <div class="position" data-position-id="position-1">
                <span class="position-title">Engineer</span>
                <span class="location">Beijing</span>
                <a class="apply" href="/apply/1">apply</a>
              </div>
              <div class="position" data-position-id="position-2">
                <span class="position-title">Designer</span>
                <span class="location">Shanghai</span>
                <a class="apply" href="/apply/2">apply</a>
              </div>
            </article>
            """,
            "f" * 64,
            200,
            None,
        )

        candidates = HtmlSourceAdapter().extract(self.source, page)

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(
            [position.position_key for position in candidate.positions],
            ["position-1", "position-2"],
        )
        self.assertEqual(
            [position.title for position in candidate.positions],
            ["Engineer", "Designer"],
        )
        self.assertEqual(
            [position.location_text for position in candidate.positions],
            ["Beijing", "Shanghai"],
        )
        self.assertEqual(
            [position.application_url for position in candidate.positions],
            [
                "https://careers.example.test/apply/1",
                "https://careers.example.test/apply/2",
            ],
        )
        self.assertNotEqual(
            candidate.positions[0].locator,
            candidate.positions[1].locator,
        )
        self.assertIn("position-1", candidate.positions[0].locator)
        self.assertIn("position-2", candidate.positions[1].locator)
        self.assertTrue(candidate.positions_complete)

    def test_zero_position_selector_matches_fail_closed(self) -> None:
        self.source.parser_config = self.multi_position_config()
        page = FetchedPage(
            self.source.source_url,
            """
            <article class="job" data-notice-id="notice-2027">
              <a class="notice" href="/notices/2027">notice</a>
              <h2>2027 Campus</h2><span class="type">campus_recruitment</span>
              <span class="audience">2027 graduates</span>
              <time class="published">2026-08-01</time>
              <time class="deadline">2026-09-01</time>
              <p class="description">Selector no longer matches</p>
            </article>
            """,
            "e" * 64,
            200,
            None,
        )

        candidate = HtmlSourceAdapter().extract(self.source, page)[0]

        self.assertEqual(candidate.positions, ())
        self.assertFalse(candidate.positions_complete)

    def test_multi_position_identity_can_come_from_a_child_selector(self) -> None:
        self.source.parser_config = self.multi_position_config()
        self.source.parser_config.pop("position_id_attribute")
        self.source.parser_config["position_id_selector"] = ".position-id"
        page = FetchedPage(
            self.source.source_url,
            """
            <article class="job" data-notice-id="notice-2027">
              <a class="notice" href="/notices/2027">notice</a>
              <h2>2027 Campus</h2><span class="type">campus_recruitment</span>
              <span class="audience">2027 graduates</span>
              <time class="published">2026-08-01</time>
              <time class="deadline">2026-09-01</time>
              <p class="description">Two open roles</p>
              <div class="position">
                <span class="position-id">position-1</span>
                <span class="position-title">Engineer</span>
                <span class="location">Beijing</span>
              </div>
              <div class="position">
                <span class="position-id">position-2</span>
                <span class="position-title">Designer</span>
                <span class="location">Shanghai</span>
              </div>
            </article>
            """,
            "d" * 64,
            200,
            None,
        )

        candidate = HtmlSourceAdapter().extract(self.source, page)[0]

        self.assertEqual(
            [position.position_key for position in candidate.positions],
            ["position-1", "position-2"],
        )
        self.assertNotEqual(
            candidate.positions[0].locator,
            candidate.positions[1].locator,
        )
