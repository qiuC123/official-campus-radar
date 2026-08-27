"""Bounded direct-HTML validation for Phase 02 T3 Cycle 04.

Page-one captures are written outside the repository for offline inspection.
The committed report contains only hashes, small position samples, form names
and short pagination snippets. The tool never follows redirects or retries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "tools" / "targets-phase-02-t3-cycle-04.json"
DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t3-cycle-04-page1.json"
DEFAULT_FOLLOWUP_CONFIG = ROOT / "tools" / "targets-phase-02-t3-cycle-04-followups.json"
DEFAULT_FOLLOWUP_OUTPUT = ROOT / "work" / "phase-02-t3-cycle-04-followups.json"
DEFAULT_CAPTURE_DIR = Path(tempfile.gettempdir()) / "official-campus-radar-cycle04"
MAX_BODY_BYTES = 2 * 1024 * 1024
HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "User-Agent": "OfficialCampusRadar/0.1 (local low-frequency acceptance)",
}


class Cycle04Error(ValueError):
    pass


def load_targets(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    targets = payload.get("targets")
    if not isinstance(targets, list) or len(targets) != 6:
        raise Cycle04Error("Cycle 04 must contain exactly six frozen targets")
    ids = [str(target.get("id", "")) for target in targets]
    if any(not target_id for target_id in ids) or len(ids) != len(set(ids)):
        raise Cycle04Error("Cycle 04 target IDs must be non-empty and unique")
    for target in targets:
        budget = target.get("request_budget")
        if not isinstance(budget, dict) or budget.get("page1_planned") != 1:
            raise Cycle04Error("every target must plan exactly one page-one request")
        if budget["page1_planned"] + budget.get("page2_planned", 0) > budget["maximum"]:
            raise Cycle04Error("target request budget exceeded")
    return payload


def load_followups(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    followups = payload.get("followups")
    if not isinstance(followups, list) or not followups:
        raise Cycle04Error("Cycle 04 followups must be a non-empty list")
    for item in followups:
        budget = item.get("request_budget", {})
        if budget.get("prior_requests") + budget.get("planned") > budget.get("maximum"):
            raise Cycle04Error("followup request budget exceeded")
        if budget.get("planned") != 1:
            raise Cycle04Error("each followup must plan exactly one request")
    return payload


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _position_samples(soup: BeautifulSoup, family: str) -> list[dict[str, str]]:
    if family == "beisen_zhiye":
        selector = "table.jobsTable tr:not(.title)"
        link_pattern = re.compile(r"/zpdetail/(\d+)")
    elif family == "wintalent_classic":
        selector = "table.search_result tr"
        link_pattern = re.compile(r"[?&]postIdEnc=([^&]+)")
    else:
        raise Cycle04Error(f"unsupported family: {family}")

    samples: list[dict[str, str]] = []
    for row in soup.select(selector):
        link = row.select_one("a[href]")
        cells = row.select("td")
        if link is None or not cells:
            continue
        href = str(link.get("href", ""))
        identity = link_pattern.search(href)
        if identity is None:
            continue
        cell_text = [_clean_text(cell.get_text(" ", strip=True)) for cell in cells]
        nonempty = [value for value in cell_text if value]
        location_index = 2 if family == "beisen_zhiye" else 3
        samples.append(
            {
                "position_key": identity.group(1),
                "title": _clean_text(link.get_text(" ", strip=True)),
                "location_candidate": (
                    cell_text[location_index]
                    if len(cell_text) > location_index
                    else ""
                ),
                "row_text": " | ".join(nonempty)[:500],
                "href": href[:500],
            }
        )
        if len(samples) == 5:
            break
    return samples


def _forms(soup: BeautifulSoup) -> list[dict[str, Any]]:
    result = []
    for form in soup.select("form")[:10]:
        names = []
        for field in form.select("input[name], select[name], textarea[name]"):
            name = str(field.get("name", "")).strip()
            if name and name not in names:
                names.append(name)
        result.append(
            {
                "id": str(form.get("id", ""))[:100],
                "method": str(form.get("method", "GET")).upper()[:10],
                "action": str(form.get("action", ""))[:500],
                "field_names": names[:50],
            }
        )
    return result


def _pagination_snippets(html: str) -> list[str]:
    patterns = [
        r"changePage\s*\([^)]{0,500}\)",
        r"(?:goToPage|gotoPage|pageIndex|currentPage|pageSize)[^\r\n<]{0,500}",
    ]
    snippets: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE):
            snippet = _clean_text(match.group(0))[:600]
            if snippet and snippet not in snippets:
                snippets.append(snippet)
            if len(snippets) == 12:
                return snippets
    return snippets


def inspect_html(html: str, target: dict[str, Any]) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    page_text = _clean_text(soup.get_text(" ", strip=True))
    samples = _position_samples(soup, target["expected_family"])
    campus_terms = [
        term for term in ("校园招聘", "校招", "应届", "实习") if term in page_text
    ]
    return {
        "title": _clean_text(soup.title.get_text(" ", strip=True))[:300]
        if soup.title
        else "",
        "position_sample_count": len(samples),
        "position_samples": samples,
        "campus_terms": campus_terms,
        "forms": _forms(soup),
        "pagination_snippets": _pagination_snippets(html),
        "family_marker_present": (
            "zhiye.com" in html.lower()
            if target["expected_family"] == "beisen_zhiye"
            else "/wt/" in html.lower() or "wintalent" in html.lower()
        ),
    }


def inspect_javascript(javascript: str) -> dict[str, Any]:
    keywords = ("api", "job", "position", "campus", "school", "recruit")
    values: list[str] = []
    for match in re.finditer(r"(['\"])(?P<value>[^'\"\r\n]{4,500})\1", javascript):
        value = match.group("value")
        lowered = value.lower()
        if (
            len(value) <= 200
            and any(keyword in lowered for keyword in keywords)
            and value not in values
        ):
            values.append(value)
        if len(values) == 100:
            break
    return {"candidate_string_count": len(values), "candidate_strings": values}


def fetch_once(target: dict[str, Any]) -> tuple[int, dict[str, str], bytes]:
    session = requests.Session()
    session.trust_env = False
    session.cookies.clear()
    try:
        response = session.get(
            target["url"],
            headers=HEADERS,
            timeout=20,
            allow_redirects=False,
        )
        body = response.content
        if len(body) > MAX_BODY_BYTES:
            raise Cycle04Error("response exceeds 2 MiB capture limit")
        return response.status_code, dict(response.headers), body
    finally:
        session.cookies.clear()
        session.close()


def run_page_one(
    config_path: Path,
    output_path: Path,
    capture_dir: Path,
    requester=fetch_once,
    delay_seconds: float = 3,
) -> dict[str, Any]:
    config = load_targets(config_path)
    capture_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for index, target in enumerate(config["targets"]):
        result: dict[str, Any] = {
            "id": target["id"],
            "company": target["company"],
            "expected_family": target["expected_family"],
            "url": target["url"],
            "official_evidence_url": target["official_evidence_url"],
            "requests_made": 1,
            "cookies_sent": False,
            "redirects_followed": False,
        }
        try:
            status, headers, body = requester(target)
            result.update(
                {
                    "status": status,
                    "content_type": headers.get("Content-Type", "").split(";", 1)[0],
                    "location": headers.get("Location", "")[:500],
                    "body_bytes": len(body),
                    "body_sha256": hashlib.sha256(body).hexdigest(),
                }
            )
            if status == 200:
                html = body.decode("utf-8", errors="replace")
                capture_path = capture_dir / f"{target['id']}.html"
                capture_path.write_text(html, encoding="utf-8")
                result["inspection"] = inspect_html(html, target)
                result["raw_capture_path"] = str(capture_path)
            else:
                result["error"] = f"HTTP {status}; no retry in this cycle"
        except (Cycle04Error, requests.RequestException) as exc:
            result["error"] = str(exc)
        results.append(result)
        if index + 1 < len(config["targets"]):
            time.sleep(delay_seconds)

    report = {
        "cycle": config["cycle"],
        "stage": "page-one direct HTML capture",
        "source_admission_claimed": False,
        "database_writes": False,
        "requests_made": len(results),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def run_followups(
    config_path: Path,
    output_path: Path,
    capture_dir: Path,
    requester=fetch_once,
    delay_seconds: float = 3,
) -> dict[str, Any]:
    config = load_followups(config_path)
    capture_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for index, target in enumerate(config["followups"]):
        result: dict[str, Any] = {
            "id": target["id"],
            "company": target["company"],
            "kind": target["kind"],
            "url": target["url"],
            "reason": target["reason"],
            "requests_made": 1,
            "cookies_sent": False,
            "redirects_followed": False,
            "request_budget_after_run": (
                target["request_budget"]["prior_requests"]
                + target["request_budget"]["planned"]
            ),
        }
        try:
            status, headers, body = requester(target)
            result.update(
                {
                    "status": status,
                    "content_type": headers.get("Content-Type", "").split(";", 1)[0],
                    "location": headers.get("Location", "")[:500],
                    "body_bytes": len(body),
                    "body_sha256": hashlib.sha256(body).hexdigest(),
                }
            )
            if status == 200:
                text = body.decode("utf-8", errors="replace")
                suffix = ".js" if target["kind"] == "javascript" else ".html"
                capture_path = capture_dir / f"{target['id']}-followup{suffix}"
                capture_path.write_text(text, encoding="utf-8")
                if target["kind"] == "javascript":
                    result["inspection"] = inspect_javascript(text)
                else:
                    result["inspection"] = inspect_html(text, target)
                result["raw_capture_path"] = str(capture_path)
            else:
                result["error"] = f"HTTP {status}; no retry in this cycle"
        except (Cycle04Error, requests.RequestException) as exc:
            result["error"] = str(exc)
        results.append(result)
        if index + 1 < len(config["followups"]):
            time.sleep(delay_seconds)
    report = {
        "cycle": config["cycle"],
        "stage": "bounded architecture followups",
        "source_admission_claimed": False,
        "database_writes": False,
        "requests_made": len(results),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("page1", "followup"), default="page1")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--capture-dir", type=Path, default=DEFAULT_CAPTURE_DIR)
    args = parser.parse_args()
    if args.stage == "followup":
        config_path = args.config or DEFAULT_FOLLOWUP_CONFIG
        output_path = args.output or DEFAULT_FOLLOWUP_OUTPUT
        report = run_followups(config_path, output_path, args.capture_dir)
    else:
        config_path = args.config or DEFAULT_CONFIG
        output_path = args.output or DEFAULT_OUTPUT
        report = run_page_one(config_path, output_path, args.capture_dir)
    print(f"Cycle 04 {args.stage} report: {output_path}")
    for result in report["results"]:
        inspection = result.get("inspection", {})
        print(
            f"{result['company']}: HTTP {result.get('status', 'ERR')}, "
            f"samples={inspection.get('position_sample_count', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
