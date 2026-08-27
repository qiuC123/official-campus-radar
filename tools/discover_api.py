"""Development-only recruitment API discovery helpers and CLI."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, TextIO
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


USER_AGENT = "OfficialCampusRadar/0.1 (local low-frequency collector)"
MAX_JSON_BODY_BYTES = 2 * 1024 * 1024
MAX_REPLAYS_PER_ENDPOINT = 6
REPLAY_LADDER_REQUESTS = 5
REDACTED_VALUE = "[REDACTED]"

TITLE_KEY = re.compile(r"title|name|job|post|position", re.IGNORECASE)
LOCATION_KEY = re.compile(
    r"city|location|(?:^|[._])locnames?$|area|place|region",
    re.IGNORECASE,
)
TIME_KEY = re.compile(r"date|time|update|publish", re.IGNORECASE)
TOTAL_KEY = re.compile(r"total|count", re.IGNORECASE)
SUCCESS_KEY = re.compile(r"code|status|ret", re.IGNORECASE)
SIGNATURE_HEADER = re.compile(
    r"sign|token|payload|nonce|trace|w-",
    re.IGNORECASE,
)
CREDENTIAL_HEADER_NAMES = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "x-api-key",
    }
)
DISCRIMINATOR_KEY = re.compile(
    r"kind|category|campus|graduate|school|workyears?|experience|intern|recruit|attr|type",
    re.IGNORECASE,
)
CAMPUS_FILTER = re.compile(
    r"campus|school|graduate|intern|校招|校园|应届|实习",
    re.IGNORECASE,
)
EPHEMERAL_REQUEST_KEY = re.compile(
    r"^(?:_|t|ts|timestamp|cachebuster)$",
    re.IGNORECASE,
)

INTERACTION_GUARD_SCRIPT = r"""
(() => {
  const report = (kind) => {
    try { window.__officialCampusRadarViolation(kind); } catch (_) {}
  };
  HTMLFormElement.prototype.submit = function () {
    report('form.submit');
  };
  HTMLFormElement.prototype.requestSubmit = function () {
    report('form.requestSubmit');
  };
  window.open = function () {
    report('window.open');
    return null;
  };
  window.addEventListener('submit', (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
    report('form submit event');
  }, true);
  window.addEventListener('click', (event) => {
    const source = event.target instanceof Element ? event.target : null;
    const link = source ? source.closest('a,area') : null;
    if (!link) return;
    const base = document.querySelector('base[target]');
    const target = (link.getAttribute('target') ||
      (base ? base.getAttribute('target') : '') || '').toLowerCase();
    if (target && !['_self', '_parent', '_top'].includes(target)) {
      event.preventDefault();
      event.stopImmediatePropagation();
      report('inherited/new-page target');
    }
  }, true);
})();
"""


@dataclass(frozen=True)
class CandidateArray:
    path: str
    rows: tuple[dict[str, object], ...]
    score: int


@dataclass(frozen=True)
class ReplayHeaderProfile:
    name: str
    headers: dict[str, str]


@dataclass(frozen=True)
class TargetSpec:
    url: str
    wait_seconds: float = 8.0
    scroll: bool = False
    click_selector: str | None = None
    target_id: str | None = None
    company: str | None = None
    company_type: str | None = None
    official_evidence_url: str | None = None


class DiscoveryError(RuntimeError):
    """An expected, actionable discovery-tool failure."""


def _join_path(parent: str, key: str) -> str:
    return f"{parent}.{key}" if parent else key


def _candidate_score(keys: set[str], row_count: int) -> int:
    title_count = sum(
        bool(TITLE_KEY.search(key))
        and not bool(LOCATION_KEY.search(key) or TIME_KEY.search(key))
        for key in keys
    )
    location_count = sum(bool(LOCATION_KEY.search(key)) for key in keys)
    time_count = sum(bool(TIME_KEY.search(key)) for key in keys)
    identity_count = sum(
        bool(re.search(r"(^|_)(id|key)$|(?:job|post|position)id$", key, re.I))
        for key in keys
    )
    return (
        title_count * 5
        + location_count * 3
        + time_count * 2
        + identity_count * 2
        + min(row_count, 5)
    )


def find_candidate_arrays(payload: object) -> list[CandidateArray]:
    """Return object-array paths that have title and location/time key signals."""

    candidates: list[CandidateArray] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, _join_path(path, str(key)))
            return
        if not isinstance(value, list):
            return
        if value and all(isinstance(item, dict) for item in value):
            rows = tuple(value)
            keys = {path for row in rows for path in _iter_leaf_paths(row)}
            title_keys = {
                key
                for key in keys
                if TITLE_KEY.search(key)
                and not (LOCATION_KEY.search(key) or TIME_KEY.search(key))
            }
            context_keys = {
                key
                for key in keys
                if LOCATION_KEY.search(key) or TIME_KEY.search(key)
            }
            if title_keys and context_keys and title_keys.isdisjoint(context_keys):
                candidates.append(
                    CandidateArray(
                        path=path,
                        rows=rows,
                        score=_candidate_score(keys, len(rows)),
                    )
                )
        for index, child in enumerate(value):
            visit(child, f"{path}[{index}]")

    visit(payload, "")
    return sorted(candidates, key=lambda candidate: (-candidate.score, candidate.path))


def _iter_integer_fields(value: object, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = _join_path(path, str(key))
            if (
                TOTAL_KEY.search(str(key))
                and isinstance(child, int)
                and not isinstance(child, bool)
            ):
                yield child_path
            yield from _iter_integer_fields(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_integer_fields(child, f"{path}[{index}]")


def _path_parts(path: str) -> list[str]:
    return [part for part in re.split(r"\.|\[\d+\]", path) if part]


def infer_total_path(payload: object, list_path: str) -> str | None:
    """Find the nearest integer total/count field to a candidate list."""

    list_parent = _path_parts(list_path)[:-1]
    ranked: list[tuple[int, int, str]] = []
    for path in _iter_integer_fields(payload):
        # Values inside arrays are commonly facet/category counts or row-level
        # counters. They cannot safely describe the candidate job list total.
        if re.search(r"\[\d+\]", path):
            continue
        parts = _path_parts(path)
        common = 0
        for left, right in zip(list_parent, parts[:-1]):
            if left != right:
                break
            common += 1
        same_parent = int(parts[:-1] == list_parent)
        ranked.append((same_parent, common, path))
    if not ranked:
        return None
    return max(ranked, key=lambda item: (item[0], item[1], -len(item[2])))[2]


def infer_success(payload: object) -> dict[str, object] | None:
    """Return an allowed top-level business success marker, if present."""

    if not isinstance(payload, dict):
        return None
    for key, value in payload.items():
        if isinstance(value, bool) or not SUCCESS_KEY.search(str(key)):
            continue
        if str(value).strip().lower() in {"200", "201", "0", "success"}:
            return {"path": str(key), "expect": value}
    return None


def _pagination_role(key: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    if not normalized:
        return None
    if normalized in {"size", "limit", "pagesize", "pagelimit"}:
        return "size"
    if normalized.endswith(("pagesize", "pagelimit")):
        return "size"
    if normalized in {"offset", "pageoffset"} or normalized.endswith(
        "pageoffset"
    ):
        return "offset"
    if normalized in {"page", "index", "pageindex", "pageno", "pagenum"}:
        return "page"
    if normalized.endswith(("pageindex", "pageno", "pagenum")):
        return "page"
    return None


def infer_pagination_parameters(
    request_body: object | None,
    request_url: str | None,
) -> dict[str, object]:
    """Infer pagination fields from a JSON body and/or URL query."""

    inferred: dict[str, object] = {}

    def visit(value: object, path: str = "") -> None:
        if not isinstance(value, dict):
            return
        for key, child in value.items():
            child_path = _join_path(path, str(key))
            if _pagination_role(str(key)) is not None and not isinstance(
                child, (dict, list)
            ):
                inferred[child_path] = child
            visit(child, child_path)

    visit(request_body)
    if request_url:
        for key, value in parse_qsl(urlsplit(request_url).query, keep_blank_values=True):
            if _pagination_role(key) is not None:
                inferred.setdefault(key, value)
    return inferred


def _iter_leaf_paths(value: object, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = _join_path(path, str(key))
            if isinstance(child, dict):
                yield from _iter_leaf_paths(child, child_path)
            else:
                yield child_path


def _ordered_keys(rows: list[dict[str, object]] | tuple[dict[str, object], ...]):
    seen: set[str] = set()
    for row in rows:
        for path in _iter_leaf_paths(row):
            if path not in seen:
                seen.add(path)
                yield path


def _row_path_value(row: dict[str, object], path: str) -> object:
    current: object = row
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _field_score(key: str, role: str) -> int:
    leaf_key = key.rsplit(".", 1)[-1]
    normalized = re.sub(r"[^a-z0-9]", "", leaf_key.lower())
    exact: dict[str, tuple[str, ...]] = {
        "title": (
            "jobadname",
            "jobtitle",
            "recruitpostname",
            "positiontitle",
            "positionname",
            "postname",
            "title",
            "jobname",
        ),
        "location": (
            "locnames",
            "cityname",
            "locationname",
            "worklocation",
            "city",
            "location",
            "area",
            "place",
            "region",
        ),
        "updated_at": (
            "changedate",
            "postdate",
            "publishdate",
            "lastupdatetime",
            "updatedat",
            "updatetime",
            "publishtime",
            "publishat",
        ),
        "raw_text": ("responsibility", "description", "jobdescription", "content"),
        "application_url": ("posturl", "joburl", "applyurl", "applicationurl", "url"),
        "is_valid": ("isvalid", "valid", "status"),
    }
    choices = exact[role]
    if normalized in choices:
        return 200 - choices.index(normalized)
    patterns = {
        "title": TITLE_KEY,
        "location": LOCATION_KEY,
        "updated_at": TIME_KEY,
        "raw_text": re.compile(r"responsib|description|content|detail", re.I),
        "application_url": re.compile(r"url|link", re.I),
        "is_valid": re.compile(r"valid|active|status", re.I),
    }
    return 50 if patterns[role].search(leaf_key) else 0


def _identity_score(key: str, values: list[object]) -> int:
    if not values or any(value in (None, "") for value in values):
        return 0
    text_values = [str(value).strip() for value in values]
    if len(set(text_values)) != len(text_values):
        return 0
    shaped = all(
        re.fullmatch(r"\d{8,}", value)
        or re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            value,
            re.I,
        )
        for value in text_values
    )
    leaf_key = key.rsplit(".", 1)[-1]
    normalized = re.sub(r"[^a-z0-9]", "", leaf_key.lower())
    key_score = 0
    if normalized in {"jobadid", "jobid", "postid", "positionid"}:
        key_score = 400
    elif normalized in {"id", "jobkey", "postkey"}:
        key_score = 100
    elif normalized.endswith(("id", "key", "code")):
        key_score = 50
    return (200 if shaped else 0) + key_score


def infer_field_map(
    rows: list[dict[str, object]] | tuple[dict[str, object], ...],
) -> dict[str, str]:
    """Infer adapter field-map candidates from observed row keys and values."""

    if not rows:
        return {}
    keys = list(_ordered_keys(rows))
    result: dict[str, str] = {}
    identity_ranked = sorted(
        (
            (_identity_score(key, [row.get(key) for row in rows]), key)
            for key in keys
        ),
        key=lambda item: (-item[0], keys.index(item[1])),
    )
    if identity_ranked and identity_ranked[0][0] > 0:
        result["position_key"] = identity_ranked[0][1]
    for role in (
        "title",
        "location",
        "raw_text",
        "application_url",
        "updated_at",
        "is_valid",
    ):
        ranked = sorted(
            (
                (
                    _field_score(key, role)
                    if role != "title"
                    or any(
                        isinstance(_row_path_value(row, key), str)
                        and not re.fullmatch(
                            r"\s*(?:\d+|[0-9a-f-]{32,})\s*",
                            _row_path_value(row, key),
                            re.I,
                        )
                        for row in rows
                    )
                    else 0,
                    key,
                )
                for key in keys
            ),
            key=lambda item: (-item[0], keys.index(item[1])),
        )
        if ranked and ranked[0][0] > 0:
            result[role] = ranked[0][1]
    return result


def _credential_header_name(key: object) -> str | None:
    normalized = str(key).strip().casefold()
    return normalized if normalized in CREDENTIAL_HEADER_NAMES else None


def redact_request_headers(
    request_headers: dict[object, object],
) -> dict[str, object]:
    """Redact captured credential-header values before retaining a candidate."""

    return {
        str(key): (
            REDACTED_VALUE
            if _credential_header_name(key)
            else copy.deepcopy(value)
        )
        for key, value in request_headers.items()
    }


def build_replay_header_profiles(
    captured_headers: dict[str, str],
) -> list[ReplayHeaderProfile]:
    """Build the fixed five-step replay ladder; never exceed six requests."""

    full = {
        str(key).strip().lower(): str(value)
        for key, value in captured_headers.items()
        if str(key).strip()
        and not str(key).startswith(":")
        and not _credential_header_name(key)
    }
    without_signature = {
        key: value for key, value in full.items() if not SIGNATURE_HEADER.search(key)
    }
    without_cookie = {key: value for key, value in full.items() if key != "cookie"}
    without_both = {
        key: value
        for key, value in full.items()
        if key != "cookie" and not SIGNATURE_HEADER.search(key)
    }
    minimal = {
        "accept": full.get("accept", "application/json"),
        "content-type": full.get("content-type", "application/json"),
        "user-agent": USER_AGENT,
    }
    return [
        ReplayHeaderProfile("完整头 + Cookie（基线）", full),
        ReplayHeaderProfile("去掉疑似签名头", without_signature),
        ReplayHeaderProfile("去掉 Cookie", without_cookie),
        ReplayHeaderProfile("同时去掉两者", without_both),
        ReplayHeaderProfile("最简合规头", minimal),
    ]


def select_sample_fields(
    row: dict[str, object],
    field_map: dict[str, str],
) -> dict[str, object]:
    """Keep mapped values and raw recruitment-type discriminator fields."""

    sample_roles = {
        "position_key",
        "title",
        "location",
        "updated_at",
        "application_url",
        "is_valid",
    }
    mapped_paths = {
        path
        for role, path in field_map.items()
        if role in sample_roles
    }
    discriminator_paths = {
        path
        for path in _iter_leaf_paths(row)
        if DISCRIMINATOR_KEY.search(path.rsplit(".", 1)[-1])
    }
    selected_paths = mapped_paths | discriminator_paths
    return {
        path: _row_path_value(row, path)
        for path in _iter_leaf_paths(row)
        if path in selected_paths
    }


def _json_path_value(payload: object, path: str) -> object:
    current = payload
    for key, index in re.findall(r"(?:^|\.)([^.\[]+)|\[(\d+)\]", path):
        if key:
            if not isinstance(current, dict) or key not in current:
                raise KeyError(path)
            current = current[key]
        else:
            if not isinstance(current, list):
                raise KeyError(path)
            current = current[int(index)]
    return current


def _query_params(request_url: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in parse_qsl(urlsplit(request_url).query, keep_blank_values=True):
        if SIGNATURE_HEADER.search(key):
            value = REDACTED_VALUE
        existing = result.get(key)
        if existing is None or (existing == "" and key not in result):
            result[key] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            result[key] = [existing, value]
    return result


def _url_has_userinfo(request_url: str) -> bool:
    parsed = urlsplit(request_url)
    return parsed.username is not None or parsed.password is not None


def _netloc_without_userinfo(request_url: str) -> str:
    parsed = urlsplit(request_url)
    if _url_has_userinfo(request_url):
        return parsed.netloc.rsplit("@", 1)[-1]
    return parsed.netloc


def _find_suspicious_body_keys(
    value: object,
    path: str,
    found: list[str],
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = _join_path(path, str(key))
            if SIGNATURE_HEADER.search(str(key)):
                found.append(child_path)
            else:
                _find_suspicious_body_keys(child, child_path, found)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _find_suspicious_body_keys(child, f"{path}[{index}]", found)


def find_suspicious_request_inputs(
    request_url: str,
    request_body: object | None,
    request_headers: object | None = None,
) -> list[str]:
    """Return URL/header/query/body paths that look signed or credential-like."""

    found = ["url.userinfo"] if _url_has_userinfo(request_url) else []
    if isinstance(request_headers, dict):
        found.extend(
            f"header.{normalized}"
            for key in request_headers
            if (normalized := _credential_header_name(key)) is not None
        )
    found.extend(
        f"query.{key}"
        for key, _value in parse_qsl(
            urlsplit(request_url).query,
            keep_blank_values=True,
        )
        if SIGNATURE_HEADER.search(key)
    )
    _find_suspicious_body_keys(request_body, "body", found)
    return found


def redact_suspicious_values(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): (
                REDACTED_VALUE
                if SIGNATURE_HEADER.search(str(key))
                else redact_suspicious_values(child)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact_suspicious_values(child) for child in value]
    return copy.deepcopy(value)


def redact_request_url(request_url: str) -> str:
    parsed = urlsplit(request_url)
    redacted_query = urlencode(
        [
            (key, REDACTED_VALUE if SIGNATURE_HEADER.search(key) else value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        ],
        doseq=True,
    )
    return urlunsplit(
        (
            parsed.scheme,
            _netloc_without_userinfo(request_url),
            parsed.path,
            redacted_query,
            parsed.fragment,
        )
    )


def _integer_or_default(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def build_config_draft(
    request_url: str,
    method: str,
    request_body: object | None,
    response_payload: object,
    list_path: str,
) -> dict[str, object]:
    """Build an adapter-shaped, evidence-based parser configuration draft."""

    parsed = urlsplit(request_url)
    endpoint = urlunsplit(
        (
            parsed.scheme,
            _netloc_without_userinfo(request_url),
            parsed.path,
            "",
            "",
        )
    )
    normalized_method = method.upper()
    request_values: object
    if normalized_method == "GET":
        request_values = _query_params(request_url)
    elif isinstance(request_body, dict):
        request_values = redact_suspicious_values(request_body)
    else:
        request_values = {}

    pagination_fields = infer_pagination_parameters(request_body, request_url)
    page_param = next(
        (
            path
            for path in pagination_fields
            if _pagination_role(path.rsplit(".", 1)[-1]) == "page"
        ),
        None,
    )
    size_param = next(
        (
            path
            for path in pagination_fields
            if _pagination_role(path.rsplit(".", 1)[-1]) == "size"
        ),
        None,
    )
    offset_param = next(
        (
            path
            for path in pagination_fields
            if _pagination_role(path.rsplit(".", 1)[-1]) == "offset"
        ),
        None,
    )

    raw_rows = _json_path_value(response_payload, list_path)
    rows = [row for row in raw_rows if isinstance(row, dict)] if isinstance(raw_rows, list) else []
    draft: dict[str, object] = {
        "endpoint": endpoint,
        "method": normalized_method,
        "list_path": list_path,
        "field_map": infer_field_map(rows),
        "batch": {
            "identity_key": "__REVIEW_REQUIRED__",
            "title": "__REVIEW_REQUIRED__",
            "official_page_url": "__REVIEW_REQUIRED__",
            "recruitment_type": "__REVIEW_REQUIRED__",
            "target_audience": "__REVIEW_REQUIRED__",
        },
    }
    draft["params" if normalized_method == "GET" else "body"] = request_values
    if page_param is not None and size_param is not None:
        draft["pagination"] = {
            "mode": "page_index",
            "page_param": page_param,
            "size_param": size_param,
            "page_size": _integer_or_default(pagination_fields[size_param], 10),
            "start_page": _integer_or_default(pagination_fields[page_param], 1),
            "max_pages": 10,
        }
    elif offset_param is not None and size_param is not None:
        draft["pagination_candidates"] = pagination_fields
        draft["pagination_note"] = (
            "Offset-based pagination is unsupported by the Phase 02 T1 "
            "page_index adapter; manual review is required."
        )
    elif pagination_fields:
        draft["pagination_candidates"] = pagination_fields

    total_path = infer_total_path(response_payload, list_path)
    if total_path is not None:
        draft["total_path"] = total_path
    success = infer_success(response_payload)
    if success is not None:
        draft["success"] = success
    return draft


def endpoint_identity(method: str, request_url: str) -> tuple[str, str]:
    """Identify an endpoint independently of captured pagination queries."""

    parsed = urlsplit(request_url)
    endpoint = urlunsplit(
        (
            parsed.scheme.lower(),
            _netloc_without_userinfo(request_url).lower(),
            parsed.path,
            "",
            "",
        )
    )
    return method.upper(), endpoint


def _material_request_value(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): _material_request_value(child)
            for key, child in value.items()
            if _pagination_role(str(key)) is None
            and not EPHEMERAL_REQUEST_KEY.fullmatch(str(key))
        }
    if isinstance(value, list):
        return [_material_request_value(child) for child in value]
    return value


def _material_request_document(
    request_url: str,
    request_body: object | None,
) -> dict[str, object]:
    material_query = [
        (
            key,
            REDACTED_VALUE if SIGNATURE_HEADER.search(key) else value,
        )
        for key, value in parse_qsl(
            urlsplit(request_url).query,
            keep_blank_values=True,
        )
        if _pagination_role(key) is None
        and not EPHEMERAL_REQUEST_KEY.fullmatch(key)
    ]
    return {
        "query": sorted(material_query),
        "body": _material_request_value(redact_suspicious_values(request_body)),
    }


def request_variant_identity(
    method: str,
    request_url: str,
    request_body: object | None,
) -> tuple[str, str, str]:
    """Identify material filter variants while ignoring pagination/cache values."""

    material = _material_request_document(request_url, request_body)
    canonical = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        *endpoint_identity(method, request_url),
        hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


def _campus_filter_score(request_url: str, request_body: object | None) -> int:
    material = _material_request_document(request_url, request_body)
    text = json.dumps(material, ensure_ascii=False, sort_keys=True)
    return len(CAMPUS_FILTER.findall(text))


def detect_page_block(
    http_status: int | None,
    final_url: str,
    visible_text: str,
    json_response_count: int,
) -> str | None:
    """Describe observable access blocks without attempting to bypass them."""

    if http_status is not None and http_status >= 400:
        return f"入口页返回 HTTP {http_status}，已跳过"
    lowered = visible_text.casefold()
    captcha_terms = (
        "验证码",
        "人机验证",
        "captcha",
        "verify you are human",
        "checking your browser",
        "access denied",
        "访问验证",
    )
    if any(term in lowered for term in captcha_terms):
        return "页面出现验证码或人机验证，按合规要求已跳过"
    path = urlsplit(final_url).path.casefold()
    login_path = re.search(r"(?:^|/)(?:login|signin|passport|auth)(?:/|$)", path)
    login_text = any(term in lowered for term in ("密码", "password")) and any(
        term in lowered for term in ("登录", "sign in", "login")
    )
    if login_path or login_text:
        return "页面出现登录墙，按合规要求已跳过"
    if len(visible_text.strip()) < 5 and json_response_count == 0:
        return "页面无可见内容且未捕获 JSON 响应，可能被无头浏览器拦截"
    return None


def click_safety_reason(metadata: dict[str, object]) -> str | None:
    """Reject selectors whose target could submit a form."""

    element_type = str(metadata.get("type", "")).casefold()
    inside_form = bool(metadata.get("inside_form"))
    target = str(metadata.get("target", "")).casefold()
    if target and target not in {"_self", "_parent", "_top"}:
        return "选择器会打开新页面；每个目标只允许打开一个页面"
    if element_type in {"submit", "image"}:
        return "选择器指向表单提交控件；工具不会提交任何数据"
    if inside_form:
        return "选择器位于表单内；工具不会与表单交互"
    return None


def _record_guard_violation(violations: list[str], message: object) -> None:
    normalized = str(message or "unknown forbidden interaction").strip()
    if normalized and normalized not in violations:
        violations.append(normalized)


def create_guarded_page(context, violations: list[str]):
    """Create the sole page after installing pre-navigation interaction guards."""

    def report_violation(_source, message) -> None:
        _record_guard_violation(violations, message)

    context.expose_binding(
        "__officialCampusRadarViolation",
        report_violation,
    )
    context.add_init_script(script=INTERACTION_GUARD_SCRIPT)
    page = context.new_page()

    def block_new_page(new_page) -> None:
        _record_guard_violation(violations, "new page blocked")
        try:
            new_page.close()
        except Exception:
            pass

    context.on("page", block_new_page)
    page.on("popup", block_new_page)
    return page


def guard_violation_reason(violations: list[str]) -> str | None:
    if not violations:
        return None
    return "已阻止禁止的表单/新页面交互：" + ", ".join(violations)


def classify_replay_results(
    results: list[dict[str, object]],
) -> dict[str, str]:
    """Apply the strict rule that only the minimal compliant profile is admissible."""

    by_name = {str(result.get("name", "")): result for result in results}
    minimal = by_name.get("最简合规头", {})
    if minimal.get("equivalent") is True:
        return {
            "status": "可接入",
            "reason": "最简合规头返回等效非空候选列表；签名头非必需",
        }
    baseline = by_name.get("完整头 + Cookie（基线）", {})
    without_signature = by_name.get("去掉疑似签名头", {})
    if (
        baseline.get("equivalent") is True
        and without_signature.get("equivalent") is False
    ):
        return {
            "status": "不可接入",
            "reason": "去掉疑似签名头后不再等效，签名可能为必需；未尝试逆向",
        }
    return {
        "status": "不可接入",
        "reason": "最简合规头未返回等效非空候选列表",
    }


def _validated_url(value: object) -> str:
    url = str(value or "").strip()
    parsed = urlsplit(url)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("target URL must not contain userinfo or credentials")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"target URL must be an absolute HTTP(S) URL: {url!r}")
    return url


def parse_targets_document(
    document: object,
    *,
    default_wait: float,
    default_scroll: bool,
    default_click: str | None,
) -> list[TargetSpec]:
    """Parse the documented list/object target-file forms."""

    raw_targets = document.get("targets") if isinstance(document, dict) else document
    if not isinstance(raw_targets, list) or not raw_targets:
        raise ValueError("targets JSON must be a non-empty list or an object with targets")
    targets: list[TargetSpec] = []
    for index, item in enumerate(raw_targets, start=1):
        target_id = None
        company = None
        company_type = None
        official_evidence_url = None
        if isinstance(item, str):
            url = _validated_url(item)
            wait_seconds = default_wait
            scroll = default_scroll
            click_selector = default_click
        elif isinstance(item, dict):
            url = _validated_url(item.get("url"))
            wait_seconds = item.get("wait", default_wait)
            scroll = item.get("scroll", default_scroll)
            click_selector = item.get("click", default_click)
            metadata = {
                "target_id": item.get("id"),
                "company": item.get("company"),
                "company_type": item.get("company_type"),
            }
            for field_name, value in metadata.items():
                if value is not None and not isinstance(value, str):
                    raise ValueError(f"target {index} {field_name} must be a string")
            target_id = str(metadata["target_id"] or "").strip() or None
            company = str(metadata["company"] or "").strip() or None
            company_type = str(metadata["company_type"] or "").strip() or None
            if item.get("official_evidence_url") is not None:
                official_evidence_url = _validated_url(
                    item.get("official_evidence_url")
                )
        else:
            raise ValueError(f"target {index} must be a URL string or object")
        if (
            not isinstance(wait_seconds, (int, float))
            or isinstance(wait_seconds, bool)
            or not math.isfinite(wait_seconds)
            or wait_seconds < 0
        ):
            raise ValueError(
                f"target {index} wait must be a finite non-negative number"
            )
        if not isinstance(scroll, bool):
            raise ValueError(f"target {index} scroll must be true or false")
        if click_selector is not None:
            click_selector = str(click_selector).strip() or None
        targets.append(
            TargetSpec(
                url=url,
                wait_seconds=float(wait_seconds),
                scroll=scroll,
                click_selector=click_selector,
                target_id=target_id,
                company=company,
                company_type=company_type,
                official_evidence_url=official_evidence_url,
            )
        )
    return targets


def _nonnegative_wait(value: str) -> float:
    try:
        wait = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("wait must be a non-negative number") from error
    if not math.isfinite(wait) or wait < 0:
        raise argparse.ArgumentTypeError("wait must be a finite non-negative number")
    return wait


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Discover candidate recruitment JSON APIs with one compliant headless "
            "page visit per target."
        ),
        epilog=(
            "Development-only: no login, credentials, form submission, CAPTCHA "
            "bypass, stealth, signature reverse engineering, path scans, or "
            "parameter brute force."
        ),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="single recruitment entry-page URL")
    source.add_argument("--targets", help="JSON file containing target URLs/options")
    parser.add_argument(
        "--wait",
        type=_nonnegative_wait,
        default=8,
        help="seconds to wait after navigation (default: 8)",
    )
    parser.add_argument(
        "--scroll",
        action="store_true",
        help="scroll to the page bottom three times to trigger lazy loading",
    )
    parser.add_argument(
        "--click",
        help="click one non-form-submitting CSS selector after the wait",
    )
    parser.add_argument("--out", help="Markdown report path; stdout when omitted")
    return parser


def _markdown_cell(value: object) -> str:
    return str(value if value is not None else "—").replace("|", "\\|").replace(
        "\n", " "
    )


def render_markdown_report(
    target_results: list[dict[str, object]],
    *,
    generated_at: str,
) -> str:
    """Render observed discovery facts and configuration drafts as Markdown."""

    lines = [
        "# Recruitment API discovery report",
        "",
        f"Generated: `{generated_at}`",
        "",
        (
            "> Development-only evidence. A discovered endpoint is not an integrated "
            "source; samples require human review to confirm campus recruitment."
        ),
    ]
    for target_index, target in enumerate(target_results, start=1):
        target_heading = target.get("target_id") or target_index
        lines.extend(
            [
                "",
                f"## Target {target_heading}",
                "",
                f"- Company: `{target.get('company') or '—'}`",
                f"- Company type: `{target.get('company_type') or '—'}`",
                (
                    "- Official-source evidence: `"
                    f"{target.get('official_evidence_url') or '—'}`"
                ),
                f"- Entry page: `{target.get('entry_url', '')}`",
                f"- Final page: `{target.get('final_url', '') or '—'}`",
                f"- Page status: `{target.get('page_status', '—')}`",
            ]
        )
        exchanges = target.get("exchanges", [])
        capture_notes = []
        if isinstance(exchanges, list):
            capture_notes = [
                exchange
                for exchange in exchanges
                if isinstance(exchange, dict) and exchange.get("capture_note")
            ]
        if capture_notes:
            lines.extend(["", "### Capture notes", ""])
            for exchange in capture_notes:
                method = str(exchange.get("method", ""))
                request_url = redact_request_url(
                    str(exchange.get("request_url", ""))
                )
                response_status = exchange.get("response_status", "—")
                note = _markdown_cell(exchange.get("capture_note"))
                lines.append(
                    f"- `{method} {request_url}` / `{response_status}` — {note}"
                )
        block_reason = target.get("block_reason")
        error = target.get("error")
        if block_reason or error:
            lines.extend(
                [
                    "- Outcome: skipped",
                    f"- Reason: {_markdown_cell(block_reason or error)}",
                ]
            )
            continue
        candidates = target.get("candidates", [])
        if not isinstance(candidates, list) or not candidates:
            lines.extend(
                [
                    "- Outcome: no candidate job API detected",
                    "",
                    "No endpoint discovery is claimed for this target.",
                ]
            )
            continue
        lines.extend(
            [
                "- Outcome: candidate endpoints observed",
                "",
                "Candidate APIs below are discovery facts, not integration claims.",
            ]
        )
        for candidate_index, candidate in enumerate(candidates, start=1):
            verdict = candidate.get("verdict", {})
            if not isinstance(verdict, dict):
                verdict = {}
            lines.extend(
                [
                    "",
                    f"### Candidate {candidate_index}",
                    "",
                    (
                        f"- Request: `{candidate.get('method', '')} "
                        f"{candidate.get('request_url', '')}`"
                    ),
                    (
                        f"- Response: `{candidate.get('response_status', '—')}` / "
                        f"`{candidate.get('content_type', '—')}`"
                    ),
                    f"- Candidate list path: `{candidate.get('list_path', '')}`",
                    f"- Candidate row count: `{candidate.get('row_count', '—')}`",
                    f"- Total path: `{candidate.get('total_path') or 'not inferred'}`",
                    f"- Reported total: `{candidate.get('reported_total', '—')}`",
                    f"- Confidence score: `{candidate.get('confidence', '—')}`",
                    (
                        "- Shared endpoint replay budget: `"
                        f"{candidate.get('endpoint_replay_budget_used', 0)} / "
                        f"{candidate.get('endpoint_replay_budget_limit', MAX_REPLAYS_PER_ENDPOINT)}"
                        "`"
                    ),
                    (
                        "- Captured request header names: `"
                        f"{', '.join(candidate.get('header_names', [])) or 'none'}` "
                        "(values redacted)"
                    ),
                    (
                        f"- Replay verdict: **{verdict.get('status', 'not verified')}** "
                        f"— {_markdown_cell(verdict.get('reason', ''))}"
                    ),
                    (
                        "- Suspicious URL/header/query/body paths: `"
                        f"{', '.join(candidate.get('suspicious_inputs', [])) or 'none'}`"
                    ),
                    "",
                    "#### Replay verification",
                    "",
                    "| Level | HTTP | Equivalent non-empty list | Note |",
                    "| --- | ---: | :---: | --- |",
                ]
            )
            replays = candidate.get("replays", [])
            if isinstance(replays, list):
                for replay in replays:
                    equivalent = "yes" if replay.get("equivalent") is True else "no"
                    lines.append(
                        "| "
                        + " | ".join(
                            (
                                _markdown_cell(replay.get("name")),
                                _markdown_cell(replay.get("http_status")),
                                equivalent,
                                _markdown_cell(replay.get("note")),
                            )
                        )
                        + " |"
                    )
            lines.extend(
                [
                    "",
                    "#### Parser configuration draft",
                    "",
                    (
                        "The draft contains observed/inferred API fields only. Human "
                        "review must add batch metadata and confirm campus scope."
                    ),
                    "",
                    "```json",
                    json.dumps(
                        candidate.get("config", {}),
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    ),
                    "```",
                    "",
                    "#### Job samples (raw key values)",
                ]
            )
            samples = candidate.get("samples", [])
            if not isinstance(samples, list) or not samples:
                lines.extend(["", "No sample rows retained."])
            else:
                for sample_index, sample in enumerate(samples[:5], start=1):
                    lines.extend(
                        [
                            "",
                            f"Sample {sample_index}:",
                            "",
                            "```json",
                            json.dumps(sample, ensure_ascii=False, indent=2, default=str),
                            "```",
                        ]
                    )
    return "\n".join(lines).rstrip() + "\n"


def analyze_captured_target(capture: dict[str, object]) -> list[dict[str, object]]:
    """Turn captures into ranked candidates without discarding filter variants."""

    best_by_variant: dict[
        tuple[str, str, str, tuple[str, ...], str],
        dict[str, object],
    ] = {}
    exchanges = capture.get("exchanges", [])
    if not isinstance(exchanges, list):
        return []
    for exchange in exchanges:
        if not isinstance(exchange, dict):
            continue
        response_payload = exchange.get("response_json")
        request_url = str(exchange.get("request_url", ""))
        method = str(exchange.get("method", "GET")).upper()
        if response_payload is None or not request_url:
            continue
        for candidate_array in find_candidate_arrays(response_payload):
            total_path = infer_total_path(response_payload, candidate_array.path)
            reported_total = (
                _json_path_value(response_payload, total_path)
                if total_path
                else None
            )
            request_headers = exchange.get("request_headers", {})
            if not isinstance(request_headers, dict):
                request_headers = {}
            suspicious_inputs = find_suspicious_request_inputs(
                request_url,
                exchange.get("request_json"),
                request_headers,
            )
            redacted_json = redact_suspicious_values(exchange.get("request_json"))
            config = build_config_draft(
                request_url,
                method,
                exchange.get("request_json"),
                response_payload,
                candidate_array.path,
            )
            field_map = config.get("field_map", {})
            if not isinstance(field_map, dict):
                field_map = {}
            candidate: dict[str, object] = {
                "method": method,
                "request_url": redact_request_url(request_url),
                "request_headers": redact_request_headers(request_headers),
                "request_body": redacted_json,
                "request_json": redacted_json,
                "_replay_url": redact_request_url(request_url),
                "_replay_body": exchange.get("request_body"),
                "_replay_json": copy.deepcopy(exchange.get("request_json")),
                "suspicious_inputs": suspicious_inputs,
                "response_status": exchange.get("response_status"),
                "content_type": exchange.get("content_type", ""),
                "list_path": candidate_array.path,
                "row_count": len(candidate_array.rows),
                "total_path": total_path,
                "reported_total": reported_total,
                "confidence": candidate_array.score,
                "campus_filter_score": _campus_filter_score(
                    request_url,
                    exchange.get("request_json"),
                ),
                "header_names": sorted(
                    {str(key).strip().lower() for key in request_headers}
                ),
                "replays": [],
                "verdict": {
                    "status": "未验证",
                    "reason": "尚未执行合规重放",
                },
                "config": config,
                "samples": [
                    select_sample_fields(row, field_map)
                    for row in candidate_array.rows[:5]
                ],
            }
            identity = (
                *request_variant_identity(
                    method,
                    request_url,
                    exchange.get("request_json"),
                ),
                tuple(sorted(suspicious_inputs)),
                candidate_array.path,
            )
            current = best_by_variant.get(identity)
            if current is None or candidate_array.score > int(
                current.get("confidence", 0)
            ):
                best_by_variant[identity] = candidate
    return sorted(
        best_by_variant.values(),
        key=lambda candidate: (
            -int(candidate.get("confidence", 0)),
            -int(candidate.get("campus_filter_score", 0)),
            str(candidate.get("request_url", "")),
            str(candidate.get("list_path", "")),
        ),
    )


def _evaluate_replay_payload(
    http_status: object,
    payload: object,
    list_path: str,
) -> tuple[bool, str]:
    if not isinstance(http_status, int):
        return False, "未取得 HTTP 响应"
    if http_status >= 300:
        return False, f"HTTP {http_status}"
    if payload is None:
        return False, f"HTTP {http_status}，响应不是可验证的有界 JSON"
    try:
        rows = _json_path_value(payload, list_path)
    except (KeyError, IndexError, ValueError):
        return False, f"HTTP {http_status}，候选列表路径不存在"
    if not isinstance(rows, list) or not rows:
        return False, f"HTTP {http_status}，候选列表路径为空或类型不符"
    return True, f"HTTP {http_status}，候选列表路径仍存在且非空"


def _execute_replay_observations(
    candidate: dict[str, object],
    *,
    requester: Callable[..., dict[str, object]],
    request_budget: int = REPLAY_LADDER_REQUESTS,
    sleep_fn: Callable[[float], object] = time.sleep,
) -> list[dict[str, object]]:
    """Issue one fixed ladder and retain bounded responses for path evaluation."""

    if candidate.get("suspicious_inputs"):
        return []

    raw_headers = candidate.get("request_headers", {})
    if not isinstance(raw_headers, dict):
        raw_headers = {}
    profiles = build_replay_header_profiles(raw_headers)
    if len(profiles) != REPLAY_LADDER_REQUESTS:
        raise DiscoveryError("replay ladder must contain exactly 5 requests")
    if request_budget < REPLAY_LADDER_REQUESTS:
        raise DiscoveryError(
            "replay ladder requires 5 requests but only "
            f"{request_budget} remain in the endpoint budget"
        )
    observations: list[dict[str, object]] = []
    for index, profile in enumerate(profiles):
        response = requester(
            method=str(candidate.get("method", "GET")),
            url=str(candidate.get("_replay_url", candidate.get("request_url", ""))),
            headers=profile.headers,
            request_json=candidate.get("_replay_json", candidate.get("request_json")),
            request_body=candidate.get("_replay_body", candidate.get("request_body")),
        )
        observations.append(
            {
                "name": profile.name,
                "http_status": response.get("http_status"),
                "payload": response.get("payload"),
                "response_note": str(response.get("note", "")).strip(),
            }
        )
        if index + 1 < len(profiles):
            sleep_fn(1.0)
    return observations


def _evaluate_replay_observations(
    observations: list[dict[str, object]],
    list_path: str,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for observation in observations:
        http_status = observation.get("http_status")
        payload = observation.get("payload")
        equivalent, note = _evaluate_replay_payload(
            http_status,
            payload,
            list_path,
        )
        response_note = str(observation.get("response_note", "")).strip()
        if response_note and payload is None:
            note = response_note
        results.append(
            {
                "name": observation.get("name", ""),
                "http_status": http_status,
                "equivalent": equivalent,
                "note": note,
            }
        )
    return results


def execute_replay_ladder(
    candidate: dict[str, object],
    *,
    requester: Callable[..., dict[str, object]],
    request_budget: int = REPLAY_LADDER_REQUESTS,
    sleep_fn: Callable[[float], object] = time.sleep,
) -> list[dict[str, object]]:
    """Execute the fixed five-request ladder sequentially for one list path."""

    observations = _execute_replay_observations(
        candidate,
        requester=requester,
        request_budget=request_budget,
        sleep_fn=sleep_fn,
    )
    return _evaluate_replay_observations(
        observations,
        str(candidate.get("list_path", "")),
    )


def _sanitized_capture_result(capture: dict[str, object]) -> dict[str, object]:
    """Copy capture facts while removing credentials from returned results."""

    result = copy.deepcopy(capture)
    for url_key in ("entry_url", "final_url"):
        value = result.get(url_key)
        if isinstance(value, str):
            result[url_key] = redact_request_url(value)
    exchanges = result.get("exchanges", [])
    if not isinstance(exchanges, list):
        return result
    for exchange in exchanges:
        if not isinstance(exchange, dict):
            continue
        request_url = exchange.get("request_url")
        if isinstance(request_url, str):
            exchange["request_url"] = redact_request_url(request_url)
        request_headers = exchange.get("request_headers")
        if isinstance(request_headers, dict):
            exchange["request_headers"] = redact_request_headers(request_headers)
        request_json = exchange.get("request_json")
        redacted_json = redact_suspicious_values(request_json)
        exchange["request_json"] = redacted_json
        if request_json != redacted_json:
            exchange["request_body"] = REDACTED_VALUE
    return result


def run_target_sequence(
    targets: list[TargetSpec],
    *,
    capture_func: Callable[[TargetSpec], dict[str, object]],
    requester: Callable[..., dict[str, object]],
    sleep_fn: Callable[[float], object] = time.sleep,
) -> list[dict[str, object]]:
    """Process target entries serially, opening each once with a three-second gap."""

    results: list[dict[str, object]] = []
    endpoint_replay_usage: dict[tuple[str, str], int] = {}
    for index, target in enumerate(targets):
        if index:
            sleep_fn(3.0)
        capture = capture_func(target)
        target_result = _sanitized_capture_result(capture)
        target_result.setdefault("target_id", target.target_id)
        target_result.setdefault("company", target.company)
        target_result.setdefault("company_type", target.company_type)
        target_result.setdefault(
            "official_evidence_url",
            redact_request_url(target.official_evidence_url)
            if target.official_evidence_url
            else None,
        )
        candidates: list[dict[str, object]] = []
        if not capture.get("block_reason") and not capture.get("error"):
            grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
            for raw_candidate in analyze_captured_target(capture):
                key = endpoint_identity(
                    str(raw_candidate.get("method", "GET")),
                    str(raw_candidate.get("request_url", "")),
                )
                grouped.setdefault(key, []).append(dict(raw_candidate))
            for endpoint_key, endpoint_candidates in grouped.items():
                replay_used = endpoint_replay_usage.get(endpoint_key, 0)
                ladder_attempted = replay_used > 0
                variants: dict[
                    tuple[str, str, str, tuple[str, ...]],
                    list[dict[str, object]],
                ] = {}
                for candidate in endpoint_candidates:
                    suspicious_inputs = candidate.get("suspicious_inputs", [])
                    if not isinstance(suspicious_inputs, list):
                        suspicious_inputs = []
                    variant_key = (
                        *request_variant_identity(
                            str(candidate.get("method", "GET")),
                            str(
                                candidate.get(
                                    "_replay_url",
                                    candidate.get("request_url", ""),
                                )
                            ),
                            candidate.get(
                                "_replay_json",
                                candidate.get("request_json"),
                            ),
                        ),
                        tuple(sorted(str(path) for path in suspicious_inputs)),
                    )
                    variants.setdefault(variant_key, []).append(candidate)
                for variant_candidates in variants.values():
                    representative = variant_candidates[0]
                    if representative.get("suspicious_inputs"):
                        for candidate in variant_candidates:
                            candidate["replays"] = []
                            candidate["verdict"] = {
                                "status": "不可接入",
                                "reason": (
                                    "URL、查询或请求正文含疑似签名/凭据字段；"
                                    "未发出重放请求，也未尝试移除或逆向"
                                ),
                            }
                    elif (
                        not ladder_attempted
                        and MAX_REPLAYS_PER_ENDPOINT - replay_used
                        >= REPLAY_LADDER_REQUESTS
                    ):
                        remaining_budget = MAX_REPLAYS_PER_ENDPOINT - replay_used
                        observations = _execute_replay_observations(
                            representative,
                            requester=requester,
                            request_budget=remaining_budget,
                            sleep_fn=sleep_fn,
                        )
                        replay_used += len(observations)
                        endpoint_replay_usage[endpoint_key] = replay_used
                        ladder_attempted = True
                        for candidate in variant_candidates:
                            replays = _evaluate_replay_observations(
                                observations,
                                str(candidate.get("list_path", "")),
                            )
                            candidate["replays"] = replays
                            candidate["verdict"] = classify_replay_results(
                                replays
                            )
                    else:
                        for candidate in variant_candidates:
                            candidate["replays"] = []
                            candidate["verdict"] = {
                                "status": "未重放",
                                "reason": (
                                    "共享端点预算只允许一个完整五级重放梯度；"
                                    "该过滤变体已保留但未发出请求"
                                ),
                            }
                for candidate in endpoint_candidates:
                    candidate["endpoint_replay_budget_used"] = replay_used
                    candidate["endpoint_replay_budget_limit"] = (
                        MAX_REPLAYS_PER_ENDPOINT
                    )
                    candidates.append(candidate)
            candidates.sort(
                key=lambda candidate: (
                    -int(candidate.get("confidence", 0)),
                    -int(candidate.get("campus_filter_score", 0)),
                    str(candidate.get("request_url", "")),
                    str(candidate.get("list_path", "")),
                )
            )
        target_result["candidates"] = candidates
        results.append(target_result)
    return results


def _single_line(error: BaseException) -> str:
    return " ".join(str(error).split())[:500]


def safe_request_post_data(request: object) -> tuple[str | None, str]:
    """Read textual request data without letting binary bodies break capture."""

    try:
        return request.post_data, ""
    except Exception:
        # Playwright raises its own Error type here, but importing it at module
        # load time would make the offline tool helpers require Playwright.
        return None, "Request body omitted: unavailable as UTF-8 text"


def _append_capture_note(exchange: dict[str, object], note: str) -> None:
    if not note:
        return
    previous = str(exchange.get("capture_note") or "")
    exchange["capture_note"] = f"{previous}; {note}" if previous else note


def capture_target(target: TargetSpec) -> dict[str, object]:
    """Open exactly one headless Chromium page and capture bounded JSON responses."""

    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as error:
        raise DiscoveryError(
            "Playwright is not installed. Run "
            "`py -3.13 -m pip install -r requirements-dev.txt` first."
        ) from error

    result: dict[str, object] = {
        "entry_url": target.url,
        "final_url": "",
        "page_status": None,
        "block_reason": None,
        "error": None,
        "exchanges": [],
    }
    exchanges: list[dict[str, object]] = []
    interaction_violations: list[str] = []

    def record_response(response) -> None:
        request = response.request
        try:
            request_headers = request.all_headers()
        except PlaywrightError:
            request_headers = dict(request.headers)
        request_body, request_capture_note = safe_request_post_data(request)
        request_json = None
        if request_body:
            try:
                request_json = json.loads(request_body)
            except (TypeError, json.JSONDecodeError):
                request_json = None
        response_headers = response.headers
        content_type = str(response_headers.get("content-type", ""))
        exchange: dict[str, object] = {
            "request_url": request.url,
            "method": request.method,
            "request_headers": dict(request_headers),
            "request_body": request_body,
            "request_json": request_json,
            "response_status": response.status,
            "content_type": content_type,
            "response_json": None,
            "capture_note": request_capture_note,
        }
        if "json" in content_type.casefold():
            content_length = response_headers.get("content-length")
            try:
                declared_size = int(content_length) if content_length else None
            except ValueError:
                declared_size = None
            if declared_size is not None and declared_size > MAX_JSON_BODY_BYTES:
                _append_capture_note(exchange, (
                    f"JSON body omitted: declared size {declared_size} exceeds "
                    f"{MAX_JSON_BODY_BYTES} bytes"
                ))
            else:
                try:
                    body = response.body()
                    if len(body) > MAX_JSON_BODY_BYTES:
                        _append_capture_note(exchange, (
                            f"JSON body omitted: actual size {len(body)} exceeds "
                            f"{MAX_JSON_BODY_BYTES} bytes"
                        ))
                    else:
                        exchange["response_json"] = json.loads(body)
                except (PlaywrightError, UnicodeDecodeError, json.JSONDecodeError) as error:
                    _append_capture_note(exchange, (
                        "JSON body could not be retained: " + _single_line(error)
                    ))
        exchanges.append(exchange)

    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=["--no-proxy-server"],
                )
            except PlaywrightError as error:
                raise DiscoveryError(
                    "Chromium is unavailable. Run "
                    "`py -3.13 -m playwright install chromium`."
                ) from error
            try:
                context = browser.new_context()
                page = create_guarded_page(context, interaction_violations)
                page.on("response", record_response)
                navigation = page.goto(
                    target.url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                result["page_status"] = navigation.status if navigation else None
                page.wait_for_timeout(target.wait_seconds * 1000)
                result["error"] = guard_violation_reason(interaction_violations)
                if target.scroll and not result["error"]:
                    for _ in range(3):
                        page.evaluate(
                            "window.scrollTo(0, document.body.scrollHeight)"
                        )
                        result["error"] = guard_violation_reason(
                            interaction_violations
                        )
                        if result["error"]:
                            break
                        page.wait_for_timeout(750)
                        result["error"] = guard_violation_reason(
                            interaction_violations
                        )
                        if result["error"]:
                            break
                if target.click_selector and not result["error"]:
                    locator = page.locator(target.click_selector).first
                    locator.wait_for(state="visible", timeout=5_000)
                    metadata = locator.evaluate(
                        """
                        element => ({
                          tag_name: element.tagName.toLowerCase(),
                          type: (element.getAttribute('type') || element.type || '').toLowerCase(),
                          inside_form: Boolean(element.closest('form')),
                          target: (element.getAttribute('target') ||
                            (document.querySelector('base[target]') || {}).target ||
                            '').toLowerCase()
                        })
                        """
                    )
                    safety_reason = click_safety_reason(metadata)
                    if safety_reason:
                        result["error"] = safety_reason
                    else:
                        locator.click(timeout=5_000)
                        result["error"] = guard_violation_reason(
                            interaction_violations
                        )
                        if not result["error"]:
                            page.wait_for_timeout(1_500)
                            result["error"] = guard_violation_reason(
                                interaction_violations
                            )
                result["final_url"] = page.url
                try:
                    visible_text = page.locator("body").inner_text(timeout=5_000)
                except PlaywrightError:
                    visible_text = ""
                json_response_count = sum(
                    exchange.get("response_json") is not None
                    for exchange in exchanges
                )
                if not result["error"]:
                    result["block_reason"] = detect_page_block(
                        result["page_status"]
                        if isinstance(result["page_status"], int)
                        else None,
                        str(result["final_url"]),
                        visible_text,
                        json_response_count,
                    )
            except PlaywrightTimeoutError as error:
                result["error"] = "页面操作超时：" + _single_line(error)
            except PlaywrightError as error:
                result["error"] = "浏览器捕获失败：" + _single_line(error)
            finally:
                browser.close()
    finally:
        result["exchanges"] = exchanges
    return result


def _requests_requester(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    request_json: object,
    request_body: object,
) -> dict[str, object]:
    """Perform one bounded, non-redirecting replay request."""

    if _url_has_userinfo(url):
        return {
            "http_status": None,
            "payload": None,
            "note": "request refused: URL userinfo or credentials are prohibited",
        }
    if any(_credential_header_name(key) for key in headers):
        return {
            "http_status": None,
            "payload": None,
            "note": "request refused: credential-bearing headers are prohibited",
        }

    import requests

    excluded_headers = {
        "accept-encoding",
        "connection",
        "content-length",
        "host",
        "transfer-encoding",
    }
    safe_headers = {
        key: value
        for key, value in headers.items()
        if key.casefold() not in excluded_headers
    }
    kwargs: dict[str, object] = {
        "allow_redirects": False,
        "headers": safe_headers,
        "stream": True,
        "timeout": 20,
    }
    if method.upper() != "GET":
        if request_json is not None:
            kwargs["json"] = request_json
        elif request_body is not None:
            kwargs["data"] = request_body
    session = requests.Session()
    session.trust_env = False
    try:
        with session.request(method.upper(), url, **kwargs) as response:
            body = bytearray()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                body.extend(chunk)
                if len(body) > MAX_JSON_BODY_BYTES:
                    return {
                        "http_status": response.status_code,
                        "payload": None,
                        "note": (
                            "replay JSON body exceeds "
                            f"{MAX_JSON_BODY_BYTES} bytes and was not retained"
                        ),
                    }
            content_type = response.headers.get("content-type", "")
            if "json" not in content_type.casefold():
                return {
                    "http_status": response.status_code,
                    "payload": None,
                    "note": f"HTTP {response.status_code}, non-JSON content-type",
                }
            try:
                payload = json.loads(bytes(body))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return {
                    "http_status": response.status_code,
                    "payload": None,
                    "note": f"HTTP {response.status_code}, malformed JSON",
                }
            return {
                "http_status": response.status_code,
                "payload": payload,
                "note": f"HTTP {response.status_code} JSON",
            }
    except requests.RequestException as error:
        return {
            "http_status": None,
            "payload": None,
            "note": "request failed: " + _single_line(error),
        }
    finally:
        session.close()


def _load_targets(args: argparse.Namespace) -> list[TargetSpec]:
    if args.url:
        document: object = [args.url]
    else:
        targets_path = Path(args.targets)
        try:
            document = json.loads(targets_path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise DiscoveryError(f"targets file not found: {targets_path}") from error
        except json.JSONDecodeError as error:
            raise DiscoveryError(
                f"targets file is not valid JSON: {targets_path}: {error.msg}"
            ) from error
        except OSError as error:
            raise DiscoveryError(
                f"targets file could not be read: {targets_path}: {_single_line(error)}"
            ) from error
    return parse_targets_document(
        document,
        default_wait=args.wait,
        default_scroll=args.scroll,
        default_click=args.click,
    )


def main(
    argv: list[str] | None = None,
    *,
    capture_func: Callable[[TargetSpec], dict[str, object]] | None = None,
    requester: Callable[..., dict[str, object]] | None = None,
    sleep_fn: Callable[[float], object] = time.sleep,
    now_fn: Callable[[], str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run discovery and return stable script-friendly exit codes."""

    parser = build_parser()
    args = parser.parse_args(argv)
    output = stdout or sys.stdout
    errors = stderr or sys.stderr
    capture_boundary = capture_func or capture_target
    request_boundary = requester or _requests_requester
    try:
        targets = _load_targets(args)
        results = run_target_sequence(
            targets,
            capture_func=capture_boundary,
            requester=request_boundary,
            sleep_fn=sleep_fn,
        )
        generated_at = now_fn() if now_fn is not None else (
            datetime.now().astimezone().isoformat(timespec="seconds")
        )
        report = render_markdown_report(results, generated_at=generated_at)
        if args.out:
            report_path = Path(args.out)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report, encoding="utf-8")
            output.write(f"report: {report_path}\n")
        else:
            output.write(report)
    except (DiscoveryError, ValueError, OSError) as error:
        errors.write(f"error: {_single_line(error)}\n")
        return 2
    incomplete = any(
        result.get("block_reason")
        or result.get("error")
        or not result.get("candidates")
        for result in results
    )
    return 1 if incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())
