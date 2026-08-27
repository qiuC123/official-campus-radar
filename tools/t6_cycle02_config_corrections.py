import copy


CORRECTED_COMPANIES = (
    "理想汽车",
    "美团",
    "中国联合网络通信集团有限公司",
)


def corrected_parser_config(company: str, parser_config: dict) -> dict:
    """Return one reviewed T6 Cycle 02 correction without mutating its input."""
    config = copy.deepcopy(parser_config)
    if company == "理想汽车":
        pagination = config.get("pagination")
        if not isinstance(pagination, dict) or pagination.get("page_size") != 10:
            raise ValueError("理想汽车基线配置的 page_size 不是 10")
        pagination["page_size"] = 100
    elif company == "美团":
        body = config.get("body")
        expected = [
            {"code": "1", "subCode": []},
            {"code": "2", "subCode": []},
        ]
        if not isinstance(body, dict) or body.get("jobType") != expected:
            raise ValueError("美团基线配置的 jobType 与 Cycle 01 证据不一致")
        body["jobType"] = [{"code": "2", "subCode": []}]
    elif company == "中国联合网络通信集团有限公司":
        if config.get("success") != {"path": "code", "expect": 200}:
            raise ValueError("中国联通基线配置的 success 条件与 Cycle 01 证据不一致")
        config.pop("success")
    else:
        raise ValueError(f"不支持的 T6 Cycle 02 配置修正：{company}")
    return config
