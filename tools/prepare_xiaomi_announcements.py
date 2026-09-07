"""Project frozen official Xiaomi notices; offline only, no admission or ATS writes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/xiaomi-official-announcement-evidence-20260907.json"
OUTPUT = ROOT / "work/xiaomi-official-announcement-candidates-20260907.json"
NOTICE_BASE = "https://hr.xiaomi.com/website/campus-notice.html#id="


def notice_sections(body):
    """Keep each heading's text separate; never borrow a cohort from another notice."""
    soup = BeautifulSoup(body, "html.parser")
    for node in soup.select("script, style, template"):
        node.decompose()
    sections = []
    current = {"heading": "", "text": []}
    for node in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        if node.find_parent(["p", "li"]):
            continue
        text = node.get_text("", strip=True)
        if not text:
            continue
        if node.name.startswith("h"):
            if current["text"] or current["heading"]:
                sections.append(current)
            current = {"heading": text, "text": []}
        else:
            current["text"].append(text)
    if current["text"] or current["heading"]:
        sections.append(current)
    return sections


def validated_rows(payload):
    if payload.get("code") != 200 or payload.get("success") is not True:
        raise ValueError("unsuccessful_official_response")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("missing_official_rows")
    ids = [row.get("id") for row in rows]
    if any(type(value) is not int or value < 1 for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("ambiguous_official_identity")
    if any(row.get("status") != 1 or row.get("isDel") is not False for row in rows):
        raise ValueError("inactive_official_row_requires_review")
    return rows


def build_candidates(evidence):
    requests = evidence["requests"]
    if not requests or any(row["http_status"] != 200 for row in requests):
        raise ValueError("incomplete_http_evidence")
    # This is a frozen source-specific rendering contract, not a general JS interpreter.
    rendering = evidence["rendering_evidence"]
    if ("campus-notice.html#id=${item.id}" not in rendering["campus_news"]
            or "String(d.id) === String(id)" not in rendering["notice_detail"]
            or "getElementById('noticeBody').innerHTML = data.body" not in rendering["notice_detail"]):
        raise ValueError("unverified_notice_rendering_identity")
    notices = []
    for row in validated_rows(evidence["announcements"]):
        if not isinstance(row.get("body"), str) or not row["body"].strip():
            raise ValueError("missing_notice_original")
        sections = notice_sections(row["body"])
        audience = [section for section in sections
                    if "招聘对象" in section["heading"] or "招募对象" in section["heading"]]
        window = [section for section in sections
                  if "网申时间" in section["heading"] or "项目开放时间" in section["heading"]]
        notices.append({
            "notice_id": row["id"], "title": row["title"], "tag": row["tag"],
            "official_url": NOTICE_BASE + str(row["id"]),
            "legacy_api_link_hint": row["linkUrl"],
            "body_sha256": hashlib.sha256(row["body"].encode("utf-8")).hexdigest(),
            "sections": sections, "audience_evidence": audience, "application_window_evidence": window,
            "official_original_observed": True,
            "ats_subject_id": None, "binding_verified": False,
            "current_application_availability_verified": False,
        })
    programs = []
    for row in validated_rows(evidence["programs"]):
        programs.append({
            "official_program_id": row["id"], "title": row["title"],
            "target_audience_text": row["targetAudience"], "buttons": row["buttons"],
            "ats_subject_id": None, "notice_binding_verified": False,
        })
    return {
        "schema_version": 1, "evidence_kind": "offline_official_notice_candidates",
        "company": "小米", "network_requests": 0, "database_writes": 0,
        "notices": notices, "program_navigation": programs,
        "notice_count": len(notices), "official_navigation_program_count": len(programs),
        "production_admitted": False,
        "gaps": ["notice_to_ats_project_binding", "complete_pagination",
                 "exhaustive_project_coverage_including_overseas", "independent_application_availability"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write the offline candidate JSON")
    args = parser.parse_args(argv)
    raw = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    result = build_candidates(json.loads(raw))
    result["source"] = {"file": SOURCE.relative_to(ROOT).as_posix(),
                        "sha256": hashlib.sha256(raw).hexdigest(), "hash_normalization": "utf8_lf_line_endings"}
    if args.write:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"notice_count": result["notice_count"],
                      "official_navigation_program_count": result["official_navigation_program_count"],
                      "production_admitted": False, "written": args.write}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
