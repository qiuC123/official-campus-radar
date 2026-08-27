import hashlib
import json
import re
from types import SimpleNamespace
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from radar.collectors.base import FetchedPage
from radar.collectors.json_api import JsonApiSourceAdapter, _canonical_json, _path_value
from radar.models import OfficialSource
from radar.services.normalization import canonicalize_url


class EmbeddedJobsAdapter(JsonApiSourceAdapter):
    """Turn two public server-rendered job formats into the JSON contract."""

    timeout_seconds = 15
    user_agent = "OfficialCampusRadar/0.1 (local low-frequency collector)"
    supported_transforms = {"apple_hydration", "gac_toyota_html"}

    @staticmethod
    def _host(url: str) -> str:
        return (urlparse(url).hostname or "").lower()

    @classmethod
    def _normalized_source(cls, source: OfficialSource):
        config = source.parser_config
        normalized_config = {
            "endpoint": source.source_url,
            "method": "GET",
            "params": {},
            "headers": config.get("headers", {"Accept": "text/html"}),
            "pagination": {
                "mode": "single",
                "page_size": 1,
                "max_pages": 1,
            },
            "list_path": config["list_path"],
            "total_path": config.get("total_path", ""),
            "batch": config["batch"],
            "field_map": config["field_map"],
            "row_filters": config.get("row_filters", []),
            "html_fields": config.get("html_fields", []),
        }
        return SimpleNamespace(
            parser_config=normalized_config,
            source_url=source.source_url,
            organization=SimpleNamespace(official_domain=cls._host(source.source_url)),
        )

    @classmethod
    def validate_source_config(cls, source: OfficialSource) -> None:
        config = source.parser_config
        if not isinstance(config, dict):
            raise ValueError("embedded jobs parser_config must be an object")
        transform = str(config.get("response_transform", "")).strip()
        if transform not in cls.supported_transforms:
            raise ValueError("embedded jobs response_transform is unsupported")
        JsonApiSourceAdapter.validate_source_config(cls._normalized_source(source))

    @staticmethod
    def _parse_apple_hydration(html: str) -> dict:
        match = re.search(
            r"window\.__staticRouterHydrationData\s*=\s*JSON\.parse\((\".*?\")\);?</script>",
            html,
            re.DOTALL,
        )
        if not match:
            raise ValueError("Apple hydration payload was not found")
        try:
            payload = json.loads(json.loads(match.group(1)))
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("Apple hydration payload is invalid JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("Apple hydration payload must be an object")
        return payload

    @staticmethod
    def _parse_gac_toyota(html: str, source_url: str) -> dict:
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
                    "href": urljoin(source_url, href),
                }
            )
        return {
            "jobs": jobs,
            "total": len(jobs),
            "pager_link_count": len(soup.select("div.pager a[href]")),
        }

    def fetch(self, source: OfficialSource) -> FetchedPage:
        self.validate_source_config(source)
        session = requests.Session()
        session.trust_env = False
        headers = {"User-Agent": self.user_agent}
        headers.update(source.parser_config.get("headers", {"Accept": "text/html"}))
        session.cookies.clear()
        response = session.get(
            source.source_url,
            headers=headers,
            timeout=self.timeout_seconds,
            allow_redirects=False,
        )
        if response.status_code >= 300:
            raise requests.HTTPError(f"HTTP {response.status_code}")
        transform = source.parser_config["response_transform"]
        if transform == "apple_hydration":
            document = self._parse_apple_hydration(response.text)
        else:
            document = self._parse_gac_toyota(response.text, source.source_url)
        list_path = source.parser_config["list_path"]
        rows = _path_value(document, list_path)
        if not isinstance(rows, list):
            raise ValueError("embedded jobs list_path must resolve to a list")
        document["_radar"] = {
            "positions_complete": True,
            "list_path": list_path,
            "batch": source.parser_config["batch"],
            "field_map": source.parser_config["field_map"],
            "valid_values": {},
            "row_filters": source.parser_config.get("row_filters", []),
            "html_fields": source.parser_config.get("html_fields", []),
            "pagination_total_kind": "items",
            "pagination_mode": "single",
        }
        body = _canonical_json(document)
        return FetchedPage(
            canonical_url=canonicalize_url(source.source_url),
            body=body,
            content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            http_status=response.status_code,
            etag=None,
        )
