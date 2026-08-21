import copy
import hashlib
import json
import re
import time
from datetime import date
from urllib.parse import urlparse

import requests

from radar.collectors.base import (
    FieldEvidenceValue,
    FetchedPage,
    NoticeCandidate,
    PositionCandidate,
)
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

        list_path = str(config.get("list_path", "")).strip()
        if not list_path:
            raise ValueError("JSON API list_path is required")
        if list_path == "_radar" or list_path.startswith("_radar."):
            raise ValueError("JSON API list_path cannot use the reserved _radar key")
        if any(not part for part in list_path.split(".")):
            raise ValueError("JSON API list_path must be a dotted object path")

        if not isinstance(config.get("params", {}), dict):
            raise ValueError("JSON API params must be an object")

        field_map = config.get("field_map")
        if not isinstance(field_map, dict):
            raise ValueError("JSON API field_map must be an object")
        for name in ("position_key", "title"):
            if not str(field_map.get(name, "")).strip():
                raise ValueError(f"JSON API field_map.{name} is required")

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

        notice_url = urlparse(str(notice["official_notice_url"]).strip())
        source_url = urlparse(source.source_url)
        if (
            notice_url.scheme != "https"
            or not notice_url.hostname
            or notice_url.hostname.lower()
            != (source_url.hostname or "").lower()
        ):
            raise ValueError(
                "JSON API notice.official_notice_url must use HTTPS on the source host"
            )

        for name in ("published_on", "deadline"):
            fixed_value = str(notice.get(name, "")).strip()
            if not (fixed_value or str(field_map.get(name, "")).strip()):
                raise ValueError(
                    f"JSON API {name} requires a fixed notice value or field path"
                )
            if fixed_value:
                try:
                    date.fromisoformat(fixed_value)
                except ValueError as error:
                    raise ValueError(
                        f"JSON API notice.{name} must be an ISO date"
                    ) from error

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
        for name in ("page_param", "size_param"):
            if not str(pagination.get(name, "")).strip():
                raise ValueError(f"JSON API pagination.{name} is required")
        start_page = pagination.get("start_page", 1)
        if (
            not isinstance(start_page, int)
            or isinstance(start_page, bool)
            or start_page < 0
        ):
            raise ValueError(
                "JSON API pagination.start_page must be a non-negative integer"
            )

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
        page_param = str(pagination["page_param"]).strip()
        size_param = str(pagination["size_param"]).strip()
        page_size = pagination["page_size"]
        start_page = pagination.get("start_page", 1)
        max_pages = pagination["max_pages"]
        delay = config.get("request_delay_seconds", 1)
        list_path = str(config["list_path"]).strip()
        total_path = str(config.get("total_path", "")).strip()
        base_params = config.get("params", {})

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
                "allow_redirects": False,
                "headers": headers,
                "timeout": self.timeout_seconds,
            }
            if method == "GET":
                request_kwargs["params"] = request_values
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
            "list_path": list_path,
            "notice": copy.deepcopy(config["notice"]),
            "field_map": copy.deepcopy(config["field_map"]),
            "valid_values": copy.deepcopy(config.get("valid_values", {})),
        }
        body = _canonical_json(aggregate_document)
        return FetchedPage(
            canonical_url=canonicalize_url(endpoint),
            body=body,
            content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            http_status=last_response.status_code,
            etag=None,
        )

    @staticmethod
    def _parse_date(value: object) -> date | None:
        if isinstance(value, date):
            return value
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return date.fromisoformat(text)
        except ValueError:
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

    def extract(
        self, source: OfficialSource, page: FetchedPage
    ) -> list[NoticeCandidate]:
        if page.not_modified:
            return []
        document = json.loads(page.body)
        if not isinstance(document, dict):
            raise ValueError("JSON API canonical document must be an object")
        metadata = document.get("_radar")
        if not isinstance(metadata, dict):
            raise ValueError("JSON API canonical document is missing adapter metadata")
        list_path = str(metadata.get("list_path", "")).strip()
        notice_config = metadata.get("notice")
        field_map = metadata.get("field_map")
        valid_values = metadata.get("valid_values", {})
        if not list_path or not isinstance(notice_config, dict):
            raise ValueError("JSON API canonical document has invalid notice metadata")
        if not isinstance(field_map, dict) or not isinstance(valid_values, dict):
            raise ValueError("JSON API canonical document has invalid field metadata")
        rows = _path_value(document, list_path)
        if not isinstance(rows, list):
            raise ValueError("JSON API canonical list_path must resolve to a list")

        positions: list[PositionCandidate] = []
        retained_rows: list[tuple[int, dict]] = []
        filtered_invalid = 0
        skipped_missing_identity = 0
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            valid = True
            for field_name, allowed_values in valid_values.items():
                field_path = str(field_map.get(field_name, "")).strip()
                if not field_path or not isinstance(allowed_values, list):
                    valid = False
                    break
                if _path_value(row, field_path) not in allowed_values:
                    valid = False
                    break
            if not valid:
                filtered_invalid += 1
                continue

            position_key_path = str(field_map["position_key"]).strip()
            raw_position_key = _path_value(row, position_key_path, "")
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
            raw_title = _path_value(row, title_path, "")
            raw_location = (
                _path_value(row, location_path, "") if location_path else ""
            )
            raw_description = (
                _path_value(row, raw_text_path, "") if raw_text_path else ""
            )
            raw_application_url = (
                _path_value(row, application_path, "")
                if application_path
                else ""
            )
            title = self._raw_text(raw_title).strip()
            location = self._raw_text(raw_location).strip()
            application_url = self._raw_text(raw_application_url).strip() or None
            if application_url:
                application_url = canonicalize_url(application_url)

            position_evidence: dict[str, FieldEvidenceValue] = {
                "position_title": FieldEvidenceValue(
                    self._raw_text(raw_title),
                    f"{base_locator}.{title_path}",
                    title,
                )
            }
            if location_path:
                position_evidence["location"] = FieldEvidenceValue(
                    self._raw_text(raw_location),
                    f"{base_locator}.{location_path}",
                    location,
                )
            if application_path and application_url:
                position_evidence["application_link"] = FieldEvidenceValue(
                    self._raw_text(raw_application_url),
                    f"{base_locator}.{application_path}",
                    application_url,
                )
            positions.append(
                PositionCandidate(
                    title=title,
                    location_text=location,
                    raw_text=self._raw_text(raw_description),
                    application_url=application_url,
                    locator=base_locator,
                    application_locator=(
                        f"{base_locator}.{application_path}"
                        if application_path
                        else ""
                    ),
                    position_key=position_key,
                    field_evidence=position_evidence,
                )
            )
            retained_rows.append((index, row))

        def notice_text(field_name: str) -> tuple[str, str]:
            raw_value = notice_config.get(field_name, "")
            return (
                self._raw_text(raw_value).strip(),
                f"$._radar.notice.{field_name}",
            )

        def notice_date(field_name: str) -> tuple[date | None, FieldEvidenceValue]:
            if str(notice_config.get(field_name, "")).strip():
                raw_value = notice_config[field_name]
                locator = f"$._radar.notice.{field_name}"
            else:
                field_path = str(field_map.get(field_name, "")).strip()
                if retained_rows:
                    index, row = retained_rows[0]
                    raw_value = _path_value(row, field_path, "")
                    locator = f"$.{list_path}[{index}].{field_path}"
                else:
                    raw_value = ""
                    locator = f"$._radar.field_map.{field_name}"
            parsed_date = self._parse_date(raw_value)
            parsed_value = parsed_date.isoformat() if parsed_date else ""
            return parsed_date, FieldEvidenceValue(
                self._raw_text(raw_value), locator, parsed_value
            )

        title, title_locator = notice_text("title")
        recruitment_type, recruitment_type_locator = notice_text(
            "recruitment_type"
        )
        target_audience, target_audience_locator = notice_text(
            "target_audience"
        )
        notice_url, notice_url_locator = notice_text("official_notice_url")
        notice_url = canonicalize_url(notice_url)
        published_on, published_evidence = notice_date("published_on")
        deadline, deadline_evidence = notice_date("deadline")
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
            "notice_url": FieldEvidenceValue(
                self._raw_text(notice_config.get("official_notice_url", "")),
                notice_url_locator,
                notice_url,
            ),
        }
        return [
            NoticeCandidate(
                title=title,
                official_notice_url=notice_url,
                recruitment_type=recruitment_type,
                target_audience=target_audience,
                published_on=published_on,
                deadline=deadline,
                withdrawn=False,
                evidence_excerpt=(
                    f"rows={len(rows)} retained={len(positions)} "
                    f"skipped_missing_identity={skipped_missing_identity} "
                    f"filtered_invalid={filtered_invalid}"
                ),
                positions=tuple(positions),
                field_locators={
                    name: evidence.locator
                    for name, evidence in field_evidence.items()
                },
                identity_key=self._raw_text(
                    notice_config.get("identity_key", "")
                ).strip(),
                field_evidence=field_evidence,
                positions_complete=bool(
                    metadata.get("positions_complete", False)
                ),
            )
        ]
