import copy
import hashlib
import json
import re
from datetime import datetime
from types import SimpleNamespace
from urllib.parse import urlparse

from radar.collectors.base import FetchedPage
from radar.collectors.json_api import JsonApiSourceAdapter, _canonical_json
from radar.models import OfficialSource


MOKA_PUBLIC_API_HOST = "api.mokahr.com"
MOKA_PUBLIC_API_ROOT = "https://api.mokahr.com/api-platform/v1/jobs"
_ORG_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _belongs_to_domain(host: str, domain: str) -> bool:
    normalized = str(domain or "").strip().lower()
    return bool(normalized) and (
        host == normalized or host.endswith(f".{normalized}")
    )


def _location_text(locations: object) -> str:
    if not isinstance(locations, list):
        return ""
    labels: list[str] = []
    for location in locations:
        if not isinstance(location, dict):
            continue
        parts: list[str] = []
        for aliases in (
            ("province", "provinceName"),
            ("city", "cityName"),
            ("area", "areaName"),
        ):
            value = ""
            for name in aliases:
                raw_value = location.get(name)
                if raw_value is None:
                    continue
                candidate = str(raw_value).strip()
                if candidate:
                    value = candidate
                    break
            if value and value not in parts:
                parts.append(value)
        label = "·".join(parts)
        if not label:
            country = location.get("country")
            label = str(country).strip() if country is not None else ""
        if label and label not in labels:
            labels.append(label)
    return "、".join(labels)


def _date_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return text[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", text) else ""


class MokaPublicApiAdapter(JsonApiSourceAdapter):
    """Read a public Moka campus board through its documented jobs API."""

    @classmethod
    def _normalized_source(cls, source: OfficialSource):
        config = source.parser_config
        org_id = str(config["org_id"]).strip()
        batch = copy.deepcopy(config["batch"])
        normalized_config = {
            "endpoint": f"{MOKA_PUBLIC_API_ROOT}/{org_id}",
            "method": "GET",
            "params": {
                "mode": "campus",
                "siteId": config["site_id"],
            },
            "pagination": {
                "mode": "offset",
                "page_param": "offset",
                "size_param": "limit",
                "page_size": config.get("page_size", 50),
                "start_offset": 0,
                "max_pages": config.get("max_pages", 100),
                "total_kind": "items",
            },
            "list_path": "jobs",
            "total_path": "total",
            "html_fields": ["raw_text"],
            "batch": batch,
            "field_map": {
                "position_key": "id",
                "title": "title",
                "location": "_radar_location_text",
                "raw_text": "description",
                "updated_at": "_radar_updated_on",
                "is_valid": "status",
            },
            "valid_values": {"is_valid": ["open"]},
            "request_delay_seconds": config.get("request_delay_seconds", 1),
        }
        if config.get("batch_partitions"):
            normalized_config["batch_partitions"] = copy.deepcopy(
                config["batch_partitions"]
            )
        return SimpleNamespace(
            parser_config=normalized_config,
            source_url=source.source_url,
            organization=SimpleNamespace(official_domain=MOKA_PUBLIC_API_HOST),
        )

    @classmethod
    def validate_source_config(cls, source: OfficialSource) -> None:
        config = source.parser_config
        if not isinstance(config, dict):
            raise ValueError("Moka parser_config must be an object")
        org_id = str(config.get("org_id", "")).strip()
        if not _ORG_ID_RE.fullmatch(org_id):
            raise ValueError("Moka org_id must contain only letters, numbers, _ or -")
        site_id = config.get("site_id")
        if (
            not isinstance(site_id, int)
            or isinstance(site_id, bool)
            or site_id <= 0
        ):
            raise ValueError("Moka site_id must be a positive integer")
        if str(config.get("mode", "")).strip().lower() != "campus":
            raise ValueError("Moka mode must be campus")

        source_url = urlparse(str(source.source_url).strip())
        if source_url.scheme != "https" or not source_url.hostname:
            raise ValueError("Moka source URL must use HTTPS")
        entrypoint = str(getattr(source, "official_entrypoint_url", "") or "").strip()
        if not (
            urlparse(entrypoint).scheme == "https"
            and _belongs_to_domain(
                _host(entrypoint), source.organization.official_domain
            )
        ):
            raise ValueError(
                "Moka source requires an HTTPS official entrypoint on the organization domain"
            )

        batch = config.get("batch")
        if not isinstance(batch, dict):
            raise ValueError("Moka batch must be an object")
        official_page_url = str(batch.get("official_page_url", "")).strip()
        if (
            urlparse(official_page_url).scheme != "https"
            or _host(official_page_url) != (source_url.hostname or "").lower()
        ):
            raise ValueError(
                "Moka batch.official_page_url must use HTTPS on the source host"
            )

        JsonApiSourceAdapter.validate_source_config(cls._normalized_source(source))

    def fetch(self, source: OfficialSource) -> FetchedPage:
        self.validate_source_config(source)
        page = JsonApiSourceAdapter().fetch(self._normalized_source(source))
        document = json.loads(page.body)
        for row in document.get("jobs", []):
            if not isinstance(row, dict):
                continue
            row["_radar_location_text"] = _location_text(row.get("locations"))
            row["_radar_updated_on"] = _date_text(row.get("updatedAt"))
        body = _canonical_json(document)
        return FetchedPage(
            canonical_url=page.canonical_url,
            body=body,
            content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            http_status=page.http_status,
            etag=page.etag,
            not_modified=page.not_modified,
        )
