from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase

from radar.collectors.base import FetchedPage, RecruitmentBatchCandidate, PositionCandidate
from radar.models import FetchRun, OfficialSource, Organization, RecruitmentBatch, SourceVersion, UpdateRun
from radar.services.admission import transition_source
from radar.services.update_runner import run_update
from radar.services.update_status import scheduled_run_is_missing
from radar.tests.helpers import complete_candidate, create_enabled_source
from radar.tests.helpers import valid_html_parser_config


class SamePageAdapter:
    def fetch(self, source):
        return FetchedPage(source.source_url, "same", "c" * 64, 200, None)

    def extract(self, source, page):
        return [complete_candidate(source, title="Campus")]


class FailingAdapter:
    def fetch(self, source):
        raise RuntimeError("source failed")


class UpdateCorrectnessTests(TestCase):
    def source(self, name, host):
        return create_enabled_source(name=name, host="official.test", path=f"/{host}")

    def test_same_200_hash_is_unchanged_and_does_not_republish(self) -> None:
        source = self.source("Same", "same")
        with patch("radar.services.update_runner.AdapterRegistry.get", return_value=SamePageAdapter()):
            first = run_update(trigger="manual")
            second = run_update(trigger="manual")
        self.assertEqual(SourceVersion.objects.filter(source=source).count(), 1)
        self.assertEqual(second.batches_updated, 0)

    def test_one_request_failure_creates_one_failed_fetch_run(self) -> None:
        source = self.source("Fetch", "fetch")
        with patch("radar.collectors.html.requests.Session.get", side_effect=requests.RequestException("down")):
            run_update(trigger="manual", source_ids=[source.pk])
        runs = FetchRun.objects.filter(source=source, status="failed")
        self.assertEqual(runs.count(), 1)
        self.assertIsNotNone(runs.get().update_run_id)

    def test_successful_source_does_not_expire_other_failed_source_notice(self) -> None:
        organization = Organization.objects.create(name="Shared", company_type="internet", industry="tech", official_domain="official.test")
        source_a = OfficialSource.objects.create(organization=organization, source_type="website", source_url="https://official.test/a", admission_evidence="reviewed", parser_config=valid_html_parser_config())
        source_b = OfficialSource.objects.create(organization=organization, source_type="website", source_url="https://official.test/b", admission_evidence="reviewed", parser_config=valid_html_parser_config())
        for source in (source_a, source_b):
            transition_source(source, to_state="verified", actor_label="owner", reason="verified", evidence="review")
            transition_source(source, to_state="enabled", actor_label="owner", reason="enabled", evidence="fixture")
        RecruitmentBatch.objects.create(organization=organization, source=source_a, identity_key="old-a", title="A", official_page_url="https://official.test/a/old", deadline=date(2026, 8, 16))
        with patch("radar.services.update_runner.AdapterRegistry.get", side_effect=[FailingAdapter(), SamePageAdapter()]):
            run_update(trigger="scheduled", now=datetime(2026, 8, 17, 22, 1, tzinfo=ZoneInfo("Asia/Shanghai")))
        self.assertEqual(RecruitmentBatch.objects.get(source=source_a).status, "active")


class UpdateStatusRemediationTests(TestCase):
    def test_previous_night_missing_is_reported_but_first_install_is_not(self) -> None:
        now = datetime(2026, 8, 18, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        self.assertFalse(scheduled_run_is_missing(now))
        UpdateRun.objects.create(trigger="scheduled", scheduled_for_date=date(2026, 8, 16), status="success")
        self.assertTrue(scheduled_run_is_missing(now))

    def test_manual_update_with_no_sources_does_not_claim_completion(self) -> None:
        administrator = get_user_model().objects.create_superuser("owner", "owner@example.test", "test")
        self.client.force_login(administrator)
        response = self.client.post("/update-now/", follow=True)
        self.assertContains(response, "未执行")
        self.assertNotContains(response, "手动更新完成")
