from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_radar.settings")

import django

django.setup()

from radar.models import FetchRun, OfficialSource, PublicationEvent, RecruitmentBatch, RecruitmentPosition, UpdateRun
from tools.t6_cycle03_unicom_config import COMPANY, MINIMAL_HEADERS, SUCCESS_GUARD


DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t6-cycle-03.json"
EXPECTED_RUN_IDS = (9, 10)


def build_report() -> dict:
    source = OfficialSource.objects.select_related("organization").get(
        organization__name=COMPANY
    )
    runs = list(UpdateRun.objects.filter(pk__in=EXPECTED_RUN_IDS).order_by("pk"))
    if [run.pk for run in runs] != list(EXPECTED_RUN_IDS):
        raise ValueError("the two exact Cycle 03 update runs are required")
    fetches = list(FetchRun.objects.filter(update_run_id__in=EXPECTED_RUN_IDS).order_by("update_run_id"))
    if len(fetches) != 2 or any(fetch.source_id != source.pk for fetch in fetches):
        raise ValueError("Cycle 03 must contain two China Unicom-only fetches")
    if any(fetch.status != FetchRun.Status.FAILED for fetch in fetches):
        raise ValueError("both Cycle 03 fetches must retain their failed outcome")
    if PublicationEvent.objects.filter(
        source_version__fetch_run__update_run_id__in=EXPECTED_RUN_IDS
    ).exists():
        raise ValueError("failed Cycle 03 fetches must not publish")
    if source.parser_config.get("headers") != MINIMAL_HEADERS:
        raise ValueError("China Unicom minimal headers do not match Cycle 03 evidence")
    if source.parser_config.get("success") != SUCCESS_GUARD:
        raise ValueError("China Unicom success guard is missing")

    return {
        "cycle": "Phase 02 / T6 Cycle 03",
        "scope": "China Unicom only",
        "development_discovery_report": "work/phase-02-t6-cycle-03-unicom-discovery.md",
        "discovery": {
            "page_contexts": 1,
            "page_openings": 1,
            "endpoint": "https://fe.zhaopin.com/grace/api/dsc/search-job-list",
            "list_path": "data.jobList",
            "observed_page_size": 11,
            "observed_total": 2704,
            "minimal_replay_initially_passed": True,
            "credentials_or_signatures_required": False,
        },
        "production_config": {
            "headers": MINIMAL_HEADERS,
            "success": SUCCESS_GUARD,
            "page_size": source.parser_config["pagination"]["page_size"],
            "max_pages": source.parser_config["pagination"]["max_pages"],
            "environment_proxy_enabled": False,
        },
        "update_runs": [
            {
                "id": run.pk,
                "status": run.status,
                "error_message": run.error_message,
                "fetch_status": fetch.status,
                "fetch_error": fetch.error_message,
            }
            for run, fetch in zip(runs, fetches, strict=True)
        ],
        "source_state": {
            "source_id": source.pk,
            "admission_state": source.admission_state,
            "is_active": source.is_active,
            "admission_event_count": source.admission_events.count(),
            "batch_count": RecruitmentBatch.objects.filter(source=source).count(),
            "position_count": RecruitmentPosition.objects.filter(batch__source=source).count(),
        },
        "outcome": "not_published_upstream_business_error",
        "daily_browser_collection_used": False,
        "raw_responses_persisted": False,
        "completed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build_report(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        if existing != rendered:
            raise SystemExit("T6 Cycle 03 report is stale")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print("source=15 runs=2 published=0 outcome=upstream_business_error")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
