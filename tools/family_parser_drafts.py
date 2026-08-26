"""Offline-only parser harness for T3 recruitment-platform family drafts.

This module never opens a browser or performs network requests. It validates
saved, minimal fixtures against the selector/JSON mappings recorded for T3
Cycle 02. Passing here is evidence for a parser draft, not source admission.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup


class DraftParseError(ValueError):
    """Raised when a draft cannot extract required, stable position fields."""


def load_family_drafts(path: str | Path) -> dict[str, dict[str, object]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    drafts = payload.get("drafts")
    if not isinstance(drafts, dict) or not drafts:
        raise DraftParseError("family draft file must contain a non-empty drafts object")
    return drafts


def _text(node) -> str:
    return node.get_text(" ", strip=True) if node is not None else ""


def _html_value(row, rule: object) -> str:
    if not isinstance(rule, dict):
        return ""
    selector = str(rule.get("selector", "")).strip()
    if not selector:
        return ""
    node = row.select_one(selector)
    if node is None:
        return ""
    attribute = str(rule.get("attribute", "")).strip()
    raw_value = str(node.get(attribute, "")) if attribute else _text(node)
    pattern = str(rule.get("regex", "")).strip()
    if not pattern:
        return raw_value.strip()
    match = re.search(pattern, raw_value)
    return match.group(1).strip() if match else ""


def _parse_date(raw_value: str) -> date | None:
    match = re.search(r"\d{4}-\d{2}-\d{2}", raw_value)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(0))
    except ValueError:
        return None


def parse_html_positions(
    html: str, draft: dict[str, object]
) -> list[dict[str, object]]:
    transport = draft.get("transport")
    if transport not in {"direct_html", "rendered_dom_dev_only"}:
        raise DraftParseError("HTML parser requires an HTML or rendered-DOM draft")
    selector = str(draft.get("position_selector", "")).strip()
    fields = draft.get("fields")
    if not selector or not isinstance(fields, dict):
        raise DraftParseError("HTML draft requires position_selector and fields")

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(selector)
    if not rows:
        raise DraftParseError("position selector returned no rows")

    positions: list[dict[str, object]] = []
    base_url = str(draft.get("base_url", ""))
    for row_index, row in enumerate(rows, start=1):
        position_key = _html_value(row, fields.get("position_key"))
        title = _html_value(row, fields.get("title"))
        location = _html_value(row, fields.get("location"))
        if not position_key or not title or not location:
            raise DraftParseError(
                f"row {row_index} is missing stable key, title, or location"
            )
        application_href = _html_value(row, fields.get("application_url"))
        source_date_raw = _html_value(row, fields.get("source_date"))
        source_date = _parse_date(source_date_raw)
        positions.append(
            {
                "position_key": position_key,
                "title": title,
                "location": location,
                "source_date": source_date.isoformat() if source_date else None,
                "source_date_role": draft.get("source_date_role"),
                "application_url": (
                    urljoin(base_url, application_href)
                    if application_href
                    else None
                ),
                "raw_text": _text(row),
            }
        )
    return positions


def _json_path(payload: object, path: str) -> object:
    value = payload
    for part in path.split(".") if path else []:
        if not isinstance(value, dict) or part not in value:
            raise DraftParseError(f"JSON path not found: {path}")
        value = value[part]
    return value


def parse_json_positions(
    payload: object, draft: dict[str, object]
) -> tuple[list[dict[str, object]], int | None]:
    if draft.get("transport") != "json_api_candidate":
        raise DraftParseError("JSON parser requires a JSON API candidate draft")
    list_path = str(draft.get("list_path", "")).strip()
    field_map = draft.get("field_map")
    if not list_path or not isinstance(field_map, dict):
        raise DraftParseError("JSON draft requires list_path and field_map")
    rows = _json_path(payload, list_path)
    if not isinstance(rows, list) or not rows:
        raise DraftParseError("JSON list path returned no rows")

    positions: list[dict[str, object]] = []
    for row_index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise DraftParseError(f"JSON row {row_index} is not an object")

        def mapped(role: str) -> str:
            key = str(field_map.get(role, "")).strip()
            return str(row.get(key, "")).strip() if key else ""

        position_key = mapped("position_key")
        title = mapped("title")
        location = mapped("location")
        if not position_key or not title or not location:
            raise DraftParseError(
                f"JSON row {row_index} is missing stable key, title, or location"
            )
        source_date_raw = mapped("source_date")
        source_date = _parse_date(source_date_raw)
        application_url = mapped("application_url") or None
        positions.append(
            {
                "position_key": position_key,
                "title": title,
                "location": location,
                "source_date": source_date.isoformat() if source_date else None,
                "source_date_role": draft.get("source_date_role"),
                "application_url": application_url,
                "raw_text": json.dumps(row, ensure_ascii=False, sort_keys=True),
            }
        )

    total_path = str(draft.get("total_path", "")).strip()
    total_value = _json_path(payload, total_path) if total_path else None
    total = total_value if isinstance(total_value, int) else None
    return positions, total


def parse_fixture(
    fixture_path: str | Path, draft: dict[str, object]
) -> dict[str, object]:
    fixture = Path(fixture_path)
    if draft.get("transport") == "json_api_candidate":
        positions, total = parse_json_positions(
            json.loads(fixture.read_text(encoding="utf-8")), draft
        )
    else:
        positions = parse_html_positions(fixture.read_text(encoding="utf-8"), draft)
        total = None
    return {"position_count": len(positions), "total": total, "positions": positions}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--family", required=True)
    parser.add_argument("--fixture", required=True)
    arguments = parser.parse_args()

    drafts = load_family_drafts(arguments.config)
    try:
        draft = drafts[arguments.family]
    except KeyError as error:
        raise DraftParseError(f"unknown family draft: {arguments.family}") from error
    print(json.dumps(parse_fixture(arguments.fixture, draft), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
