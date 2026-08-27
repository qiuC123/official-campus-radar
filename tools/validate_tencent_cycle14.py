"""Offline correction of the Cycle 13 Tencent scope whitelist."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "tools" / "api-acceptance-cycle-14-tencent-offline.json"
DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t3-api-acceptance-cycle-14-tencent-offline.json"


def run(config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_report = json.loads(
        (ROOT / config["source_report"]).read_text(encoding="utf-8")
    )
    source_config = json.loads(
        (ROOT / config["source_config"]).read_text(encoding="utf-8")
    )
    result = source_report["results"][0]
    target = source_config["targets"][0]
    mapping = source_config["mapping_evidence"]
    checks = {
        "company_key": result["key"] == config["expected_company_key"],
        "minimal_request": result["minimal_request"] is True,
        "no_cookies": result["cookies_sent"] is False,
        "complete": result["complete"] is True,
        "expected_total": result["reported_total"]
        == result["unique_ids"]
        == config["expected_total"],
        "required_fields": result["missing_required_fields"] == [],
        "mapping_ids": mapping["campus_mapping_ids"]
        == config["expected_mapping_ids"]
        == target["request"]["projectMappingIdList"],
        "mapping_names": mapping["campus_mapping_names"]
        == config["expected_mapping_names"],
        "observed_labels": set(result["scope_raw_values"])
        == set(config["allowed_observed_labels"]),
    }
    passed = all(checks.values())
    return {
        "cycle": config["cycle"],
        "mode": "offline re-evaluation; no network request",
        "source_cycle": source_report["cycle"],
        "source_cycle_failure_preserved": source_report["passed"] is False,
        "correction": (
            "Cycle 13 used an incomplete recruitLabelName whitelist. "
            "The request itself was already constrained by the verified campus "
            "projectMappingIdList [1, 14, 9]."
        ),
        "network_requests_made": 0,
        "database_writes": False,
        "checks": checks,
        "reported_total": result["reported_total"],
        "unique_ids": result["unique_ids"],
        "observed_labels": result["scope_raw_values"],
        "stable_count_added": 1 if passed else 0,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = run(args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"{report['cycle']}: {'PASS' if report['passed'] else 'FAIL'} "
        f"({report['unique_ids']}/{report['reported_total']}; offline)"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
