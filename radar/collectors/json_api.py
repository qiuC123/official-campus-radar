import copy
import hashlib
import json
import math
import re
import time
import warnings
from datetime import date, datetime, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from radar.collectors.base import (
    EXPLICIT_MISSING,
    FieldEvidenceValue,
    FetchedPage,
    RecruitmentBatchCandidate,
    PositionCandidate,
)
from radar.models import OfficialSource
from radar.services.normalization import canonicalize_url


SUPPORTED_HTML_FIELDS = {
    "title",
    "location",
    "raw_text",
    "application_url",
}

# Some ATS responses repeat a position across adjacent pages while updating
# request-time counters. These top-level fields are not part of the position's
# business identity and must not turn an otherwise identical duplicate into a
# conflict. Keep this allowlist deliberately narrow: all other fields remain
# subject to strict equality.
VOLATILE_DUPLICATE_COMPARISON_FIELDS = frozenset({"pageViews"})


def _path_value(payload: object, path: str, default: object = None) -> object:
    """Resolve dotted object paths and flatten explicit ``[]`` list segments."""
    parts = path.split(".") if path else []

    def resolve(current: object, remaining: list[str]) -> object:
        if not remaining:
            return current
        part = remaining[0]
        if not part:
            return default
        is_array = part.endswith("[]")
        key = part[:-2] if is_array else part
        if not isinstance(current, dict) or key not in current:
            return default
        child = current[key]
        if not is_array:
            return resolve(child, remaining[1:])
        if not isinstance(child, list):
            return default
        values: list[object] = []
        for item in child:
            value = resolve(item, remaining[1:])
            if value is default:
                continue
            if isinstance(value, list):
                values.extend(value)
            else:
                values.append(value)
        return values

    return resolve(payload, parts)


def _field_value(payload: object, path_expression: str, default: object = None) -> object:
    """Return the first populated value from ``path||fallback`` expressions."""
    for path in path_expression.split("||"):
        path = path.strip()
        if not path:
            continue
        value = _path_value(payload, path, default)
        if value is default or value is None or value == "" or value == []:
            continue
        return value
    return default


def _set_path(payload: dict, path: str, value: object) -> None:
    parts = path.split(".")
    current = payload
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value


def _path_has_non_dict_intermediate(payload: dict, path: str) -> bool:
    current = payload
    for part in path.split(".")[:-1]:
        if part not in current:
            return False
        child = current[part]
        if not isinstance(child, dict):
            return True
        current = child
    return False


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _canonical_duplicate_comparison_row(row: dict) -> str:
    comparison_row = {
        key: value
        for key, value in row.items()
        if key not in VOLATILE_DUPLICATE_COMPARISON_FIELDS
    }
    return _canonical_json(comparison_row)


