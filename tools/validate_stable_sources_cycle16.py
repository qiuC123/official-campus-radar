"""Read-only completeness acceptance for seven T3 Cycle 16 sources."""

from __future__ import annotations

import argparse
import copy
import json
import re
import time
from pathlib import Path
from typing import Any, Callable

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "tools" / "api-acceptance-cycle-16-seven-sources.json"
DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t3-api-acceptance-cycle-16-seven-sources.json"
USER_AGENT = "OfficialCampusRadar/0.1 (local low-frequency acceptance)"


class AcceptanceError(ValueError):
    pass


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


def get_path(document: Any, dotted_path: str) -> Any:
    values = get_values(document, dotted_path)
    if len(values) != 1:
        raise AcceptanceError(f"missing or ambiguous path: {dotted_path}")
    return values[0]


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


def parse_apple_hydration(html: str) -> dict[str, Any]:
    match = re.search(
        r"window\.__staticRouterHydrationData\s*=\s*JSON\.parse\((\".*?\")\);?</script>",
        html,
        re.DOTALL,
    )
    if not match:
        raise AcceptanceError("Apple hydration payload was not found")
    try:
        return json.loads(json.loads(match.group(1)))
    except (TypeError, json.JSONDecodeError) as exc:
        raise AcceptanceError("Apple hydration payload is invalid JSON") from exc


