from __future__ import annotations

import copy


PARTITIONED_COMPANIES = ("京东", "大疆创新", "美团", "腾讯")


def _batch(
    *,
    identity_key: str,
    title: str,
    official_page_url: str,
    recruitment_type: str,
    target_audience: str,
) -> dict:
    return {
        "identity_key": identity_key,
        "title": title,
        "official_page_url": official_page_url,
        "recruitment_type": recruitment_type,
        "target_audience": target_audience,
        "published_on": "",
        "deadline": "",
    }


def _jd_partitions(portal: str) -> list[dict]:
    audience = "2026年10月至2027年9月毕业的应届毕业生"
    return [
        {
            "batch": _batch(
                identity_key="official-project:jd:plan:56",
                title="京东 JDS-新星计划",
                official_page_url=portal,
                recruitment_type="special_program",
                target_audience=audience,
            ),
            "row_filters": [{"path": "planId", "equals_any": [56]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:jd:plan:57",
                title="京东 TET-管理培训生",
                official_page_url=portal,
                recruitment_type="special_program",
                target_audience=audience,
            ),
            "row_filters": [{"path": "planId", "equals_any": [57]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:jd:plan:58",
                title="京东 新锐之星",
                official_page_url=portal,
                recruitment_type="special_program",
                target_audience=audience,
            ),
            "row_filters": [{"path": "planId", "equals_any": [58]}],
        },
    ]


def _tencent_partitions(portal: str) -> list[dict]:
    audience = "毕业时间为2026年1月至2027年12月"
    return [
        {
            "batch": _batch(
                identity_key="official-project:tencent:project:1",
                title="腾讯应届毕业生招聘",
                official_page_url=portal,
                recruitment_type="campus_recruitment",
                target_audience=audience,
            ),
            "row_filters": [{"path": "projectId", "equals_any": [1]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:tencent:project:14",
                title="腾讯青云计划（应届生）",
                official_page_url=portal,
                recruitment_type="special_program",
                target_audience=audience,
            ),
            "row_filters": [{"path": "projectId", "equals_any": [14]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:tencent:project:9",
                title="腾讯 AI 产品经理培训生",
                official_page_url=portal,
                recruitment_type="special_program",
                target_audience=audience,
            ),
            "row_filters": [{"path": "projectId", "equals_any": [9]}],
        },
    ]


def _meituan_partitions(portal: str) -> list[dict]:
    audience = "在校生及实习生"
    return [
        {
            "batch": _batch(
                identity_key="official-project:meituan:special:6",
                title="美团日常实习招聘",
                official_page_url=portal,
                recruitment_type="internship",
                target_audience=audience,
            ),
            "row_filters": [{"path": "jobSpecialCode", "equals_any": ["6"]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:meituan:special:8",
                title="美团 LongCat 实习招聘",
                official_page_url=portal,
                recruitment_type="internship",
                target_audience=audience,
            ),
            "row_filters": [{"path": "jobSpecialCode", "equals_any": ["8"]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:meituan:special:3",
                title="美团北斗实习招聘",
                official_page_url=portal,
                recruitment_type="internship",
                target_audience=audience,
            ),
            "row_filters": [{"path": "jobSpecialCode", "equals_any": ["3"]}],
        },
    ]


def _dji_partitions(portal: str) -> list[dict]:
    return [
        {
            "batch": _batch(
                identity_key="official-project:dji:tuojiangzhe:2027",
                title="大疆创新 2027 拓疆者校园招聘",
                official_page_url=portal,
                recruitment_type="campus_recruitment",
                target_audience="2027届毕业生",
            ),
            "row_filters": [
                {"path": "attribute_id", "not_equals_any": [132985]}
            ],
        },
        {
            "batch": _batch(
                identity_key="official-project:dji:digital-management:2027",
                title="大疆创新数字管理构建者计划",
                official_page_url=portal,
                recruitment_type="special_program",
                target_audience="2027届及优秀2026届理工科毕业生",
            ),
            "row_filters": [{"path": "attribute_id", "equals_any": [132985]}],
        },
    ]


SOURCE_CONTRACTS = {
    "京东": {
        "adapter": "json_api",
        "endpoint": "https://campus.jd.com/api/wx/position/page?type=present",
        "base_identity": "phase-02:p07",
        "factory": _jd_partitions,
    },
    "腾讯": {
        "adapter": "json_api",
        "endpoint": "https://join.qq.com/api/v1/position/searchPosition",
        "base_identity": "phase-02:p01",
        "factory": _tencent_partitions,
    },
    "美团": {
        "adapter": "json_api",
        "endpoint": "https://job.meituan.com/api/official/job/getJobList",
        "base_identity": "phase-02:p08",
        "factory": _meituan_partitions,
    },
    "大疆创新": {
        "adapter": "moka_public_api",
        "org_id": "dji",
        "site_id": 143359,
        "base_identity": "phase-02:p14",
        "factory": _dji_partitions,
    },
}


def partitioned_parser_config(
    company: str,
    adapter_name: str,
    parser_config: dict,
) -> dict:
    contract = SOURCE_CONTRACTS.get(company)
    if contract is None:
        raise ValueError(f"unsupported partitioned company: {company}")
    if adapter_name != contract["adapter"]:
        raise ValueError(f"unexpected adapter for {company}")
    if not isinstance(parser_config, dict):
        raise ValueError(f"parser config for {company} must be an object")
    batch = parser_config.get("batch")
    if not isinstance(batch, dict):
        raise ValueError(f"parser config for {company} has no base batch")
    if batch.get("identity_key") != contract["base_identity"]:
        raise ValueError(f"unexpected base batch identity for {company}")
    if adapter_name == "json_api":
        if parser_config.get("endpoint") != contract["endpoint"]:
            raise ValueError(f"unexpected endpoint for {company}")
    elif (
        parser_config.get("org_id") != contract["org_id"]
        or parser_config.get("site_id") != contract["site_id"]
    ):
        raise ValueError(f"unexpected Moka tenant for {company}")
    portal = str(batch.get("official_page_url") or "").strip()
    if not portal.startswith("https://"):
        raise ValueError(f"missing official portal for {company}")
    result = copy.deepcopy(parser_config)
    result["batch_partitions"] = contract["factory"](portal)
    return result
