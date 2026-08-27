"""Bounded public-API completeness acceptance for T3 Cycle 11."""

from __future__ import annotations

import argparse
import copy
import json
import time
from pathlib import Path
from typing import Any, Callable

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "tools" / "api-acceptance-cycle-11-public-family.json"
DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t3-api-acceptance-cycle-11-public-family.json"
USER_AGENT = "OfficialCampusRadar/0.1 (local low-frequency acceptance)"


class AcceptanceError(ValueError):
    pass


def get_path(document: Any, dotted_path: str) -> Any:
    current = document
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise AcceptanceError(f"missing path: {dotted_path}")
        current = current[part]
    return current


def get_values(document: Any, dotted_path: str) -> list[Any]:
    values = [document]
    for raw_part in dotted_path.split("."):
        is_array = raw_part.endswith("[]")
        part = raw_part[:-2] if is_array else raw_part
        next_values: list[Any] = []
        for value in values:
            if part:
                if not isinstance(value, dict) or part not in value:
                    continue
                value = value[part]
            if is_array:
                if isinstance(value, list):
                    next_values.extend(value)
            else:
                next_values.append(value)
        values = next_values
    return values


def set_path(document: dict[str, Any], dotted_path: str, value: Any) -> None:
    current = document
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value


def request_page(
    session: requests.Session,
    target: dict[str, Any],
    request_values: dict[str, Any],
) -> tuple[int, str, Any]:
    headers = {"User-Agent": USER_AGENT, **target.get("headers", {})}
    kwargs: dict[str, Any] = {
        "headers": headers,
        "timeout": 20,
        "allow_redirects": False,
    }
    encoding = target["body_encoding"]
    if encoding == "query":
        kwargs["params"] = request_values
    elif encoding == "form":
        kwargs["data"] = request_values
    else:
        kwargs["json"] = request_values
    session.cookies.clear()
    response = session.request(target["method"], target["endpoint"], **kwargs)
    try:
        payload = response.json()
    except ValueError as exc:
        raise AcceptanceError("response is not JSON") from exc
    return response.status_code, response.headers.get("content-type", ""), payload


Requester = Callable[[dict[str, Any], dict[str, Any]], tuple[int, str, Any]]


def validate_target(target: dict[str, Any], requester: Requester) -> dict[str, Any]:
    pagination = target["pagination"]
    seen: set[str] = set()
    samples: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    reported_total: int | None = None
    missing_fields: set[str] = set()
    scope_values: set[str] = set()

    for index in range(pagination["max_pages"]):
        values = copy.deepcopy(target["request"])
        cursor = (
            pagination["start"] + index * pagination["page_size"]
            if pagination["mode"] == "offset"
            else pagination["start"] + index
        )
        set_path(values, pagination["page_param"], cursor)
        set_path(values, pagination["size_param"], pagination["page_size"])
        status, content_type, payload = requester(target, values)
        if status != 200:
            raise AcceptanceError(f"HTTP {status}")
        success = target.get("success")
        if success and get_path(payload, success["path"]) != success["expect"]:
            raise AcceptanceError("business success check failed")
        rows = get_path(payload, target["list_path"])
        if not isinstance(rows, list):
            raise AcceptanceError("list_path did not resolve to a list")
        raw_total = get_path(payload, target["total_path"])
        try:
            page_total = int(raw_total)
        except (TypeError, ValueError) as exc:
            raise AcceptanceError("total_path is not numeric") from exc
        if page_total < 0 or (reported_total is not None and page_total != reported_total):
            raise AcceptanceError("reported total changed during pagination")
        reported_total = page_total
        added = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_id = str(row.get(target["id_field"], "")).strip()
            title = str(row.get(target["title_field"], "")).strip()
            locations = [
                str(value).strip()
                for path in target["location_paths"]
                for value in get_values(row, path)
                if value not in (None, "") and str(value).strip()
            ]
            if not row_id:
                missing_fields.add(target["id_field"])
            if not title:
                missing_fields.add(target["title_field"])
            if not locations:
                missing_fields.add("location")
            scope = target.get("scope")
            if scope:
                scope_values.add(str(row.get(scope["field"], "")))
            if row_id and row_id not in seen:
                seen.add(row_id)
                added += 1
                if len(samples) < 5:
                    samples.append(
                        {field: row.get(field) for field in target["sample_fields"]}
                    )
        pages.append(
            {
                "cursor": cursor,
                "status": status,
                "content_type": content_type.split(";", 1)[0],
                "row_count": len(rows),
                "new_unique_ids": added,
            }
        )
        if len(seen) >= reported_total or len(rows) < pagination["page_size"]:
            break
        time.sleep(1)

    scope = target.get("scope")
    allowed = set(scope["allowed"]) if scope else set()
    scope_ok = not scope or (bool(scope_values) and scope_values <= allowed)
    complete = reported_total is not None and len(seen) == reported_total
    passed = complete and not missing_fields and scope_ok
    return {
        "key": target["key"],
        "company": target["company"],
        "official_page_url": target["official_page_url"],
        "endpoint": target["endpoint"],
        "minimal_request": True,
        "cookies_sent": False,
        "redirects_followed": False,
        "requests_made": len(pages),
        "reported_total": reported_total,
        "unique_ids": len(seen),
        "complete": complete,
        "scope_raw_values": sorted(scope_values),
        "scope_ok": scope_ok,
        "missing_required_fields": sorted(missing_fields),
        "pages": pages,
        "samples": samples,
        "passed": passed,
    }


def run(config_path: Path, requester: Requester | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    session = requests.Session()
    session.trust_env = False

    def live_request(target: dict[str, Any], values: dict[str, Any]):
        return request_page(session, target, values)

    effective_requester = requester or live_request
    results = []
    for index, target in enumerate(config["targets"]):
        try:
            result = validate_target(target, effective_requester)
        except (AcceptanceError, requests.RequestException) as exc:
            result = {
                "key": target["key"],
                "company": target["company"],
                "requests_made": 0,
                "errors": [str(exc)],
                "passed": False,
            }
        results.append(result)
        if requester is None and index + 1 < len(config["targets"]):
            time.sleep(2)
    return {
        "cycle": config["cycle"],
        "scope": "read-only public API completeness acceptance; not source admission",
        "source_admission_claimed": False,
        "database_writes": False,
        "raw_response_persisted": False,
        "results": results,
        "stable_count_added": sum(result["passed"] for result in results),
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
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{report['cycle']} report: {args.output}")
    for result in report["results"]:
        print(
            f"{result['company']}: {'PASS' if result['passed'] else 'FAIL'} "
            f"({result.get('unique_ids', 0)}/{result.get('reported_total', '?')})"
        )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
