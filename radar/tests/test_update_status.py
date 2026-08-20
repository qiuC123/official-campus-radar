from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from django.test import TestCase

from radar.models import UpdateRun
from radar.services.update_status import (scheduled_command_arguments,
                                          scheduled_run_is_missing)


def shanghai_datetime(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("Asia/Shanghai"))


class UpdateStatusTests(TestCase):
    def test_missing_schedule_respects_2200_boundary(self) -> None:
        self.assertFalse(scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 21, 59)))
        UpdateRun.objects.create(trigger="scheduled", scheduled_for_date=date(2026, 8, 16), status="success")
        self.assertTrue(scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 22, 1)))
        UpdateRun.objects.create(trigger="scheduled", scheduled_for_date=date(2026, 8, 17), status="success")
        self.assertFalse(scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 22, 1)))

    def test_manual_success_cannot_satisfy_scheduled_audit_record(self) -> None:
        UpdateRun.objects.create(trigger="scheduled", scheduled_for_date=date(2026, 8, 16), status="failed")
        UpdateRun.objects.create(trigger="manual", status="success")
        self.assertTrue(scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 22, 1)))

    def test_scheduled_task_argument_contract(self) -> None:
        root = Path(r"D:\radar")
        self.assertEqual(scheduled_command_arguments(root), ["-3.13", str(root / "manage.py"), "run_daily_update", "--trigger", "scheduled"])
