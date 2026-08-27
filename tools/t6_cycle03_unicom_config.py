import copy


COMPANY = "中国联合网络通信集团有限公司"
STALE_HEADERS = {
    "Accept": "application/json",
    "Origin": "https://webapp.zhaopin.com",
    "Referer": "https://webapp.zhaopin.com/",
}
INCOMPLETE_HEADERS = {"Accept": "application/json"}
MINIMAL_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
}
SUCCESS_GUARD = {"path": "code", "expect": 200}


def corrected_parser_config(parser_config: dict) -> dict:
    """Return the reviewed Cycle 03 China Unicom configuration."""

    config = copy.deepcopy(parser_config)
    if config.get("headers") not in (STALE_HEADERS, INCOMPLETE_HEADERS):
        raise ValueError("中国联通基线请求头与 Cycle 02 现场不一致")
    if config.get("success") != SUCCESS_GUARD:
        raise ValueError("中国联通业务成功条件与 Cycle 02 现场不一致")
    pagination = config.get("pagination")
    if not isinstance(pagination, dict) or pagination.get("page_size") != 100:
        raise ValueError("中国联通基线 page_size 不是 100")

    config["headers"] = MINIMAL_HEADERS
    return config
