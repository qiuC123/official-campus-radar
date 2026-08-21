from urllib.parse import urlparse

from radar.models import OfficialSource


class JsonApiSourceAdapter:
    max_page_limit = 100

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
