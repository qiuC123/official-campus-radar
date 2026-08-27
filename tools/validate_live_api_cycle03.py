"""Low-frequency, read-only API acceptance for Phase 02 T3 Cycle 03.

This tool makes at most two requests per configured target (page 1 and page 2),
does not use cookies, and stores only a small allow-listed sample rather than raw
responses. It is a development acceptance tool, not a production collector.
"""

from __future__ import annotations

import argparse
import copy
import json
import time
from pathlib import Path
from typing import Any, Callable
from urllib import error, parse, request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "tools" / "api-acceptance-cycle-03.json"
DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t3-api-acceptance-cycle-03.json"
MINIMAL_HEADERS = {
    "Accept": "application/json",
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


def make_values(target: dict[str, Any], page: int) -> dict[str, Any]:
    values = copy.deepcopy(target.get("base_values", {}))
    pagination = target["pagination"]
    values[pagination["page_param"]] = page
    values[pagination["size_param"]] = pagination["page_size"]
    return values


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(target: dict[str, Any], values: dict[str, Any]) -> tuple[int, str, Any]:
    url = target["endpoint"]
    body: bytes | None = None
    headers = dict(MINIMAL_HEADERS)
    encoding = target["body_encoding"]
    if encoding == "query":
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{parse.urlencode(values)}"
    elif encoding == "json":
        body = json.dumps(values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif encoding == "form":
        body = parse.urlencode(values).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        raise AcceptanceError(f"unsupported body encoding: {encoding}")

    api_request = request.Request(url, data=body, headers=headers, method=target["method"])
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


def campus_evidence(target: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    rule = target["campus_evidence"]
    mode = rule["mode"]
    if mode == "endpoint_contains":
        actual = rule["value"] in target["endpoint"]
        return {"mode": mode, "raw_values": [rule["value"]], "passed": actual}
    if mode == "request_value":
        value = target.get("base_values", {}).get(rule["field"])
        return {"mode": mode, "raw_values": [value], "passed": str(value) == rule["expected"]}
    if mode == "row_field":
        values = []
        for row in rows:
            value = row.get(rule["field"])
            if value not in (None, "") and value not in values:
                values.append(value)
        return {"mode": mode, "raw_values": values[:10], "passed": bool(values)}
    raise AcceptanceError(f"unsupported campus evidence mode: {mode}")


def sanitize_rows(target: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = target["sample_fields"]
    return [{field: row.get(field) for field in allowed} for row in rows[:5]]


def validate_target(target: dict[str, Any], requester: Requester = request_json) -> dict[str, Any]:
    budget = target["request_budget"]
    if budget["planned"] != 2:
        raise AcceptanceError("Cycle 03 requires exactly two planned requests per target")
    if budget["already_spent"] + budget["planned"] > budget["maximum"]:
        raise AcceptanceError(f"request budget exceeded for {target['company']}")

    pages: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for page_number in (1, 2):
        values = make_values(target, page_number)
        try:
            status, content_type, payload = requester(target, values)
            if status != 200:
                raise AcceptanceError(f"HTTP {status}")
            rows = get_path(payload, target["list_path"])
            if not isinstance(rows, list):
                raise AcceptanceError("list_path did not resolve to a list")
            row_dicts = [row for row in rows if isinstance(row, dict)]
            ids = [str(row.get(target["id_field"], "")) for row in row_dicts]
            missing_required = [
                field
                for row in row_dicts
                for field in target["required_fields"]
                if row.get(field) in (None, "")
            ]
            page_result: dict[str, Any] = {
                "page": page_number,
                "status": status,
                "content_type": content_type.split(";", 1)[0],
                "row_count": len(row_dicts),
                "ids": ids,
                "missing_required_fields": sorted(set(missing_required)),
                "samples": sanitize_rows(target, row_dicts),
            }
            if target.get("total_path"):
                page_result["reported_total"] = get_path(payload, target["total_path"])
                page_result["total_kind"] = target["total_kind"]
            pages.append(page_result)
            all_rows.extend(row_dicts)
        except (AcceptanceError, error.URLError, TimeoutError) as exc:
            errors.append(f"page {page_number}: {exc}")
            pages.append({"page": page_number, "error": str(exc)})

        if page_number == 1:
            time.sleep(1)

    page_one_ids = set(pages[0].get("ids", []))
    page_two_ids = set(pages[1].get("ids", []))
    distinct_pages = bool(page_one_ids and page_two_ids and page_one_ids.isdisjoint(page_two_ids))
    evidence = campus_evidence(target, all_rows)
    required_ok = all(not page.get("missing_required_fields") for page in pages if "error" not in page)
    passed = not errors and distinct_pages and evidence["passed"] and required_ok
    return {
        "key": target["key"],
        "company": target["company"],
        "endpoint": target["endpoint"],
        "method": target["method"],
        "body_encoding": target["body_encoding"],
        "minimal_request": True,
        "cookies_sent": False,
        "requests_made": sum(1 for page in pages if "status" in page),
        "request_budget_after_run": budget["already_spent"] + budget["planned"],
        "pages": pages,
        "pagination": {"page_ids_are_distinct": distinct_pages, "passed": distinct_pages},
        "campus_evidence": evidence,
        "adapter_transport_supported": target["adapter_transport_supported"],
        "adapter_note": target.get("adapter_note", ""),
        "errors": errors,
        "passed": passed,
    }


def run(config_path: Path, requester: Requester = request_json) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    results = [validate_target(target, requester) for target in config["targets"]]
    return {
        "cycle": config["cycle"],
        "scope": "read-only two-page API acceptance; not source admission",
        "source_admission_claimed": False,
        "database_writes": False,
        "raw_responses_persisted": False,
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
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Cycle 03 report: {args.output}")
    for result in report["results"]:
        print(f"{result['company']}: {'PASS' if result['passed'] else 'FAIL'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