def parse_gac_toyota_jobs(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for row in soup.select("table.jobsTable tr:not(.title)"):
        cells = row.select("td")
        link = row.select_one("a[href*='/zpdetail/']")
        if len(cells) < 4 or link is None:
            continue
        href = str(link.get("href", "")).strip()
        jobs.append(
            {
                "id": href.rsplit("/", 1)[-1],
                "title": link.get_text(" ", strip=True),
                "location": cells[2].get_text(" ", strip=True),
                "published_on": cells[3].get_text(" ", strip=True),
                "href": href,
            }
        )
    return {
        "jobs": jobs,
        "total": len(jobs),
        "pager_link_count": len(soup.select("div.pager a[href]")),
    }


def request_page(
    session: requests.Session,
    target: dict[str, Any],
    request_values: dict[str, Any],
) -> tuple[int, str, Any]:
    headers = {"User-Agent": USER_AGENT, **target.get("headers", {})}
    kwargs: dict[str, Any] = {
        "headers": headers,
        "timeout": 30,
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
    if target.get("response_kind") == "apple_hydration":
        payload = parse_apple_hydration(response.text)
    elif target.get("response_kind") == "gac_toyota_html":
        payload = parse_gac_toyota_jobs(response.text)
    else:
        try:
            payload = response.json()
        except ValueError as exc:
            raise AcceptanceError("response is not JSON") from exc
    return response.status_code, response.headers.get("content-type", ""), payload


Requester = Callable[[dict[str, Any], dict[str, Any]], tuple[int, str, Any]]


def _text_values(row: dict[str, Any], paths: list[str]) -> list[str]:
    return [
        str(value).strip()
        for path in paths
        for value in get_values(row, path)
        if value not in (None, "") and str(value).strip()
    ]


def _matches_filter(row: dict[str, Any], rule: dict[str, Any] | None) -> bool:
    if not rule:
        return True
    values = {str(value) for value in get_values(row, rule["path"])}
    if "contains_any" in rule:
        return any(
            token in value
            for token in rule["contains_any"]
            for value in values
        )
    allowed = {str(value) for value in rule["allowed"]}
    return bool(values & allowed)


def _sample(row: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    result = {}
    for field in fields:
        values = get_values(row, field)
        result[field] = values[0] if len(values) == 1 else values
    return result


def validate_target(target: dict[str, Any], requester: Requester) -> dict[str, Any]:
    pagination = target["pagination"]
    all_ids: set[str] = set()
    accepted_ids: set[str] = set()
    samples: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    reported_total: int | None = None
    missing_fields: set[str] = set()
    scope_values: dict[str, set[str]] = {
        rule["path"]: set() for rule in target.get("scope_fields", [])
    }

    for index in range(pagination["max_pages"]):
        values = copy.deepcopy(target["request"])
        mode = pagination["mode"]
        if mode == "offset":
            cursor = pagination["start"] + index * pagination["page_size"]
        elif mode == "page_index":
            cursor = pagination["start"] + index
        else:
            cursor = 1
        if mode != "single":
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
        page_total: int | None = None
        if target.get("total_path"):
            try:
                page_total = int(get_path(payload, target["total_path"]))
            except (TypeError, ValueError) as exc:
                raise AcceptanceError("total_path is not numeric") from exc
            if page_total < 0 or (
                reported_total is not None and page_total != reported_total
            ):
                raise AcceptanceError("reported total changed during pagination")
            reported_total = page_total
        added = 0
        accepted = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_ids = _text_values(row, [target["id_path"]])
            row_id = row_ids[0] if row_ids else ""
            if row_id and row_id not in all_ids:
                all_ids.add(row_id)
                added += 1
            if not _matches_filter(row, target.get("row_filter")):
                continue
            accepted += 1
            if row_id:
                accepted_ids.add(row_id)
            titles = _text_values(row, [target["title_path"]])
            locations = _text_values(row, target["location_paths"])
            if not row_id:
                missing_fields.add(target["id_path"])
            if not titles:
                missing_fields.add(target["title_path"])
            if not locations:
                missing_fields.add("location")
            for rule in target.get("scope_fields", []):
                scope_values[rule["path"]].update(
                    str(value) for value in get_values(row, rule["path"])
                )
            if row_id and len(samples) < 5:
                samples.append(_sample(row, target["sample_fields"]))
        if (
            page_total is None
            and target.get("infer_total_from_short_page")
            and len(rows) < pagination["page_size"]
        ):
            reported_total = len(all_ids)
        pages.append(
            {
                "cursor": cursor,
                "status": status,
                "content_type": content_type.split(";", 1)[0],
                "row_count": len(rows),
                "accepted_row_count": accepted,
                "new_unique_ids": added,
            }
        )
        if (
            mode == "single"
            or (reported_total is not None and len(all_ids) >= reported_total)
            or len(rows) < pagination["page_size"]
        ):
            break
        time.sleep(0.5)

    scope_checks = []
    for rule in target.get("scope_fields", []):
        observed = scope_values[rule["path"]]
        allowed = {str(value) for value in rule["allowed"]}
        scope_checks.append(
            {
                "path": rule["path"],
                "raw_values": sorted(observed),
                "allowed": sorted(allowed),
                "passed": bool(observed) and observed <= allowed,
            }
        )
    scope_ok = all(check["passed"] for check in scope_checks)
    complete = reported_total is not None and len(all_ids) == reported_total
    passed = (
        complete
        and bool(accepted_ids)
        and not missing_fields
        and scope_ok
        and bool(target.get("official_link_evidence"))
        and bool(target.get("scope_evidence") or target.get("scope_fields"))
    )
    return {
        "key": target["key"],
        "company": target["company"],
        "official_page_url": target["official_page_url"],
        "official_link_evidence": target["official_link_evidence"],
        "endpoint": target["endpoint"],
        "minimal_request": True,
        "cookies_sent": False,
        "redirects_followed": False,
        "requests_made": len(pages),
        "reported_total": reported_total,
        "unique_ids": len(all_ids),
        "accepted_unique_ids": len(accepted_ids),
        "complete": complete,
        "scope_evidence": target.get("scope_evidence", "row fields"),
        "scope_checks": scope_checks,
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
            time.sleep(1)
    return {
        "cycle": config["cycle"],
        "scope": "read-only public source completeness acceptance; not source admission",
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
            f"({result.get('unique_ids', 0)}/{result.get('reported_total', '?')}; "
            f"accepted {result.get('accepted_unique_ids', 0)})"
        )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
