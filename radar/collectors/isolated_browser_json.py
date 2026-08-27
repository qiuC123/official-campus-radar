import copy
import json
import math

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from radar.collectors.ats_json_api import AtsJsonApiSourceAdapter, _host
from radar.collectors.json_api import JsonApiSourceAdapter, _path_value
from radar.models import OfficialSource


class IsolatedBrowserJsonSourceAdapter(JsonApiSourceAdapter):
    """Narrow production-browser exception for China Unicom's public job page."""

    organization_name = "中国联合网络通信集团有限公司"
    entry_url = "https://zglt.zhaopin.com/scjobs/index.html"
    endpoint = "https://fe.zhaopin.com/grace/api/dsc/search-job-list"
    allowed_browser_keys = {
        "entry_url",
        "frontend_page_size",
        "navigation_timeout_ms",
        "response_timeout_ms",
    }

    @classmethod
    def validate_source_config(cls, source: OfficialSource) -> None:
        if source.organization.name != cls.organization_name:
            raise ValueError("isolated browser adapter is restricted to China Unicom")
        if source.source_type != OfficialSource.SourceType.ATS:
            raise ValueError("isolated browser adapter requires source_type=ats")
        if _host(source.source_url) != "zglt.zhaopin.com":
            raise ValueError("isolated browser adapter requires the reviewed ATS host")
        if str(source.parser_config.get("endpoint", "")).strip() != cls.endpoint:
            raise ValueError("isolated browser adapter requires the reviewed endpoint")

        AtsJsonApiSourceAdapter.validate_source_config(source)
        config = source.parser_config
        if str(config.get("method", "")).upper() != "POST":
            raise ValueError("isolated browser adapter requires POST")
        if str(config.get("body_encoding", "")).lower() != "json":
            raise ValueError("isolated browser adapter requires a JSON request body")
        pagination = config["pagination"]
        if (
            pagination.get("mode") != "page_index"
            or pagination.get("page_param") != "pageIndex"
            or pagination.get("size_param") != "pageSize"
            or pagination.get("start_page", 1) != 1
            or pagination.get("page_size") != 100
            or pagination.get("max_pages") != 40
        ):
            raise ValueError("isolated browser adapter requires reviewed pagination")
        body = config.get("body")
        if not isinstance(body, dict) or body.get("pageIndex") != 1:
            raise ValueError("isolated browser adapter requires the reviewed body")
        if body.get("pageSize") != pagination["page_size"]:
            raise ValueError("isolated browser body and pagination page sizes differ")

        browser_config = config.get("isolated_browser")
        if not isinstance(browser_config, dict):
            raise ValueError("isolated_browser configuration is required")
        unexpected = set(browser_config) - cls.allowed_browser_keys
        if unexpected:
            raise ValueError(
                "isolated_browser contains forbidden settings: "
                + ", ".join(sorted(unexpected))
            )
        if str(browser_config.get("entry_url", "")).strip() != cls.entry_url:
            raise ValueError("isolated_browser.entry_url must be the reviewed public page")
        if browser_config.get("frontend_page_size") != 11:
            raise ValueError("isolated_browser.frontend_page_size must be 11")
        for name in ("navigation_timeout_ms", "response_timeout_ms"):
            value = browser_config.get(name)
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1_000
                or value > 120_000
            ):
                raise ValueError(f"isolated_browser.{name} must be 1000..120000")

    @staticmethod
    def _integer_at(payload: dict, path: str) -> int:
        missing = object()
        raw_value = _path_value(payload, path, missing)
        if raw_value is missing or isinstance(raw_value, bool):
            raise ValueError(f"browser JSON path {path!r} must resolve to an integer")
        try:
            value = int(raw_value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"browser JSON path {path!r} must resolve to an integer"
            ) from error
        if str(value) != str(raw_value) and not isinstance(raw_value, int):
            raise ValueError(f"browser JSON path {path!r} must resolve to an integer")
        if value < 0:
            raise ValueError("browser JSON total cannot be negative")
        return value

    @classmethod
    def _validate_payload(cls, config: dict, payload: object) -> list[object]:
        if not isinstance(payload, dict):
            raise ValueError("browser JSON response must be an object")
        if "_radar" in payload:
            raise ValueError("browser JSON response contains reserved _radar metadata")
        missing = object()
        success = config.get("success")
        if isinstance(success, dict):
            actual = _path_value(payload, str(success["path"]).strip(), missing)
            if actual is missing or str(actual) != str(success["expect"]):
                raise ValueError("browser JSON success check failed")
        rows = _path_value(payload, str(config["list_path"]).strip(), missing)
        if rows is missing or not isinstance(rows, list):
            raise ValueError("browser JSON list_path must resolve to a list")
        return rows

    def _collect_payloads(self, source: OfficialSource) -> tuple[list[dict], int]:
        config = source.parser_config
        browser_config = config["isolated_browser"]
        endpoint = str(config["endpoint"]).strip()
        expected_body = copy.deepcopy(config["body"])
        pagination = config["pagination"]
        configured_page_size = pagination["page_size"]
        frontend_page_size = browser_config["frontend_page_size"]
        max_pages = pagination["max_pages"]
        delay_ms = round(float(config.get("request_delay_seconds", 1)) * 1000)
        routed_pages: list[int] = []

        def is_target_response(response) -> bool:
            return response.url == endpoint and response.request.method == "POST"

        def route_request(route, request) -> None:
            try:
                request_body = request.post_data_json
            except Exception as error:
                raise ValueError("browser request body is not JSON") from error
            if not isinstance(request_body, dict):
                raise ValueError("browser request body must be an object")
            page_index = request_body.get("pageIndex")
            page_size = request_body.get("pageSize")
            if not isinstance(page_index, int) or isinstance(page_index, bool):
                raise ValueError("browser request pageIndex is invalid")
            if page_size != frontend_page_size:
                raise ValueError("browser frontend pageSize changed unexpectedly")
            reviewed_body = copy.deepcopy(request_body)
            reviewed_body["pageIndex"] = expected_body["pageIndex"]
            reviewed_body["pageSize"] = expected_body["pageSize"]
            if reviewed_body != expected_body:
                raise ValueError("browser request scope changed unexpectedly")
            request_body["pageSize"] = configured_page_size
            routed_pages.append(page_index)
            route.continue_(
                post_data=json.dumps(
                    request_body,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )

        payloads: list[dict] = []
        status = 200
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=["--no-proxy-server"],
                )
                context = browser.new_context(
                    service_workers="block",
                    accept_downloads=False,
                )
                try:
                    page = context.new_page()
                    page.route(endpoint, route_request)
                    with page.expect_response(
                        is_target_response,
                        timeout=browser_config["response_timeout_ms"],
                    ) as response_info:
                        page.goto(
                            browser_config["entry_url"],
                            wait_until="domcontentloaded",
                            timeout=browser_config["navigation_timeout_ms"],
                        )
                    response = response_info.value
                    status = response.status
                    if status >= 300:
                        raise ValueError(f"browser JSON returned HTTP {status}")
                    first_payload = response.json()
                    first_rows = self._validate_payload(config, first_payload)
                    if routed_pages != [1]:
                        raise ValueError("browser initial request did not use page 1")
                    if len(first_rows) > configured_page_size:
                        raise ValueError("browser JSON page exceeds configured page size")
                    payloads.append(first_payload)

                    total = self._integer_at(first_payload, str(config["total_path"]))
                    total_pages = max(1, math.ceil(total / configured_page_size))
                    if total_pages > max_pages:
                        raise ValueError("browser JSON exceeds configured max_pages")

                    next_button = page.get_by_label("Go to next page", exact=True)
                    for expected_page in range(2, total_pages + 1):
                        page.wait_for_timeout(delay_ms)
                        if next_button.count() != 1:
                            raise ValueError("browser next-page control is unavailable")
                        with page.expect_response(
                            is_target_response,
                            timeout=browser_config["response_timeout_ms"],
                        ) as response_info:
                            next_button.click()
                        response = response_info.value
                        status = response.status
                        if status >= 300:
                            raise ValueError(f"browser JSON returned HTTP {status}")
                        payload = response.json()
                        rows = self._validate_payload(config, payload)
                        if routed_pages != list(range(1, expected_page + 1)):
                            raise ValueError("browser pagination request sequence changed")
                        if len(rows) > configured_page_size:
                            raise ValueError(
                                "browser JSON page exceeds configured page size"
                            )
                        current_total = self._integer_at(
                            payload, str(config["total_path"])
                        )
                        if current_total != total:
                            raise ValueError("browser JSON total changed during collection")
                        payloads.append(payload)
                finally:
                    context.close()
                    browser.close()
        except PlaywrightTimeoutError as error:
            raise ValueError("isolated browser timed out") from error
        return payloads, status

    def fetch(self, source: OfficialSource):
        self.validate_source_config(source)
        config = source.parser_config
        payloads, status = self._collect_payloads(source)
        if not payloads:
            raise ValueError("isolated browser returned no JSON payload")

        positions: list[object] = []
        aggregate_document = copy.deepcopy(payloads[0])
        for payload in payloads:
            positions.extend(copy.deepcopy(self._validate_payload(config, payload)))
        total = self._integer_at(payloads[0], str(config["total_path"]))
        expected_pages = max(1, math.ceil(total / config["pagination"]["page_size"]))
        if len(payloads) != expected_pages:
            raise ValueError("isolated browser returned an incomplete page sequence")
        positions_complete = len(positions) >= total
        return self._finalize_fetched_page(
            config=config,
            endpoint=str(config["endpoint"]).strip(),
            aggregate_document=aggregate_document,
            positions=positions,
            positions_complete=positions_complete,
            http_status=status,
        )
