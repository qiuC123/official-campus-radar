"""One-request completeness check for China Telecom T3 Cycle 07."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "tools" / "api-completeness-cycle-07-telecom.json"
DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t3-api-completeness-cycle-07-telecom.json"
MINIMAL_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "OfficialCampusRadar/0.1 (local low-frequency completeness check)",
}


class CompletenessError(ValueError):
    pass


def get_path(document: Any, dotted_path: str) -> Any:
    current = document
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise CompletenessError(f"missing path: {dotted_path}")
        current = current[part]
    return current


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(target: dict[str, Any]) -> tuple[int, str, Any]:
    encoded = json.dumps(target["body"], separators=(",", ":")).encode("utf-8")
    api_request = request.Request(
        target["endpoint"],
        data=encoded,
        headers=MINIMAL_HEADERS,
        method="POST",
    )
    opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(api_request, timeout=20) as response:
            status = response.status
            content_type = response.headers.get("content-type", "")
            response_body = response.read()
    except error.HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get("content-type", "")
        response_body = exc.read()
    try:
        payload = json.loads(response_body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompletenessError("response is not JSON") from exc
    return status, content_type, payload


Requester = Callable[[dict[str, Any]], tuple[int, str, Any]]


def validate_target(
    target: dict[str, Any], requester: Requester = request_json
) -> dict[str, Any]:
    budget = target["request_budget"]
    if budget != {"maximum": 1, "already_spent": 0, "planned": 1}:
        raise CompletenessError("Cycle 07 requires exactly one fresh request")

    try:
        status, content_type, payload = requester(target)
        if status != 200:
            raise CompletenessError(f"HTTP {status}")
        rows = get_path(payload, target["list_path"])
        reported_total = get_path(payload, target["total_path"])
        if not isinstance(rows, list):
            raise CompletenessError("list_path did not resolve to a list")
        if not isinstance(reported_total, int) or isinstance(reported_total, bool):
            raise CompletenessError("total_path did not resolve to an integer")
        row_dicts = [row for row in rows if isinstance(row, dict)]
        missing_required = sorted(
            {
                field
                for row in row_dicts
                for field in target["required_fields"]
                if row.get(field) in (None, "", [])
            }
        )
        campus_values = sorted(
            {
                str(row.get(target["campus_field"]))
                for row in row_dicts
                if row.get(target["campus_field"]) not in (None, "")
            }
        )
        ids = [str(row.get(target["id_field"], "")) for row in row_dicts]
        complete = bool(row_dicts) and len(row_dicts) == reported_total
        unique_ids = bool(ids) and len(ids) == len(set(ids)) and all(ids)
        campus_ok = campus_values == [target["campus_expected"]]
        required_ok = not missing_required
        passed = complete and unique_ids and campus_ok and required_ok
        return {
            "key": target["key"],
            "company": target["company"],
            "endpoint": target["endpoint"],
            "official_page_url": target["official_page_url"],
            "minimal_request": True,
            "cookies_sent": False,
            "requests_made": 1,
            "request_budget_after_run": 1,
            "status": status,
            "content_type": content_type.split(";", 1)[0],
            "row_count": len(row_dicts),
            "reported_total": reported_total,
            "list_is_complete": complete,
            "ids_are_unique": unique_ids,
            "campus_raw_values": campus_values,
            "missing_required_fields": missing_required,
            "samples": [
                {field: row.get(field) for field in target["sample_fields"]}
                for row in row_dicts[:5]
            ],
            "errors": [],
            "passed": passed,
        }
    except (CompletenessError, error.URLError, TimeoutError) as exc:
        return {
            "key": target["key"],
            "company": target["company"],
            "minimal_request": True,
            "cookies_sent": False,
            "requests_made": 0,
            "errors": [str(exc)],
            "passed": False,
        }


def run(config_path: Path, requester: Requester = request_json) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    result = validate_target(config["target"], requester)
    return {
        "cycle": config["cycle"],
        "scope": "one-request list completeness check; not source admission",
        "source_admission_claimed": False,
        "database_writes": False,
        "raw_response_persisted": False,
        "result": result,
        "passed": result["passed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = run(args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Cycle 07 Telecom report: {args.output}")
    print(f"中国电信: {'PASS' if report['passed'] else 'FAIL'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
