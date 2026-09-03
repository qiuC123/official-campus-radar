from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from django.test import TestCase

from radar.models import UpdateRun
from radar.services.update_status import (
    expected_scheduled_at,
    scheduled_command_arguments,
    scheduled_run_is_missing,
)


def shanghai_datetime(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("Asia/Shanghai"))


class UpdateStatusTests(TestCase):
    def test_expected_schedule_uses_noon_evening_and_previous_evening(self) -> None:
        self.assertEqual(
            expected_scheduled_at(shanghai_datetime(2026, 8, 17, 11, 59)),
            shanghai_datetime(2026, 8, 16, 20, 0),
        )
        self.assertEqual(
            expected_scheduled_at(shanghai_datetime(2026, 8, 17, 12, 1)),
            shanghai_datetime(2026, 8, 17, 12, 0),
        )
        self.assertEqual(
            expected_scheduled_at(shanghai_datetime(2026, 8, 17, 20, 1)),
            shanghai_datetime(2026, 8, 17, 20, 0),
        )

    def test_missing_schedule_checks_each_due_slot(self) -> None:
        self.assertFalse(
            scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 11, 59))
        )
        self.assertTrue(
            scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 12, 1))
        )
        UpdateRun.objects.create(
            trigger="scheduled",
            scheduled_for_date=date(2026, 8, 17),
            status="success",
            started_at=shanghai_datetime(2026, 8, 17, 12, 0),
        )
        self.assertFalse(
            scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 19, 59))
        )
        self.assertTrue(
            scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 20, 1))
        )
        UpdateRun.objects.create(
            trigger="scheduled",
            scheduled_for_date=date(2026, 8, 17),
            status="partial_failure",
            started_at=shanghai_datetime(2026, 8, 17, 20, 0),
        )
        self.assertFalse(
            scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 20, 1))
        )

    def test_manual_success_cannot_satisfy_scheduled_audit_record(self) -> None:
        UpdateRun.objects.create(
            trigger="scheduled",
            scheduled_for_date=date(2026, 8, 17),
            status="failed",
            started_at=shanghai_datetime(2026, 8, 17, 20, 0),
        )
        UpdateRun.objects.create(
            trigger="manual",
            status="success",
            started_at=shanghai_datetime(2026, 8, 17, 20, 0),
        )
        self.assertTrue(
            scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 20, 1))
        )

    def test_scheduled_task_argument_contract(self) -> None:
        root = Path(r"D:\radar")
        self.assertEqual(scheduled_command_arguments(root), ["-3.13", str(root / "manage.py"), "run_daily_update", "--trigger", "scheduled"])
