from pathlib import Path
from unittest.mock import patch

import requests
from django.test import TestCase

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
