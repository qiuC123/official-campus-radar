from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from radar.models import UpdateRun


SHANGHAI = ZoneInfo("Asia/Shanghai")
SCHEDULE_TIME = time(22, 0)


def expected_scheduled_date(now: datetime):
    local = now.astimezone(SHANGHAI)
    return local.date() if local.time() >= SCHEDULE_TIME else local.date() - timedelta(days=1)


def scheduled_run_is_missing(now: datetime) -> bool:
    local = now.astimezone(SHANGHAI)
    if (
        local.time() < SCHEDULE_TIME
        and not UpdateRun.objects.filter(trigger=UpdateRun.Trigger.SCHEDULED).exists()
    ):
        return False
    return not UpdateRun.objects.filter(
        trigger=UpdateRun.Trigger.SCHEDULED,
        status__in=[UpdateRun.Status.SUCCESS, UpdateRun.Status.PARTIAL_FAILURE],
        scheduled_for_date=expected_scheduled_date(local),
    ).exists()


def latest_successful_update() -> UpdateRun | None:
    return UpdateRun.objects.filter(status__in=[UpdateRun.Status.SUCCESS, UpdateRun.Status.PARTIAL_FAILURE]).order_by("-completed_at", "-started_at").first()


def latest_source_failures():
    latest_run = UpdateRun.objects.order_by("-started_at", "-pk").first()
    if latest_run is None or latest_run.status not in {
        UpdateRun.Status.PARTIAL_FAILURE,
        UpdateRun.Status.FAILED,
    }:
        return []
    return list(
        latest_run.fetch_runs.filter(status="failed")
        .select_related("source__organization")
        .order_by("source__organization__name")
    )


def scheduled_command_arguments(project_root: Path) -> list[str]:
    return ["-3.13", str(project_root / "manage.py"), "run_daily_update", "--trigger", "scheduled"]
