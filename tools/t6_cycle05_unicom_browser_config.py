import copy

from tools.t6_cycle03_unicom_config import COMPANY, MINIMAL_HEADERS, SUCCESS_GUARD


EXPECTED_ADAPTER = "ats_json_api"
NEW_ADAPTER = "isolated_browser_json"
ENDPOINT = "https://fe.zhaopin.com/grace/api/dsc/search-job-list"
ENTRY_URL = "https://zglt.zhaopin.com/scjobs/index.html"
BROWSER_CONFIG = {
    "entry_url": ENTRY_URL,
    "frontend_page_size": 11,
    "navigation_timeout_ms": 30_000,
    "response_timeout_ms": 30_000,
}


def browser_parser_config(parser_config: dict) -> dict:
    """Return the reviewed Cycle 05 isolated-browser configuration."""

    config = copy.deepcopy(parser_config)
    if config.get("endpoint") != ENDPOINT:
        raise ValueError("中国联通基线端点与 Cycle 04 证据不一致")
    if config.get("headers") != MINIMAL_HEADERS:
        raise ValueError("中国联通基线请求头与 Cycle 03 现场不一致")
    if config.get("success") != SUCCESS_GUARD:
        raise ValueError("中国联通业务成功条件与 Cycle 03 现场不一致")
    pagination = config.get("pagination")
    if not isinstance(pagination, dict) or pagination != {
        "max_pages": 40,
        "mode": "page_index",
        "page_param": "pageIndex",
        "page_size": 100,
        "size_param": "pageSize",
        "start_page": 1,
        "total_kind": "items",
    }:
        raise ValueError("中国联通分页基线与 Cycle 04 现场不一致")
    body = config.get("body")
    if not isinstance(body, dict) or body.get("orgNumbers") != ["105347"]:
        raise ValueError("中国联通组织范围与准入证据不一致")

    config["batch"]["title"] = "中国联合网络通信集团有限公司校园招聘"
    config["batch"]["target_audience"] = "2027届"
    config["isolated_browser"] = copy.deepcopy(BROWSER_CONFIG)
    return config
