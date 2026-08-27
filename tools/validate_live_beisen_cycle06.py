"""Bounded two-page Beisen API acceptance for Phase 02 T3 Cycle 06.

The tool sends exactly two anonymous JSON requests to each configured target,
persists only allow-listed fields, and never writes application data. It is a
development acceptance tool, not a production collector or source admission.
"""

from __future__ import annotations

import argparse
import copy
import json
import time
from pathlib import Path
from typing import Any, Callable
from urllib import error, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "tools" / "api-acceptance-cycle-06-beisen.json"
DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t3-api-acceptance-cycle-06-beisen.json"
MINIMAL_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "OfficialCampusRadar/0.1 (local low-frequency acceptance)",
}


class AcceptanceError(ValueError):
    pass


def get_path(document: Any, dotted_path: str) -> Any:
    current = document
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise AcceptanceError(f"missing path: {dotted_path}")
        current = current[part]
    return current


def make_body(target: dict[str, Any], page: int) -> dict[str, Any]:
    body = copy.deepcopy(target["base_body"])
    pagination = target["pagination"]
    body[pagination["page_param"]] = page
    body[pagination["size_param"]] = pagination["page_size"]
    return body


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(target: dict[str, Any], body: dict[str, Any]) -> tuple[int, str, Any]:
    encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
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
        raise AcceptanceError("response is not JSON") from exc
    return status, content_type, payload


Requester = Callable[[dict[str, Any], dict[str, Any]], tuple[int, str, Any]]


def sanitize_rows(target: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = target["sample_fields"]
    return [{field: row.get(field) for field in allowed} for row in rows[:5]]


def validate_target(target: dict[str, Any], requester: Requester = request_json) -> dict[str, Any]:
    budget = target["request_budget"]
    pages_to_request = target["pagination"]["pages"]
    if pages_to_request != [0, 1] or budget["planned"] != 2:
        raise AcceptanceError("Cycle 06 requires exactly Beisen pages 0 and 1")
    if budget["already_spent"] + budget["planned"] > budget["maximum"]:
        raise AcceptanceError(f"request budget exceeded for {target['company']}")

    pages: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, page_number in enumerate(pages_to_request):
        body = make_body(target, page_number)
        try:
            status, content_type, payload = requester(target, body)
            if status != 200:
                raise AcceptanceError(f"HTTP {status}")
            if get_path(payload, target["success"]["path"]) != target["success"]["expect"]:
                raise AcceptanceError("business success check failed")
            rows = get_path(payload, target["list_path"])
            if not isinstance(rows, list):
                raise AcceptanceError("list_path did not resolve to a list")
            row_dicts = [row for row in rows if isinstance(row, dict)]
            ids = [str(row.get(target["id_field"], "")) for row in row_dicts]
            missing_required = sorted(
                {
                    field
                    for row in row_dicts
                    for field in target["required_fields"]
                    if row.get(field) in (None, "", [])
                }
            )
            pages.append(
                {
                    "page_index": page_number,
                    "status": status,
                    "content_type": content_type.split(";", 1)[0],
                    "row_count": len(row_dicts),
                    "ids": ids,
                    "reported_total": get_path(payload, target["total_path"]),
                    "missing_required_fields": missing_required,
                    "samples": sanitize_rows(target, row_dicts),
                }
            )
        except (AcceptanceError, error.URLError, TimeoutError) as exc:
            errors.append(f"page {page_number}: {exc}")
            pages.append({"page_index": page_number, "error": str(exc)})
        if index == 0:
            time.sleep(1)

    first_ids = set(pages[0].get("ids", []))
    second_ids = set(pages[1].get("ids", []))
    distinct_pages = bool(first_ids and second_ids and first_ids.isdisjoint(second_ids))
    required_ok = all(
        not page.get("missing_required_fields")
        for page in pages
        if "error" not in page
    )
    campus = target["campus_evidence"]
    raw_value = target["base_body"].get(campus["request_field"])
    campus_ok = raw_value == campus["expected"] and bool(campus["raw_label"])
    passed = not errors and distinct_pages and required_ok and campus_ok
    return {
        "key": target["key"],
        "company": target["company"],
        "endpoint": target["endpoint"],
        "official_page_url": target["official_page_url"],
        "minimal_request": True,
        "cookies_sent": False,
        "requests_made": sum(1 for page in pages if "status" in page),
        "request_budget_after_run": budget["already_spent"] + budget["planned"],
        "pages": pages,
        "pagination": {"page_ids_are_distinct": distinct_pages, "passed": distinct_pages},
        "campus_evidence": {
            "field": campus["request_field"],
            "raw_value": raw_value,
            "raw_label": campus["raw_label"],
            "passed": campus_ok,
        },
        "required_fields_passed": required_ok,
        "errors": errors,
        "passed": passed,
    }


def run(config_path: Path, requester: Requester = request_json) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    results = [validate_target(target, requester) for target in config["targets"]]
    return {
        "cycle": config["cycle"],
        "scope": "read-only two-page Beisen acceptance; not source admission",
        "source_admission_claimed": False,
        "database_writes": False,
        "raw_responses_persisted": False,
        "skipped_targets": config.get("skipped_targets", []),
        "results": results,
        "passed": all(result["passed"] for result in results),
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
    print(f"Cycle 06 Beisen report: {args.output}")
    for result in report["results"]:
        print(f"{result['company']}: {'PASS' if result['passed'] else 'FAIL'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