class JsonApiSourceAdapter:
    max_page_limit = 100
    timeout_seconds = 15
    user_agent = "OfficialCampusRadar/0.1 (local low-frequency collector)"

    def _finalize_fetched_page(
        self,
        *,
        config: dict,
        endpoint: str,
        aggregate_document: dict,
        positions: list[object],
        positions_complete: bool,
        http_status: int,
    ) -> FetchedPage:
        """Build the canonical page shared by HTTP and browser JSON transports."""

        list_path = str(config["list_path"]).strip()
        pagination = config["pagination"]
        total_kind = str(pagination.get("total_kind", "items")).strip().lower()
        pagination_mode = str(pagination["mode"]).strip().lower()
        duplicate_rows_removed = 0
        position_key_path = str(config["field_map"]["position_key"]).strip()
        unique_positions: list[object] = []
        rows_by_key: dict[str, str] = {}
        for row in positions:
            if not isinstance(row, dict):
                unique_positions.append(row)
                continue
            raw_key = _field_value(row, position_key_path, "")
            position_key = self._raw_text(raw_key).strip()
            if not position_key:
                unique_positions.append(row)
                continue
            canonical_row = _canonical_duplicate_comparison_row(row)
            previous_row = rows_by_key.get(position_key)
            if previous_row is None:
                rows_by_key[position_key] = canonical_row
                unique_positions.append(row)
            elif previous_row == canonical_row:
                duplicate_rows_removed += 1
            else:
                raise ValueError(
                    f"JSON API returned conflicting rows for position key {position_key!r}"
                )
        _set_path(aggregate_document, list_path, unique_positions)
        aggregate_document["_radar"] = {
            "positions_complete": positions_complete,
            "list_path": list_path,
            "batch": copy.deepcopy(config["batch"]),
            "field_map": copy.deepcopy(config["field_map"]),
            "valid_values": copy.deepcopy(config.get("valid_values", {})),
            "row_filters": copy.deepcopy(config.get("row_filters", [])),
            "html_fields": copy.deepcopy(config.get("html_fields", [])),
            "pagination_total_kind": total_kind,
            "pagination_mode": pagination_mode,
            "duplicate_rows_removed": duplicate_rows_removed,
            "batch_partitions": copy.deepcopy(
                config.get("batch_partitions", [])
            ),
        }
        body = _canonical_json(aggregate_document)
        return FetchedPage(
            canonical_url=canonicalize_url(endpoint),
            body=body,
            content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            http_status=http_status,
            etag=None,
        )

    @staticmethod
    def validate_source_config(source: OfficialSource) -> None:
        config = source.parser_config
        if not isinstance(config, dict):
            raise ValueError("JSON API parser_config must be an object")

        endpoint = str(config.get("endpoint", "")).strip()
        parsed_endpoint = urlparse(endpoint)
        if not endpoint:
            raise ValueError("JSON API endpoint is required")
        if parsed_endpoint.scheme != "https":
            raise ValueError("JSON API endpoint must use HTTPS")
        if (
            parsed_endpoint.username is not None
            or parsed_endpoint.password is not None
        ):
            raise ValueError("JSON API endpoint must not contain userinfo")
        official_domain = source.organization.official_domain.strip().lower()
        endpoint_host = (parsed_endpoint.hostname or "").lower()
        if not official_domain or not (
            endpoint_host == official_domain
            or endpoint_host.endswith(f".{official_domain}")
        ):
            raise ValueError("JSON API endpoint must belong to the official domain")

        method = str(config.get("method", "GET")).upper()
        if method not in {"GET", "POST"}:
            raise ValueError("JSON API method must be GET or POST")
        default_body_encoding = "query" if method == "GET" else "json"
        body_encoding = str(
            config.get("body_encoding", default_body_encoding)
        ).strip().lower()
        allowed_body_encodings = {"query"} if method == "GET" else {"json", "form"}
        if body_encoding not in allowed_body_encodings:
            raise ValueError(
                f"JSON API body_encoding must be one of "
                f"{sorted(allowed_body_encodings)} for {method}"
            )

        if "success" in config:
            success = config["success"]
            if not isinstance(success, dict):
                raise ValueError("JSON API success must be an object")
            if not str(success.get("path", "")).strip():
                raise ValueError("JSON API success.path is required")
            if "expect" not in success:
                raise ValueError("JSON API success.expect is required")

        list_path = str(config.get("list_path", "")).strip()
        if not list_path:
            raise ValueError("JSON API list_path is required")
        if list_path == "_radar" or list_path.startswith("_radar."):
            raise ValueError("JSON API list_path cannot use the reserved _radar key")
        if any(not part for part in list_path.split(".")):
            raise ValueError("JSON API list_path must be a dotted object path")

        params = config.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("JSON API params must be an object")
        body = config.get("body") if "body" in config else None
        if "body" in config and not isinstance(body, dict):
            raise ValueError("JSON API body must be an object")

        headers = config.get("headers", {})
        if not isinstance(headers, dict):
            raise ValueError("JSON API headers must be an object")
        allowed_headers = {
            "accept",
            "accept-language",
            "content-type",
            "origin",
            "referer",
            "cr-service",
        }
        for raw_name, raw_value in headers.items():
            name = str(raw_name).strip()
            value = str(raw_value).strip()
            if name.lower() not in allowed_headers:
                raise ValueError(f"JSON API header {name!r} is not allowed")
            if not value or "\r" in value or "\n" in value:
                raise ValueError(f"JSON API header {name!r} has an invalid value")

        field_map = config.get("field_map")
        if not isinstance(field_map, dict):
            raise ValueError("JSON API field_map must be an object")
        for name in ("position_key", "title"):
            if not str(field_map.get(name, "")).strip():
                raise ValueError(f"JSON API field_map.{name} is required")

        html_fields = config.get("html_fields", [])
        if not isinstance(html_fields, list):
            raise ValueError("JSON API html_fields must be a list")
        seen_html_fields: set[str] = set()
        for configured_name in html_fields:
            name = str(configured_name).strip()
            if not name or name not in SUPPORTED_HTML_FIELDS:
                raise ValueError(
                    "JSON API html_fields entries must be supported position roles"
                )
            if name in seen_html_fields:
                raise ValueError("JSON API html_fields entries must be unique")
            if not str(field_map.get(name, "")).strip():
                raise ValueError(
                    f"JSON API field_map.{name} is required by html_fields"
                )
            seen_html_fields.add(name)

        valid_values = config.get("valid_values", {})
        if not isinstance(valid_values, dict):
            raise ValueError("JSON API valid_values must be an object")
        for name, allowed_values in valid_values.items():
            if not str(field_map.get(name, "")).strip():
                raise ValueError(
                    f"JSON API valid_values.{name} requires a field_map path"
                )
            if not isinstance(allowed_values, list) or not allowed_values:
                raise ValueError(
                    f"JSON API valid_values.{name} must be a non-empty list"
                )

        row_filters = config.get("row_filters", [])
        if not isinstance(row_filters, list):
            raise ValueError("JSON API row_filters must be a list")
        for row_filter in row_filters:
            if not isinstance(row_filter, dict):
                raise ValueError("JSON API row_filters entries must be objects")
            if not str(row_filter.get("path", "")).strip():
                raise ValueError("JSON API row filter path is required")
            operators = [
                name
                for name in (
                    "equals_any",
                    "contains_any",
                    "not_equals_any",
                    "not_contains_any",
                )
                if name in row_filter
            ]
            if len(operators) != 1:
                raise ValueError(
                    "JSON API row filter requires exactly one supported operator"
                )
            values = row_filter[operators[0]]
            if not isinstance(values, list) or not values:
                raise ValueError("JSON API row filter values must be a non-empty list")

        batch = config.get("batch")
        if not isinstance(batch, dict):
            raise ValueError("JSON API batch must be an object")
        for name in (
            "identity_key",
            "title",
            "official_page_url",
            "recruitment_type",
            "target_audience",
        ):
            if not str(batch.get(name, "")).strip():
                raise ValueError(f"JSON API batch.{name} is required")

        official_page_url = urlparse(str(batch["official_page_url"]).strip())
        source_url = urlparse(source.source_url)
        if (
            official_page_url.scheme != "https"
            or not official_page_url.hostname
            or official_page_url.hostname.lower()
            != (source_url.hostname or "").lower()
        ):
            raise ValueError(
                "JSON API batch.official_page_url must use HTTPS on the source host"
            )

        batch_partitions = config.get("batch_partitions", [])
        if not isinstance(batch_partitions, list):
            raise ValueError("JSON API batch_partitions must be a list")
        if len(batch_partitions) > 20:
            raise ValueError("JSON API batch_partitions must contain at most 20 entries")
        partition_identities: set[str] = set()
        for partition in batch_partitions:
            if not isinstance(partition, dict) or set(partition) != {"batch", "row_filters"}:
                raise ValueError(
                    "JSON API batch partition requires exactly batch and row_filters"
                )
            partition_batch = partition["batch"]
            partition_filters = partition["row_filters"]
            if not isinstance(partition_batch, dict):
                raise ValueError("JSON API batch partition batch must be an object")
            for name in (
                "identity_key",
                "title",
                "official_page_url",
                "recruitment_type",
                "target_audience",
            ):
                if not str(partition_batch.get(name, "")).strip():
                    raise ValueError(
                        f"JSON API batch partition batch.{name} is required"
                    )
            identity = str(partition_batch["identity_key"]).strip()
            if identity in partition_identities:
                raise ValueError("JSON API batch partition identities must be unique")
            partition_identities.add(identity)
            partition_url = urlparse(
                str(partition_batch["official_page_url"]).strip()
            )
            if (
                partition_url.scheme != "https"
                or not partition_url.hostname
                or partition_url.hostname.lower()
                != (source_url.hostname or "").lower()
            ):
                raise ValueError(
                    "JSON API partition official_page_url must use HTTPS on the source host"
                )
            for name in ("published_on", "deadline"):
                has_fixed_provenance = name in partition_batch
                fixed_value = str(partition_batch.get(name, "")).strip()
                if not (
                    has_fixed_provenance
                    or str(field_map.get(name, "")).strip()
                ):
                    raise ValueError(
                        "JSON API batch partition "
                        f"{name} requires a fixed batch value or field path"
                    )
                if fixed_value:
                    try:
                        date.fromisoformat(fixed_value)
                    except ValueError as error:
                        raise ValueError(
                            "JSON API batch partition "
                            f"batch.{name} must be an ISO date"
                        ) from error
            if not isinstance(partition_filters, list) or not partition_filters:
                raise ValueError(
                    "JSON API batch partition row_filters must be a non-empty list"
                )
            for row_filter in partition_filters:
                if not isinstance(row_filter, dict):
                    raise ValueError(
                        "JSON API batch partition row filters must be objects"
                    )
                if not str(row_filter.get("path", "")).strip():
                    raise ValueError(
                        "JSON API batch partition row filter path is required"
                    )
                operators = [
                    name
                    for name in (
                        "equals_any",
                        "contains_any",
                        "not_equals_any",
                        "not_contains_any",
                    )
                    if name in row_filter
                ]
                if len(operators) != 1:
                    raise ValueError(
                        "JSON API batch partition row filter requires exactly one operator"
                    )
                values = row_filter[operators[0]]
                if not isinstance(values, list) or not values:
                    raise ValueError(
                        "JSON API batch partition row filter values must be non-empty"
                    )

        partition_coverage = config.get("partition_coverage")
        if partition_coverage is not None:
            if (
                not isinstance(partition_coverage, dict)
                or set(partition_coverage) != {"request_path", "row_path"}
            ):
                raise ValueError(
                    "JSON API partition_coverage requires exactly request_path and row_path"
                )
            if not batch_partitions:
                raise ValueError(
                    "JSON API partition_coverage requires batch_partitions"
                )
            request_path = str(partition_coverage["request_path"]).strip()
            row_path = str(partition_coverage["row_path"]).strip()
            if not request_path or not row_path:
                raise ValueError(
                    "JSON API partition_coverage paths must be non-empty"
                )
            request_template = (
                params if method == "GET" else body if body is not None else params
            )
            missing = object()
            if _path_value(request_template, request_path, missing) != []:
                raise ValueError(
                    "JSON API partition_coverage request path must be an explicit empty list"
                )
            covered_values: set[str] = set()
            for partition in batch_partitions:
                coverage_filters = [
                    row_filter
                    for row_filter in partition["row_filters"]
                    if str(row_filter.get("path", "")).strip() == row_path
                ]
                if (
                    len(coverage_filters) != 1
                    or set(coverage_filters[0]) != {"path", "equals_any"}
                ):
                    raise ValueError(
                        "JSON API partition_coverage requires one equals_any filter "
                        "for its row path in every partition"
                    )
                values = {
                    str(value).strip()
                    for value in coverage_filters[0]["equals_any"]
                    if str(value).strip()
                }
                if not values or covered_values & values:
                    raise ValueError(
                        "JSON API partition_coverage values must be non-empty and disjoint"
                    )
                covered_values.update(values)

        for name in ("published_on", "deadline"):
            has_fixed_provenance = name in batch
            fixed_value = str(batch.get(name, "")).strip()
            if not (
                has_fixed_provenance
                or str(field_map.get(name, "")).strip()
            ):
                raise ValueError(
                    f"JSON API {name} requires a fixed batch value or field path"
                )
            if fixed_value:
                try:
                    date.fromisoformat(fixed_value)
                except ValueError as error:
                    raise ValueError(
                        f"JSON API batch.{name} must be an ISO date"
                    ) from error

        pagination = config.get("pagination")
        if not isinstance(pagination, dict):
            raise ValueError("JSON API pagination must be an object")
        pagination_mode = str(pagination.get("mode", "")).strip().lower()
        if pagination_mode not in {"page_index", "offset", "single"}:
            raise ValueError(
                "JSON API pagination.mode must be page_index, offset, or single"
            )
        total_kind = str(pagination.get("total_kind", "items")).strip().lower()
        if total_kind not in {"items", "pages"}:
            raise ValueError(
                "JSON API pagination.total_kind must be items or pages"
            )
        total_path = str(config.get("total_path", "")).strip()
        if total_kind == "pages" and not total_path:
            raise ValueError(
                "JSON API total_path is required when pagination.total_kind is pages"
            )
        if pagination_mode == "offset" and total_kind != "items":
            raise ValueError(
                "JSON API offset pagination only supports item totals"
            )
        max_pages = pagination.get("max_pages")
        if (
            not isinstance(max_pages, int)
            or isinstance(max_pages, bool)
            or max_pages <= 0
            or max_pages > JsonApiSourceAdapter.max_page_limit
        ):
            raise ValueError(
                "JSON API pagination.max_pages must be between 1 and 100"
            )
        page_size = pagination.get("page_size")
        if not isinstance(page_size, int) or isinstance(page_size, bool) or page_size <= 0:
            raise ValueError("JSON API pagination.page_size must be a positive integer")
        if pagination_mode == "single":
            if max_pages != 1:
                raise ValueError("JSON API single pagination requires max_pages=1")
            return

        request_template = (
            params if method == "GET" else body if body is not None else params
        )
        pagination_paths: dict[str, str] = {}
        for name in ("page_param", "size_param"):
            path = str(pagination.get(name, "")).strip()
            if not path:
                raise ValueError(f"JSON API pagination.{name} is required")
            if any(not part for part in path.split(".")):
                raise ValueError(
                    f"JSON API pagination.{name} must be a dotted object path"
                )
            if _path_has_non_dict_intermediate(request_template, path):
                raise ValueError(
                    f"JSON API pagination.{name} collides with the request template"
                )
            pagination_paths[name] = path
            if body_encoding == "form" and "." in path:
                raise ValueError(
                    "JSON API form pagination paths must be top-level fields"
                )
        page_param = pagination_paths["page_param"]
        size_param = pagination_paths["size_param"]
        if (
            page_param == size_param
            or page_param.startswith(f"{size_param}.")
            or size_param.startswith(f"{page_param}.")
        ):
            raise ValueError(
                "JSON API pagination.page_param and pagination.size_param "
                "must not overlap"
            )
        start_name = "start_page" if pagination_mode == "page_index" else "start_offset"
        start_default = 1 if pagination_mode == "page_index" else 0
        start_value = pagination.get(start_name, start_default)
        if (
            not isinstance(start_value, int)
            or isinstance(start_value, bool)
            or start_value < 0
        ):
            raise ValueError(
                f"JSON API pagination.{start_name} must be a non-negative integer"
            )

        if body_encoding == "form":
            for key, value in request_template.items():
                if isinstance(value, (dict, list, tuple, set)):
                    raise ValueError(
                        f"JSON API form body field {key!r} must be a scalar value"
                    )

        delay = config.get("request_delay_seconds", 1)
        if (
            not isinstance(delay, (int, float))
            or isinstance(delay, bool)
            or not math.isfinite(delay)
            or delay <= 0
        ):
            raise ValueError(
                "JSON API request_delay_seconds must be a finite positive number"
            )

    def fetch(self, source: OfficialSource) -> FetchedPage:
        self.validate_source_config(source)
        config = source.parser_config
        endpoint = str(config["endpoint"]).strip()
        method = str(config.get("method", "GET")).upper()
        pagination = config["pagination"]
        pagination_mode = str(pagination["mode"]).strip().lower()
        page_param = str(pagination.get("page_param", "")).strip()
        size_param = str(pagination.get("size_param", "")).strip()
        page_size = pagination["page_size"]
        start_page = pagination.get("start_page", 1)
        start_offset = pagination.get("start_offset", 0)
        max_pages = pagination["max_pages"]
        delay = config.get("request_delay_seconds", 1)
        list_path = str(config["list_path"]).strip()
        total_path = str(config.get("total_path", "")).strip()
        total_kind = str(pagination.get("total_kind", "items")).strip().lower()
        body_encoding = str(
            config.get(
                "body_encoding",
                "query" if method == "GET" else "json",
            )
        ).strip().lower()
        base_request_values = (
            config.get("params", {})
            if method == "GET"
            else config.get("body", config.get("params", {}))
        )

        session = requests.Session()
        session.trust_env = False
        headers = {"User-Agent": self.user_agent}
        headers.update(
            {
                str(name).strip(): str(value).strip()
                for name, value in config.get("headers", {}).items()
            }
        )
        positions: list[object] = []
        aggregate_document: dict | None = None
        positions_complete = False
        last_response = None
        missing = object()

        for page_number in range(max_pages):
            request_values = copy.deepcopy(base_request_values)
            if pagination_mode != "single":
                request_cursor = (
                    start_page + page_number
                    if pagination_mode == "page_index"
                    else start_offset + page_number * page_size
                )
                _set_path(request_values, page_param, request_cursor)
                _set_path(request_values, size_param, page_size)
            request_kwargs = {
                "allow_redirects": False,
                "headers": headers,
                "timeout": self.timeout_seconds,
            }
            if method == "GET":
                request_kwargs["params"] = request_values
            elif body_encoding == "form":
                request_kwargs["data"] = request_values
            else:
                request_kwargs["json"] = request_values
            session.cookies.clear()
            response = session.request(method, endpoint, **request_kwargs)
            last_response = response
            if response.status_code >= 300:
                raise requests.HTTPError(f"HTTP {response.status_code}")
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("JSON API response must be an object")
            success = config.get("success")
            if isinstance(success, dict):
                actual = _path_value(
                    payload,
                    str(success.get("path", "")).strip(),
                    missing,
                )
                if actual is missing or str(actual) != str(success.get("expect")):
                    raise ValueError("JSON API success check failed")
            if "_radar" in payload:
                raise ValueError(
                    "JSON API response contains the reserved _radar metadata key"
                )
            page_positions = _path_value(payload, list_path, missing)
            if page_positions is missing or not isinstance(page_positions, list):
                raise ValueError(
                    f"JSON API list_path {list_path!r} must resolve to a list"
                )
            if aggregate_document is None:
                aggregate_document = copy.deepcopy(payload)
            positions.extend(copy.deepcopy(page_positions))

            if pagination_mode == "single":
                positions_complete = True
                break

            if not page_positions:
                positions_complete = True
                break

            total = None
            if total_path:
                raw_total = _path_value(payload, total_path, missing)
                if raw_total is not missing:
                    if isinstance(raw_total, int) and not isinstance(
                        raw_total, bool
                    ):
                        total = raw_total
                    elif isinstance(raw_total, str) and re.fullmatch(
                        r"(?:0|-?[1-9][0-9]*)", raw_total
                    ):
                        total = int(raw_total)
                    else:
                        raise ValueError(
                            f"JSON API total_path {total_path!r} must resolve to an integer"
                        )
                    if total < 0:
                        raise ValueError("JSON API total count cannot be negative")
            if total is not None:
                if total_kind == "pages":
                    if total == 0:
                        raise ValueError(
                            "JSON API total page count cannot be zero for a non-empty page"
                        )
                    if page_number + 1 >= total:
                        positions_complete = True
                        break
                elif len(positions) >= total:
                    positions_complete = True
                    break

            if config.get("stop_on_short_page", False) and len(page_positions) < page_size:
                positions_complete = True
                break

            if page_number + 1 < max_pages:
                time.sleep(delay)

        if aggregate_document is None or last_response is None:
            raise ValueError("JSON API pagination returned no response")
        return self._finalize_fetched_page(
            config=config,
            endpoint=endpoint,
            aggregate_document=aggregate_document,
            positions=positions,
            positions_complete=positions_complete,
            http_status=last_response.status_code,
        )

    @staticmethod
    def _parse_date(value: object) -> date | None:
        if isinstance(value, date):
            return value
        text = str(value or "").strip()
        if not text:
            return None
        if re.fullmatch(r"\d{10}|\d{13}", text):
            timestamp = int(text)
            if len(text) == 13:
                timestamp /= 1000
            try:
                return datetime.fromtimestamp(timestamp, tz=timezone.utc).date()
            except (OverflowError, OSError, ValueError):
                return None
        try:
            return date.fromisoformat(text)
        except ValueError:
            try:
                return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
            except ValueError:
                pass
            match = re.fullmatch(
                r"(?P<year>\d{4})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日",
                text,
            )
            if match is None:
                return None
            try:
                return date(
                    int(match.group("year")),
                    int(match.group("month")),
                    int(match.group("day")),
                )
            except ValueError:
                return None

    @staticmethod
    def _raw_text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return _canonical_json(value)
        return str(value)

    @classmethod
    def _field_text(
        cls,
        field_name: str,
        value: object,
        html_fields: set[str],
    ) -> str:
        if field_name == "location" and isinstance(value, list):
            raw_value = "、".join(
                cls._raw_text(item).strip()
                for item in value
                if cls._raw_text(item).strip()
            )
        else:
            raw_value = cls._raw_text(value)
        if field_name not in html_fields:
            return raw_value
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", MarkupResemblesLocatorWarning)
            return BeautifulSoup(raw_value, "html.parser").get_text(
                separator="\n",
                strip=True,
            )

    @classmethod
    def _row_is_valid(
        cls,
        row: dict,
        field_map: dict,
        valid_values: dict,
        row_filters: list,
    ) -> bool:
        def equals_any(raw_value, allowed_values) -> bool:
            for allowed in allowed_values:
                if raw_value == allowed:
                    return True
                if isinstance(raw_value, (str, int, float, bool)) and isinstance(
                    allowed, (str, int, float, bool)
                ) and str(raw_value) == str(allowed):
                    return True
            return False

        for field_name, allowed_values in valid_values.items():
            field_path = str(field_map.get(field_name, "")).strip()
            if (
                not field_path
                or not isinstance(allowed_values, list)
                or _field_value(row, field_path) not in allowed_values
            ):
                return False
        for row_filter in row_filters:
            if not isinstance(row_filter, dict):
                return False
            raw_value = _field_value(
                row,
                str(row_filter.get("path", "")).strip(),
                "",
            )
            if "equals_any" in row_filter:
                matched = equals_any(raw_value, row_filter["equals_any"])
            elif "contains_any" in row_filter:
                text_value = cls._raw_text(raw_value)
                matched = any(
                    str(fragment) in text_value
                    for fragment in row_filter["contains_any"]
                )
            elif "not_equals_any" in row_filter:
                matched = not equals_any(raw_value, row_filter["not_equals_any"])
            elif "not_contains_any" in row_filter:
                text_value = cls._raw_text(raw_value)
                matched = all(
                    str(fragment) not in text_value
                    for fragment in row_filter["not_contains_any"]
                )
            else:
                return False
            if not matched:
                return False
        return True

    def extract(
        self, source: OfficialSource, page: FetchedPage
    ) -> list[RecruitmentBatchCandidate]:
        if page.not_modified:
            return []
        document = json.loads(page.body)
        if not isinstance(document, dict):
            raise ValueError("JSON API canonical document must be an object")
        metadata = document.get("_radar")
        if not isinstance(metadata, dict):
            raise ValueError("JSON API canonical document is missing adapter metadata")
        list_path = str(metadata.get("list_path", "")).strip()
        batch_config = metadata.get("batch")
        field_map = metadata.get("field_map")
        valid_values = metadata.get("valid_values", {})
        row_filters = metadata.get("row_filters", [])
        raw_html_fields = metadata.get("html_fields", [])
        if not list_path or not isinstance(batch_config, dict):
            raise ValueError("JSON API canonical document has invalid batch metadata")
        if (
            not isinstance(field_map, dict)
            or not isinstance(valid_values, dict)
            or not isinstance(raw_html_fields, list)
            or not isinstance(row_filters, list)
        ):
            raise ValueError("JSON API canonical document has invalid field metadata")
        html_fields = {
            str(field_name).strip()
            for field_name in raw_html_fields
            if str(field_name).strip()
        }
        rows = _path_value(document, list_path)
        if not isinstance(rows, list):
            raise ValueError("JSON API canonical list_path must resolve to a list")

        batch_partitions = metadata.get("batch_partitions", [])
        if batch_partitions:
            if not isinstance(batch_partitions, list):
                raise ValueError("JSON API canonical batch partitions must be a list")
            position_key_path = str(field_map["position_key"]).strip()
            expected_keys = {
                self._raw_text(
                    _field_value(row, position_key_path, "")
                ).strip()
                for row in rows
                if isinstance(row, dict)
                and self._row_is_valid(
                    row,
                    field_map,
                    valid_values,
                    row_filters,
                )
                and self._raw_text(
                    _field_value(row, position_key_path, "")
                ).strip()
            }
            partition_candidates: list[RecruitmentBatchCandidate] = []
            observed_keys: set[str] = set()
            for partition in batch_partitions:
                partition_document = copy.deepcopy(document)
                partition_metadata = partition_document["_radar"]
                partition_metadata["batch"] = copy.deepcopy(partition["batch"])
                partition_metadata["row_filters"] = [
                    *copy.deepcopy(row_filters),
                    *copy.deepcopy(partition["row_filters"]),
                ]
                partition_metadata["batch_partitions"] = []
                partition_body = _canonical_json(partition_document)
                partition_page = FetchedPage(
                    canonical_url=page.canonical_url,
                    body=partition_body,
                    content_hash=hashlib.sha256(
                        partition_body.encode("utf-8")
                    ).hexdigest(),
                    http_status=page.http_status,
                    etag=page.etag,
                )
                candidates = self.extract(source, partition_page)
                if len(candidates) != 1:
                    raise ValueError(
                        "JSON API batch partition must produce exactly one batch"
                    )
                candidate = candidates[0]
                candidate_keys = {
                    position.position_key for position in candidate.positions
                }
                if observed_keys & candidate_keys:
                    raise ValueError(
                        "JSON API batch partitions overlap on position keys"
                    )
                observed_keys.update(candidate_keys)
                partition_candidates.append(candidate)
            if observed_keys != expected_keys:
                missing = len(expected_keys - observed_keys)
                unexpected = len(observed_keys - expected_keys)
                raise ValueError(
                    "JSON API batch partitions must cover every retained position "
                    f"exactly once (missing={missing}, unexpected={unexpected})"
                )
            return partition_candidates

        positions: list[PositionCandidate] = []
        retained_rows: list[tuple[int, dict]] = []
        filtered_invalid = 0
        skipped_missing_identity = 0
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            valid = self._row_is_valid(
                row,
                field_map,
                valid_values,
                row_filters,
            )
            if not valid:
                filtered_invalid += 1
                continue

            position_key_path = str(field_map["position_key"]).strip()
            raw_position_key = _field_value(row, position_key_path, "")
            position_key = self._raw_text(raw_position_key).strip()
            if not position_key:
                skipped_missing_identity += 1
                continue

            base_locator = f"$.{list_path}[{index}]"
            title_path = str(field_map["title"]).strip()
            location_path = str(field_map.get("location", "")).strip()
            raw_text_path = str(field_map.get("raw_text", "")).strip()
            application_path = str(
                field_map.get("application_url", "")
            ).strip()
            updated_path = str(field_map.get("updated_at", "")).strip()
            raw_title = _field_value(row, title_path, "")
            raw_location = (
                _field_value(row, location_path, "") if location_path else ""
            )
            raw_description = (
                _field_value(row, raw_text_path, "") if raw_text_path else ""
            )
            raw_application_url = (
                _field_value(row, application_path, "")
                if application_path
                else ""
            )
            raw_updated = _field_value(row, updated_path, "") if updated_path else ""
            source_updated_on = self._parse_date(raw_updated)
            title = self._field_text("title", raw_title, html_fields).strip()
            location = self._field_text(
                "location", raw_location, html_fields
            ).strip()
            location_is_missing = not location
            if location_is_missing:
                location = "未说明"
            description = self._field_text(
                "raw_text", raw_description, html_fields
            ).strip()
            application_url = (
                self._field_text(
                    "application_url",
                    raw_application_url,
                    html_fields,
                ).strip()
                or None
            )
            if application_url:
                application_url = canonicalize_url(application_url)

            position_evidence: dict[str, FieldEvidenceValue] = {
                "position_title": FieldEvidenceValue(
                    self._raw_text(raw_title),
                    f"{base_locator}.{title_path}",
                    title,
                    excerpt=title if "title" in html_fields else None,
                )
            }
            if location_path:
                position_evidence["location"] = FieldEvidenceValue(
                    (
                        EXPLICIT_MISSING
                        if location_is_missing
                        else self._raw_text(raw_location)
                    ),
                    f"{base_locator}.{location_path}",
                    location,
                    excerpt=(
                        location
                        if location_is_missing or "location" in html_fields
                        else None
                    ),
                )
            if raw_text_path:
                position_evidence["raw_text"] = FieldEvidenceValue(
                    self._raw_text(raw_description),
                    f"{base_locator}.{raw_text_path}",
                    description,
                    excerpt=(
                        description if "raw_text" in html_fields else None
                    ),
                )
            if application_path and application_url:
                position_evidence["application_link"] = FieldEvidenceValue(
                    self._raw_text(raw_application_url),
                    f"{base_locator}.{application_path}",
                    application_url,
                    excerpt=(
                        application_url
                        if "application_url" in html_fields
                        else None
                    ),
                )
            if updated_path and source_updated_on:
                position_evidence["source_updated_on"] = FieldEvidenceValue(
                    self._raw_text(raw_updated),
                    f"{base_locator}.{updated_path}",
                    source_updated_on.isoformat(),
                )
            positions.append(
                PositionCandidate(
                    title=title,
                    location_text=location,
                    raw_text=description,
                    application_url=application_url,
                    locator=base_locator,
                    application_locator=(
                        f"{base_locator}.{application_path}"
                        if application_path
                        else ""
                    ),
                    position_key=position_key,
                    field_evidence=position_evidence,
                    source_updated_on=source_updated_on,
                )
            )
            retained_rows.append((index, row))

        def batch_text(field_name: str) -> tuple[str, str]:
            raw_value = batch_config.get(field_name, "")
            return (
                self._raw_text(raw_value).strip(),
                f"$._radar.batch.{field_name}",
            )

        def batch_date(field_name: str) -> tuple[date | None, FieldEvidenceValue]:
            has_missing_provenance = False
            if field_name in batch_config:
                raw_value = batch_config[field_name]
                locator = f"$._radar.batch.{field_name}"
                has_missing_provenance = True
            else:
                field_path = str(field_map.get(field_name, "")).strip()
                if retained_rows and field_path:
                    index, row = retained_rows[0]
                    raw_value = _path_value(row, field_path, "")
                    locator = f"$.{list_path}[{index}].{field_path}"
                    has_missing_provenance = True
                else:
                    raw_value = ""
                    locator = f"$._radar.field_map.{field_name}"
            parsed_date = self._parse_date(raw_value)
            parsed_value = parsed_date.isoformat() if parsed_date else ""
            return parsed_date, FieldEvidenceValue(
                self._raw_text(raw_value) or (
                    EXPLICIT_MISSING if has_missing_provenance else ""
                ),
                locator,
                parsed_value,
            )

        title, title_locator = batch_text("title")
        recruitment_type, recruitment_type_locator = batch_text(
            "recruitment_type"
        )
        target_audience, target_audience_locator = batch_text(
            "target_audience"
        )
        official_page_url, notice_url_locator = batch_text("official_page_url")
        official_page_url = canonicalize_url(official_page_url)
        published_on, published_evidence = batch_date("published_on")
        deadline, deadline_evidence = batch_date("deadline")
        field_evidence = {
            "title": FieldEvidenceValue(title, title_locator, title),
            "recruitment_type": FieldEvidenceValue(
                recruitment_type,
                recruitment_type_locator,
                recruitment_type,
            ),
            "target_audience": FieldEvidenceValue(
                target_audience,
                target_audience_locator,
                target_audience,
            ),
            "published_on": published_evidence,
            "deadline": deadline_evidence,
            "official_page_url": FieldEvidenceValue(
                self._raw_text(batch_config.get("official_page_url", "")),
                notice_url_locator,
                official_page_url,
            ),
        }
        return [
            RecruitmentBatchCandidate(
                title=title,
                official_page_url=official_page_url,
                recruitment_type=recruitment_type,
                target_audience=target_audience,
                published_on=published_on,
                deadline=deadline,
                withdrawn=False,
                evidence_excerpt=(
                    f"rows={len(rows)} retained={len(positions)} "
                    f"skipped_missing_identity={skipped_missing_identity} "
                    f"filtered_invalid={filtered_invalid}"
                    f" duplicate_rows_removed={metadata.get('duplicate_rows_removed', 0)}"
                ),
                positions=tuple(positions),
                field_locators={
                    name: evidence.locator
                    for name, evidence in field_evidence.items()
                },
                identity_key=self._raw_text(
                    batch_config.get("identity_key", "")
                ).strip(),
                field_evidence=field_evidence,
                positions_complete=bool(
                    metadata.get("positions_complete", False)
                ),
            )
        ]
