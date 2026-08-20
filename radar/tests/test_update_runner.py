from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from radar.collectors.base import FetchedPage, NoticeCandidate, PositionCandidate
from radar.models import OfficialSource, Organization, RecruitmentNotice
from radar.services.update_runner import run_update
from radar.tests.helpers import complete_candidate, create_enabled_source


class HealthyAdapter:
    def fetch(self, source):
        return FetchedPage(source.source_url, "fixture", "b" * 64, 200, None)

    def extract(self, source, page):
        return [complete_candidate(source, title="2027 校园招聘")]


class FailingAdapter:
    def fetch(self, source):
        raise RuntimeError("fixture source failure")


class UpdateRunnerTests(TestCase):
    def setUp(self) -> None:
        self.good = create_enabled_source(name="成功公司", host="good.example.test")
        self.bad = create_enabled_source(name="失败公司", host="bad.example.test")
        self.good_org = self.good.organization
        self.bad_org = self.bad.organization

    def test_one_source_failure_does_not_block_successful_source(self) -> None:
        with patch("radar.services.update_runner.AdapterRegistry.get", side_effect=[HealthyAdapter(), FailingAdapter()]):
            summary = run_update(trigger="scheduled", now=datetime(2026, 8, 17, 22, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
        self.assertEqual(summary.sources_checked, 2)
        self.assertEqual(summary.sources_failed, 1)
        self.assertEqual(summary.notices_created, 1)
        self.assertTrue(summary.update_run_id)

    def test_expiration_requires_a_successful_source_check(self) -> None:
        RecruitmentNotice.objects.create(organization=self.good_org, source=self.good, identity_key="good-old", title="已过期", official_notice_url="https://good.example.test/old", deadline=date(2026, 8, 16))
        RecruitmentNotice.objects.create(organization=self.bad_org, source=self.bad, identity_key="bad-old", title="失败来源保留", official_notice_url="https://bad.example.test/old", deadline=date(2026, 8, 16))
        with patch("radar.services.update_runner.AdapterRegistry.get", side_effect=[HealthyAdapter(), FailingAdapter()]):
            run_update(trigger="scheduled", now=datetime(2026, 8, 17, 22, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
        self.assertEqual(RecruitmentNotice.objects.get(organization=self.good_org, official_notice_url="https://good.example.test/old").status, "expired")
        self.assertEqual(RecruitmentNotice.objects.get(organization=self.bad_org, official_notice_url="https://bad.example.test/old").status, "active")

    def test_command_fails_when_no_active_admitted_source_can_complete(self) -> None:
        OfficialSource.objects.update(is_active=False)
        with self.assertRaises(CommandError):
            call_command("run_daily_update", "--trigger", "scheduled")
