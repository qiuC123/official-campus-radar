import copy
import hashlib
import json
import time
from urllib.parse import urlparse

import requests

from radar.collectors.base import FetchedPage
from radar.models import OfficialSource
from radar.services.normalization import canonicalize_url


def _path_value(payload: object, path: str, default: object = None) -> object:
    current = payload
    for part in path.split("."):
        if not part or not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


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


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


class JsonApiSourceAdapter:
    max_page_limit = 100
    timeout_seconds = 15
    user_agent = "OfficialCampusRadar/0.1 (local low-frequency collector)"

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

        if not str(config.get("list_path", "")).strip():
            raise ValueError("JSON API list_path is required")

        field_map = config.get("field_map")
        if not isinstance(field_map, dict):
            raise ValueError("JSON API field_map must be an object")
        for name in ("position_key", "title"):
            if not str(field_map.get(name, "")).strip():
                raise ValueError(f"JSON API field_map.{name} is required")

        notice = config.get("notice")
        if not isinstance(notice, dict):
            raise ValueError("JSON API notice must be an object")
        for name in (
            "identity_key",
            "title",
            "official_notice_url",
            "recruitment_type",
            "target_audience",
        ):
            if not str(notice.get(name, "")).strip():
                raise ValueError(f"JSON API notice.{name} is required")
        for name in ("published_on", "deadline"):
            if not (
                str(notice.get(name, "")).strip()
                or str(field_map.get(name, "")).strip()
            ):
                raise ValueError(
                    f"JSON API {name} requires a fixed notice value or field path"
                )

        pagination = config.get("pagination")
        if not isinstance(pagination, dict):
            raise ValueError("JSON API pagination must be an object")
        if pagination.get("mode") != "page_index":
            raise ValueError("JSON API pagination.mode must be page_index")
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

        delay = config.get("request_delay_seconds", 1)
        if (
            not isinstance(delay, (int, float))
            or isinstance(delay, bool)
            or delay < 0
        ):
            raise ValueError(
                "JSON API request_delay_seconds must be a non-negative number"
            )

    def fetch(self, source: OfficialSource) -> FetchedPage:
        self.validate_source_config(source)
        config = source.parser_config
        endpoint = str(config["endpoint"]).strip()
        method = str(config.get("method", "GET")).upper()
        pagination = config["pagination"]
        page_param = str(pagination.get("page_param", "pageIndex"))
        size_param = str(pagination.get("size_param", "pageSize"))
        page_size = pagination["page_size"]
        start_page = pagination.get("start_page", 1)
        max_pages = pagination["max_pages"]
        delay = config.get("request_delay_seconds", 1)
        list_path = str(config["list_path"]).strip()
        total_path = str(config.get("total_path", "")).strip()
        base_params = config.get("params", {})
        if not isinstance(base_params, dict):
            raise ValueError("JSON API params must be an object")

        session = requests.Session()
        headers = {"User-Agent": self.user_agent}
        positions: list[object] = []
        aggregate_document: dict | None = None
        positions_complete = False
        last_response = None
        missing = object()

        for offset in range(max_pages):
            request_values = dict(base_params)
            request_values[page_param] = start_page + offset
            request_values[size_param] = page_size
            request_kwargs = {
                "headers": headers,
                "timeout": self.timeout_seconds,
            }
            if method == "GET":
                request_kwargs["params"] = request_values
            else:
                request_kwargs["json"] = request_values
            response = session.request(method, endpoint, **request_kwargs)
            last_response = response
            if response.status_code >= 400:
                raise requests.HTTPError(f"HTTP {response.status_code}")
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("JSON API response must be an object")
            page_positions = _path_value(payload, list_path, missing)
            if page_positions is missing or not isinstance(page_positions, list):
                raise ValueError(
                    f"JSON API list_path {list_path!r} must resolve to a list"
                )
            if aggregate_document is None:
                aggregate_document = copy.deepcopy(payload)
            positions.extend(copy.deepcopy(page_positions))

            if not page_positions:
                positions_complete = True
                break

            total = None
            if total_path:
                raw_total = _path_value(payload, total_path, missing)
                if raw_total is not missing:
                    try:
                        total = int(raw_total)
                    except (TypeError, ValueError) as error:
                        raise ValueError(
                            f"JSON API total_path {total_path!r} must resolve to an integer"
                        ) from error
                    if total < 0:
                        raise ValueError("JSON API total count cannot be negative")
            if total is not None and len(positions) >= total:
                positions_complete = True
                break

            if offset + 1 < max_pages:
                time.sleep(delay)

        if aggregate_document is None or last_response is None:
            raise ValueError("JSON API pagination returned no response")
        _set_path(aggregate_document, list_path, positions)
        aggregate_document["_radar"] = {
            "positions_complete": positions_complete,
        }
        body = _canonical_json(aggregate_document)
        return FetchedPage(
            canonical_url=canonicalize_url(endpoint),
            body=body,
            content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            http_status=last_response.status_code,
            etag=None,
        )
