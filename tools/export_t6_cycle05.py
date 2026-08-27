from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_radar.settings")

import django

django.setup()

from radar.models import (  # noqa: E402
    FetchRun,
    OfficialSource,
    PublicationEvent,
    RecruitmentBatch,
    RecruitmentPosition,
    SourceVersion,
    UpdateRun,
)
from radar.services.admission import source_is_admitted  # noqa: E402
from tools.t6_cycle05_unicom_browser_config import (  # noqa: E402
    BROWSER_CONFIG,
    COMPANY,
    NEW_ADAPTER,
)


DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t6-cycle-05.json"
EXPECTED_RUN_ID = 11
BACKUP = Path(
    r"C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t6-cycle05-20260827-184535.sqlite3"
)
BACKUP_SHA256 = "D133AD9769CC981B4C2D89151DC2CF1CF4C6A5C8422F474EA167067CF0DF7BD4"


def build_report() -> dict:
    source = OfficialSource.objects.select_related("organization").get(
        organization__name=COMPANY
    )
    run = UpdateRun.objects.get(pk=EXPECTED_RUN_ID)
    fetch = FetchRun.objects.get(update_run=run, source=source)
    version = SourceVersion.objects.get(fetch_run=fetch)
    publications = PublicationEvent.objects.filter(source_version=version)
    batches = RecruitmentBatch.objects.filter(source=source)
    positions = RecruitmentPosition.objects.filter(batch__source=source)

    if source.adapter_name != NEW_ADAPTER or not source_is_admitted(source):
        raise ValueError("China Unicom isolated-browser source is not admitted")
    if run.status != UpdateRun.Status.SUCCESS or fetch.status != FetchRun.Status.SUCCESS:
        raise ValueError("Cycle 05 update and fetch must both be successful")
    if fetch.http_status != 200 or not version.is_applied:
        raise ValueError("Cycle 05 source version was not applied")
    if publications.count() != 1 or batches.count() != 1:
        raise ValueError("Cycle 05 must publish exactly one China Unicom batch")
    if positions.count() != 2704 or positions.filter(is_current=True).count() != 2704:
        raise ValueError("Cycle 05 must retain all 2704 current positions")
    if not BACKUP.exists() or BACKUP.stat().st_size != 10_100_736:
        raise ValueError("Cycle 05 pre-write backup is missing or changed")
    backup_hash = hashlib.sha256(BACKUP.read_bytes()).hexdigest().upper()
    if backup_hash != BACKUP_SHA256:
        raise ValueError("Cycle 05 pre-write backup hash changed")

    total = positions.count()
    page_size = source.parser_config["pagination"]["page_size"]
    return {
        "cycle": "Phase 02 / T6 Cycle 05",
        "scope": "China Unicom only",
        "authorization": {
            "owner_confirmed": True,
            "confirmed_on": "2026-08-27",
            "decision": "docs/adr/0004-isolated-production-browser-for-unicom.md",
            "scheduled_task_authorized": False,
        },
        "isolation": {
            "ephemeral_context": True,
            "headless": True,
            "environment_proxy_enabled": False,
            "imported_user_profile": False,
            "imported_storage_state": False,
            "configured_cookies": False,
            "request_headers_or_tokens_persisted": False,
            "allowed_entry_url": BROWSER_CONFIG["entry_url"],
            "allowed_endpoint": source.parser_config["endpoint"],
        },
        "pagination": {
            "frontend_page_size": BROWSER_CONFIG["frontend_page_size"],
            "collected_page_size": page_size,
            "total_positions": total,
            "expected_page_requests": math.ceil(total / page_size),
            "request_delay_seconds": source.parser_config[
                "request_delay_seconds"
            ],
            "max_pages": source.parser_config["pagination"]["max_pages"],
        },
        "database_backup": {
            "path": str(BACKUP),
            "bytes": BACKUP.stat().st_size,
            "sha256": backup_hash,
        },
        "update_run": {
            "id": run.pk,
            "status": run.status,
            "error_message": run.error_message,
            "fetch_run_id": fetch.pk,
            "fetch_status": fetch.status,
            "http_status": fetch.http_status,
            "source_version_id": version.pk,
            "source_version_applied": version.is_applied,
            "publication_event_count": publications.count(),
        },
        "source_state": {
            "source_id": source.pk,
            "adapter_name": source.adapter_name,
            "admission_state": source.admission_state,
            "is_active": source.is_active,
            "admitted": True,
            "admission_event_count": source.admission_events.count(),
            "batch_count": batches.count(),
            "position_count": positions.count(),
            "current_position_count": positions.filter(is_current=True).count(),
        },
        "database_totals": {
            "batch_count": RecruitmentBatch.objects.count(),
            "current_position_count": RecruitmentPosition.objects.filter(
                is_current=True
            ).count(),
        },
        "raw_response_body_persisted": False,
        "outcome": "published_all_25_sources",
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
            raise SystemExit("T6 Cycle 05 report is stale")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print("source=15 run=11 positions=2704 outcome=published_all_25_sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
