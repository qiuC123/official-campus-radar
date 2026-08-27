from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_radar.settings")

import django

django.setup()

from radar.models import Evidence, FetchRun, PublicationEvent, UpdateRun


DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t6-cycle-02.json"
EXPECTED_SOURCE_IDS = (2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 15, 18, 19, 21, 22)
PROTECTED_SOURCE_IDS = (1, 9, 10, 14, 16, 17, 20, 23, 24, 25)


def build_report(update_run_ids: list[int]) -> dict:
    unique_run_ids = list(dict.fromkeys(update_run_ids))
    if not unique_run_ids or len(unique_run_ids) != len(update_run_ids):
        raise ValueError("update run IDs must be non-empty and unique")
    runs = list(UpdateRun.objects.filter(pk__in=unique_run_ids).order_by("pk"))
    if [run.pk for run in runs] != sorted(unique_run_ids):
        raise ValueError("one or more update runs are missing")
    if any(run.completed_at is None for run in runs):
        raise ValueError("all update runs must be complete")

    fetches = list(
        FetchRun.objects.filter(update_run_id__in=unique_run_ids)
        .select_related("source__organization", "update_run")
        .order_by("source_id")
    )
    if [fetch.source_id for fetch in fetches] != list(EXPECTED_SOURCE_IDS):
        raise ValueError("Cycle 02 must retry each of the exact 15 unpublished sources once")
    if any(fetch.source_id in PROTECTED_SOURCE_IDS for fetch in fetches):
        raise ValueError("Cycle 02 accessed a protected Cycle 01 success source")

    events = list(
        PublicationEvent.objects.filter(
            source_version__fetch_run__update_run_id__in=unique_run_ids
        ).select_related("source_version__source")
    )
    events_by_source: dict[int, list[PublicationEvent]] = {}
    for event in events:
        events_by_source.setdefault(event.source_version.source_id, []).append(event)

    results = []
    for fetch in fetches:
        source_events = events_by_source.get(fetch.source_id, [])
        if fetch.status == FetchRun.Status.FAILED:
            if source_events:
                raise ValueError("failed source must not have publication events")
            outcome = "failed"
            event_type = ""
            reasons = []
            accepted_positions = 0
        else:
            if len(source_events) != 1:
                raise ValueError("completed source must have exactly one publication event")
            event = source_events[0]
            event_type = event.event_type
            reasons = list(event.reason_codes)
            outcome = (
                "published"
                if event_type == PublicationEvent.EventType.PUBLISHED
                else "rejected"
            )
            accepted_positions = (
                Evidence.objects.filter(
                    publication_event=event,
                    field_name="position_title",
                    position_id__isnull=False,
                )
                .values("position_id")
                .distinct()
                .count()
                if outcome == "published"
                else 0
            )
        results.append(
            {
                "source_id": fetch.source_id,
                "company": fetch.source.organization.name,
                "update_run_id": fetch.update_run_id,
                "fetch_status": fetch.status,
                "http_status": fetch.http_status,
                "error": fetch.error_message,
                "publication_event": event_type,
                "reason_codes": reasons,
                "accepted_position_count": accepted_positions,
                "outcome": outcome,
            }
        )

    outcome_counts = Counter(result["outcome"] for result in results)
    return {
        "cycle": "Phase 02 / T6 Cycle 02",
        "mode": "scoped correction and retry of previously unpublished sources",
        "update_run_ids": [run.pk for run in runs],
        "database_writes": True,
        "raw_responses_persisted": False,
        "expected_source_ids": list(EXPECTED_SOURCE_IDS),
        "protected_source_ids_not_accessed": list(PROTECTED_SOURCE_IDS),
        "source_attempt_count": len(results),
        "published_source_count": outcome_counts["published"],
        "rejected_source_count": outcome_counts["rejected"],
        "failed_source_count": outcome_counts["failed"],
        "accepted_position_count": sum(
            result["accepted_position_count"] for result in results
        ),
        "run_statuses": [
            {
                "update_run_id": run.pk,
                "status": run.status,
                "error_message": run.error_message,
            }
            for run in runs
        ],
        "results": results,
        "completed": True,
        "outcome": "partial_acceptance",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-run-id", type=int, action="append", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build_report(args.update_run_id)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        if existing != rendered:
            raise SystemExit("T6 Cycle 02 report is stale")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(
        f"sources={report['source_attempt_count']} "
        f"published={report['published_source_count']} "
        f"rejected={report['rejected_source_count']} "
        f"failed={report['failed_source_count']} "
        f"positions={report['accepted_position_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
