from __future__ import annotations

import copy
import json
from urllib.parse import quote


PARTITIONED_COMPANIES = ("京东", "大疆创新", "美团", "腾讯", "vivo")

VIVO_PORTAL = "https://hr-campus.vivo.com/jobs"
VIVO_PROJECTS = (
    (
        "1",
        "蓝极星计划",
        "official-project:vivo:blue-star",
        "vivo 2027 届蓝极星计划",
        "autumn",
        "2027届",
    ),
    (
        "2",
        "秋季校园招聘",
        "phase-02:p13",
        "vivo 2027 届秋季校园招聘",
        "autumn",
        "2027届",
    ),
    (
        "7",
        "日常实习生",
        "official-project:vivo:daily-internship",
        "vivo 日常实习生招聘",
        "internship",
        "在校生",
    ),
    (
        "8",
        "暑期实习生",
        "official-project:vivo:summer-internship",
        "vivo 暑期实习生招聘",
        "internship",
        "在校生",
    ),
)


def _vivo_project_url(project_id: str, label: str) -> str:
    selection = json.dumps(
        [{"id": project_id, "label": label}],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"{VIVO_PORTAL}?1={quote(selection, safe='')}"


VIVO_PROJECT_URLS = {
    identity_key: _vivo_project_url(project_id, label)
    for project_id, label, identity_key, _, _, _ in VIVO_PROJECTS
}

TENCENT_PARTITION_AVAILABILITY_PROBES = [
    {
        "identity_key": "official-project:tencent:project:9",
        "mode": "browser_text",
        "url": "https://join.qq.com/post.html?query=p_9",
        "timeout_seconds": 30,
        "ready_text_any": ["AI产品经理培训生", "已截止简历投递"],
        "closed_text_any": ["AI产品经理培训生项目已截止简历投递"],
        "open_text_any": [],
    }
]


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
    graduate_audience = "毕业时间为2026年1月至2027年12月"
    return [
        {
            "batch": _batch(
                identity_key="official-project:tencent:project:1",
                title="腾讯应届毕业生招聘",
                official_page_url=portal,
                recruitment_type="campus_recruitment",
                target_audience=graduate_audience,
            ),
            "row_filters": [{"path": "projectId", "equals_any": [1]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:tencent:project:2",
                title="腾讯 2026 应届实习招聘",
                official_page_url=portal,
                recruitment_type="internship",
                target_audience="毕业时间为2026年9月至2027年12月",
            ),
            "row_filters": [{"path": "projectId", "equals_any": [2]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:tencent:projects:4-12",
                title="腾讯日常实习招聘",
                official_page_url=portal,
                recruitment_type="internship",
                target_audience="全体在校生",
            ),
            "row_filters": [{"path": "projectId", "equals_any": [4, 12]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:tencent:project:14",
                title="腾讯青云计划（应届生）",
                official_page_url=portal,
                recruitment_type="special_program",
                target_audience=graduate_audience,
            ),
            "row_filters": [{"path": "projectId", "equals_any": [14]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:tencent:project:20",
                title="腾讯青云计划（实习生）",
                official_page_url=portal,
                recruitment_type="internship",
                target_audience="毕业时间为2026年9月以后",
            ),
            "row_filters": [{"path": "projectId", "equals_any": [20]}],
        },
        {
            "batch": _batch(
                identity_key="official-project:tencent:project:9",
                title="腾讯 AI 产品经理培训生",
                official_page_url=portal,
                recruitment_type="special_program",
                target_audience=graduate_audience,
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


def _geely_partitions(portal: str) -> list[dict]:
    return [
        {
            "batch": _batch(
                identity_key="official-project:geely:2027-autumn",
                title="吉利控股 2027 届秋季校园招聘",
                official_page_url=portal,
                recruitment_type="autumn",
                target_audience="2027届",
            ),
            "row_filters": [
                {
                    "path": "customFields[].value",
                    "contains_any": ["2027届秋招"],
                }
            ],
        },
        {
            "batch": _batch(
                identity_key="official-project:geely:2027-internship",
                title="吉利控股 2027 届实习生招聘",
                official_page_url=portal,
                recruitment_type="internship",
                target_audience="在校生",
            ),
            "row_filters": [
                {
                    "path": "customFields[].value",
                    "contains_any": ["2027届实习生"],
                }
            ],
        },
    ]


def _vivo_partitions(portal: str) -> list[dict]:
    del portal
    return [
        {
            "batch": _batch(
                identity_key=identity_key,
                title=title,
                official_page_url=VIVO_PROJECT_URLS[identity_key],
                recruitment_type=recruitment_type,
                target_audience=target_audience,
            ),
            "row_filters": [
                {"path": "ClassificationOne", "equals_any": [label]}
            ],
        }
        for _, label, identity_key, title, recruitment_type, target_audience
        in VIVO_PROJECTS
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
    "吉利控股": {
        "adapter": "moka_public_api",
        "org_id": "geely",
        "site_id": 78436,
        "legacy_site_ids": (98148,),
        "base_identity": "phase-02:p16",
        "factory": _geely_partitions,
    },
    "vivo": {
        "adapter": "json_api",
        "endpoint": "https://hr-campus.vivo.com/api/Jobad/GetJobAdPageList",
        "base_identity": "phase-02:p13",
        "factory": _vivo_partitions,
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
    else:
        accepted_site_ids = {
            contract["site_id"],
            *contract.get("legacy_site_ids", ()),
        }
        if (
            parser_config.get("org_id") != contract["org_id"]
            or parser_config.get("site_id") not in accepted_site_ids
        ):
            raise ValueError(f"unexpected Moka tenant for {company}")
    portal = str(batch.get("official_page_url") or "").strip()
    if not portal.startswith("https://"):
        raise ValueError(f"missing official portal for {company}")
    result = copy.deepcopy(parser_config)
    if company == "吉利控股":
        portal = (
            "https://campus.geely.com/campus-recruitment/geely/78436"
            "?locale=zh-CN#/jobs"
        )
        result["site_id"] = 78436
        result["max_pages"] = 30
        result["row_filters"] = [
            {
                "path": "customFields[].value",
                "contains_any": ["2027届秋招", "2027届实习生"],
            }
        ]
        result["batch"] = _batch(
            identity_key="phase-02:p16",
            title="吉利控股 2027 届校园招聘",
            official_page_url=portal,
            recruitment_type="autumn",
            target_audience="2027届及在校生",
        )
    if company == "vivo":
        body = result.get("body")
        if not isinstance(body, dict):
            raise ValueError("missing JSON request body for vivo")
        body["ClassificationOne"] = []
        display_fields = body.get("DisplayFields")
        if not isinstance(display_fields, list):
            raise ValueError("missing DisplayFields for vivo")
        if "ClassificationOne" not in display_fields:
            display_fields.append("ClassificationOne")
        result["row_filters"] = []
        result["partition_coverage"] = {
            "request_path": "ClassificationOne",
            "row_path": "ClassificationOne",
        }
    result["batch_partitions"] = contract["factory"](portal)
    if company == "腾讯":
        body = result.get("body")
        if not isinstance(body, dict):
            raise ValueError("missing JSON request body for 腾讯")
        body["projectMappingIdList"] = [1, 2, 104, 14, 20, 9]
        result["partition_availability_probes"] = copy.deepcopy(
            TENCENT_PARTITION_AVAILABILITY_PROBES
        )
    return result
