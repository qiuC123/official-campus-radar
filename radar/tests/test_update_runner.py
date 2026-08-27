from dataclasses import replace
from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from radar.collectors.base import FetchedPage, RecruitmentBatchCandidate, PositionCandidate
from radar.models import (
    FetchRun,
    OfficialSource,
    Organization,
    PublicationEvent,
    RecruitmentBatch,
    RecruitmentPosition,
    SourceVersion,
)
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


class RejectingAdapter(HealthyAdapter):
    def extract(self, source, page):
        candidate = complete_candidate(source, title="社会招聘")
        return [replace(candidate, recruitment_type="other")]


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
        self.assertEqual(summary.batches_created, 1)
        self.assertTrue(summary.update_run_id)

    def test_expiration_requires_a_successful_source_check(self) -> None:
        good_batch = RecruitmentBatch.objects.create(organization=self.good_org, source=self.good, identity_key="good-old", title="已过期", official_page_url="https://good.example.test/old", deadline=date(2026, 8, 16))
        good_position = RecruitmentPosition.objects.create(
            batch=good_batch,
            position_key="old-position",
            title="旧岗位",
            location_text="北京",
            normalized_locations=["北京"],
        )
        original_changed_at = good_position.content_changed_at
        RecruitmentBatch.objects.create(organization=self.bad_org, source=self.bad, identity_key="bad-old", title="失败来源保留", official_page_url="https://bad.example.test/old", deadline=date(2026, 8, 16))
        with patch("radar.services.update_runner.AdapterRegistry.get", side_effect=[HealthyAdapter(), FailingAdapter()]):
            run_update(trigger="scheduled", now=datetime(2026, 8, 17, 22, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
        self.assertEqual(RecruitmentBatch.objects.get(organization=self.good_org, official_page_url="https://good.example.test/old").status, "expired")
        self.assertEqual(RecruitmentBatch.objects.get(organization=self.bad_org, official_page_url="https://bad.example.test/old").status, "active")
        good_position.refresh_from_db()
        self.assertGreater(good_position.content_changed_at, original_changed_at)

    def test_command_fails_when_no_active_admitted_source_can_complete(self) -> None:
        OfficialSource.objects.update(is_active=False)
        with self.assertRaises(CommandError):
            call_command("run_daily_update", "--trigger", "scheduled")

    def test_rejected_same_hash_requires_explicit_scoped_reprocessing(self) -> None:
        OfficialSource.objects.exclude(pk=self.good.pk).update(is_active=False)
        with patch(
            "radar.services.update_runner.AdapterRegistry.get",
            return_value=RejectingAdapter(),
        ):
            first = run_update(trigger="manual", source_ids=[self.good.pk])
            unchanged = run_update(trigger="manual", source_ids=[self.good.pk])
            retried = run_update(
                trigger="manual",
                source_ids=[self.good.pk],
                reprocess_rejected=True,
            )

        self.assertEqual(first.status, "partial_failure")
        self.assertEqual(first.batches_rejected, 1)
        self.assertEqual(unchanged.batches_rejected, 0)
        self.assertEqual(retried.batches_rejected, 1)
        self.assertEqual(SourceVersion.objects.filter(source=self.good).count(), 2)
        self.assertEqual(
            PublicationEvent.objects.filter(
                source_version__source=self.good,
                event_type="rejected",
            ).count(),
            2,
        )
        self.assertEqual(
            FetchRun.objects.filter(source=self.good, status="unchanged").count(),
            1,
        )

    def test_reprocessing_flag_is_manual_and_requires_explicit_sources(self) -> None:
        with self.assertRaisesRegex(CommandError, "only be reprocessed manually"):
            call_command(
                "run_daily_update",
                "--trigger",
                "scheduled",
                "--source-id",
                str(self.good.pk),
                "--reprocess-rejected",
            )

    def test_service_rejects_unscoped_or_scheduled_reprocessing(self) -> None:
        with self.assertRaisesRegex(ValueError, "only be reprocessed manually"):
            run_update(
                trigger="scheduled",
                source_ids=[self.good.pk],
                reprocess_rejected=True,
            )
        with self.assertRaisesRegex(ValueError, "requires source IDs"):
            run_update(trigger="manual", reprocess_rejected=True)
        with self.assertRaisesRegex(CommandError, "requires --source-id"):
            call_command(
                "run_daily_update",
                "--trigger",
                "manual",
                "--reprocess-rejected",
            )
