from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from radar.services.project_partitions import (  # noqa: E402
    PARTITIONED_COMPANIES,
    partitioned_parser_config,
)

LEDGER = ROOT / "tools" / "stable-sources-phase-02-t3.json"

HEADER = [
    "organization_name",
    "company_type",
    "industry",
    "official_domain",
    "source_type",
    "source_url",
    "official_entrypoint_url",
    "admission_evidence",
    "adapter_name",
    "parser_config",
    "is_active",
]

TYPE_CODES = {
    "民企": "private",
    "央国企": "state_owned",
    "外资": "foreign",
    "中外合资": "joint_venture",
}

SOURCE_META = {
    "P11": ("tools/api-acceptance-cycle-03.json", "pinduoduo", "互联网/科技", "pddglobalhr.com", "api", "json_api", "", "应届毕业生"),
    "P20": ("tools/api-acceptance-cycle-03.json", "li_auto", "汽车", "lixiang.com", "api", "json_api", "", "应届毕业生/实习生"),
    "S08": ("tools/api-acceptance-cycle-03.json", "crrc", "轨道交通/制造", "crrcgc.cc", "ats", "ats_json_api", "https://www.crrcgc.cc/", "应届毕业生"),
    "P13": ("tools/api-acceptance-cycle-06-beisen.json", "vivo_autumn_campus", "消费电子/科技", "vivo.com", "api", "json_api", "", "2027届"),
    "P08": ("tools/api-acceptance-cycle-07-meituan.json", "P08-C07", "互联网/科技", "meituan.com", "api", "json_api", "", "实习生"),
    "P06": ("tools/api-acceptance-cycle-11-public-family.json", "P06", "互联网/科技", "baidu.com", "api", "json_api", "", "应届毕业生"),
    "P07": ("tools/api-acceptance-cycle-11-public-family.json", "P07", "电商/物流/科技", "jd.com", "api", "json_api", "", "应届毕业生"),
    "P10": ("tools/api-acceptance-cycle-11-public-family.json", "P10", "互联网/游戏", "163.com", "api", "json_api", "", "应届毕业生"),
    "P18": ("tools/api-acceptance-cycle-11-public-family.json", "P18", "物流/供应链", "sf-express.com", "api", "json_api", "", "应届毕业生"),
    "P12": ("tools/api-acceptance-cycle-12-oppo.json", "P12", "消费电子/科技", "oppo.com", "api", "json_api", "", "应届毕业生"),
    "P01": ("tools/api-acceptance-cycle-13-tencent.json", "P01", "互联网/科技", "qq.com", "api", "json_api", "", "2027届"),
    "P15": ("tools/api-acceptance-cycle-15-catl.json", "P15", "新能源/制造", "catl.com", "ats", "moka_public_api", "https://talent.catl.com/", "2027届"),
    "P19": ("tools/api-acceptance-cycle-16-seven-sources.json", "P19", "新能源汽车/制造", "byd.com", "api", "json_api", "", "2027届"),
    "S03": ("tools/api-acceptance-cycle-16-seven-sources.json", "S03", "通信", "chinatelecom.com.cn", "api", "json_api", "", "应届毕业生"),
    "S04": ("tools/api-acceptance-cycle-16-seven-sources.json", "S04", "通信", "chinaunicom.com.cn", "ats", "ats_json_api", "https://www.chinaunicom.com.cn/46/menu01/528/column06", "2027届"),
    "F02": ("tools/api-acceptance-cycle-16-seven-sources.json", "F02", "电商/云计算", "amazon.jobs", "api", "json_api", "", "实习生"),
    "F06": ("tools/api-acceptance-cycle-16-seven-sources.json", "F06", "消费电子/科技", "apple.com", "website", "embedded_jobs", "", "实习生"),
    "J02": ("tools/api-acceptance-cycle-17-faw-midea-pagination.json", "J02", "汽车制造", "faw-vw.com", "ats", "ats_json_api", "https://www.faw-vw.com/home", "2026届"),
    "P17": ("tools/api-acceptance-cycle-17-faw-midea-pagination.json", "P17", "制造/家电", "midea.com", "api", "json_api", "", "实习生"),
    "P02": ("tools/api-acceptance-cycle-18-evidence-backfill.json", "P02", "旅游/互联网", "ctrip.com", "api", "json_api", "", "应届毕业生"),
    "P14": ("tools/api-acceptance-cycle-18-evidence-backfill.json", "P14", "智能硬件/机器人", "dji.com", "ats", "moka_public_api", "https://careers.dji.com/zh-CN/campus", "2027届"),
    "P16": ("tools/api-acceptance-cycle-18-evidence-backfill.json", "P16", "汽车制造", "geely.com", "ats", "moka_public_api", "https://campus.geely.com/", "应届毕业生"),
    "J04": ("tools/api-acceptance-cycle-18-evidence-backfill.json", "J04", "汽车制造", "dongfeng-nissan.com.cn", "api", "json_api", "", "实习生"),
    "F05": ("tools/api-acceptance-cycle-18-evidence-backfill.json", "F05", "汽车/工业技术", "bosch.com.cn", "ats", "ats_json_api", "https://www.bosch.com.cn/careers/job-offers/", "2027届"),
    "J03": ("tools/api-acceptance-cycle-18-evidence-backfill.json", "J03", "汽车制造", "gac-toyota.com.cn", "ats", "embedded_jobs", "https://www.gac-toyota.com.cn/", "应届毕业生"),
}

INTERNSHIP_KEYS = {"P08", "P17", "F02", "F06", "J04"}
UPDATED_FIELDS = {
    "P06": "updateDate",
    "P13": "ChangeDate",
    "P10": "updateTime",
    "P19": "updateTime",
    "S04": "job.modifiedTime",
    "P14": "updatedAt",
    "P15": "updatedAt",
    "P16": "updatedAt",
}


def _targets(document: dict) -> list[dict]:
    if isinstance(document.get("targets"), list):
        return document["targets"]
    if isinstance(document.get("target"), dict):
        return [document["target"]]
    return []


def _load_target(relative_path: str, target_key: str) -> dict:
    document = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    for target in _targets(document):
        if str(target.get("key")) == target_key:
            return target
    raise ValueError(f"target {target_key!r} is missing from {relative_path}")


def _batch(source_key: str, company: str, target: dict, audience: str) -> dict:
    recruitment_type = "internship" if source_key in INTERNSHIP_KEYS else "campus_recruitment"
    label = "实习招聘" if recruitment_type == "internship" else "校园招聘"
    return {
        "identity_key": f"phase-02:{source_key.lower()}",
        "title": f"{company}{label}",
        "official_page_url": target["official_page_url"],
        "recruitment_type": recruitment_type,
        "target_audience": audience,
        "published_on": "",
        "deadline": "",
    }


def _request_values(target: dict) -> dict:
    for name in ("request", "body", "base_body", "base_values"):
        value = target.get(name)
        if isinstance(value, dict):
            return value
    return {}


def _pagination(source_key: str, target: dict) -> dict:
    raw = target.get("pagination") or {}
    if source_key == "P08":
        raw = {
            "mode": "page_index",
            "page_param": "page.pageNo",
            "size_param": "page.pageSize",
            "page_size": 10,
            "start": 1,
            "max_pages": 100,
            "total_kind": "pages",
        }
    mode = raw.get("mode", "page_index")
    if mode == "single":
        return {"mode": "single", "page_size": raw.get("page_size", 1), "max_pages": 1}
    start = raw.get("start")
    if start is None:
        start = 0 if source_key == "P13" or mode == "offset" else 1
    result = {
        "mode": mode,
        "page_param": raw["page_param"],
        "size_param": raw["size_param"],
        "page_size": raw["page_size"],
        "max_pages": min(raw.get("max_pages", 100), 100),
        "total_kind": target.get("total_kind", raw.get("total_kind", "items")),
    }
    result["start_offset" if mode == "offset" else "start_page"] = start
    return result


def _field_path(target: dict, primary: str, fallback: str) -> str:
    value = target.get(primary) or target.get(fallback) or ""
    return str(value)


def _location_path(target: dict) -> str:
    values = target.get("location_paths")
    if isinstance(values, list):
        return "||".join(str(value) for value in values if str(value).strip())
    return {
        "pinduoduo": "workLocation",
        "li_auto": "location_title",
        "crrc": "workPlaceStr",
        "vivo_autumn_campus": "LocNames",
        "P08-C07": "cityList[].name",
    }.get(str(target.get("key")), "")


def _title_path(target: dict) -> str:
    return _field_path(target, "title_path", "title_field") or {
        "pinduoduo": "name",
        "li_auto": "title",
        "crrc": "postName",
        "vivo_autumn_campus": "JobAdName",
        "P08-C07": "name",
    }.get(str(target.get("key")), "")


def _row_filters(target: dict) -> list[dict]:
    filters = []
    request_values = _request_values(target)
    row_filter = target.get("row_filter")
    if isinstance(row_filter, dict):
        if "allowed" in row_filter:
            filters.append({"path": row_filter["path"], "equals_any": row_filter["allowed"]})
        elif "contains_any" in row_filter:
            filters.append({"path": row_filter["path"], "contains_any": row_filter["contains_any"]})
    for scope in target.get("scope_fields", []):
        # A field already fixed in the request is a server-side scope guard.
        # Requiring the same field in every response row breaks APIs that do
        # not echo request filters (for example FAW-VW recruitType).
        if scope["path"] in request_values:
            continue
        filters.append({"path": scope["path"], "equals_any": scope["allowed"]})
    scope = target.get("scope")
    if isinstance(scope, dict) and scope.get("field") and scope.get("allowed"):
        filters.append({"path": scope["field"], "equals_any": scope["allowed"]})
    return filters


def _generic_config(source_key: str, company: str, target: dict, audience: str) -> dict:
    method = str(target.get("method", "GET")).upper()
    config = {
        "endpoint": target["endpoint"],
        "method": method,
        "body_encoding": target.get("body_encoding", "query" if method == "GET" else "json"),
        "headers": target.get("headers", {}),
        "pagination": _pagination(source_key, target),
        "list_path": target["list_path"],
        "batch": _batch(source_key, company, target, audience),
        "field_map": {
            "position_key": _field_path(target, "id_path", "id_field"),
            "title": _title_path(target),
            "location": _location_path(target),
        },
        # Tencent's projectMappingIdList already limits the response to the
        # three accepted campus projects. Cycle 14 proved that the older
        # recruitLabelName whitelist was incomplete and would drop valid rows.
        "row_filters": [] if source_key == "P01" else _row_filters(target),
        "request_delay_seconds": 1,
    }
    values = _request_values(target)
    config["params" if method == "GET" else "body"] = values
    if target.get("total_path"):
        config["total_path"] = target["total_path"]
    if target.get("success"):
        config["success"] = target["success"]
    if not target.get("total_path"):
        config["stop_on_short_page"] = True
    if source_key in UPDATED_FIELDS:
        config["field_map"]["updated_at"] = UPDATED_FIELDS[source_key]
    return config


def _moka_config(source_key: str, company: str, target: dict, audience: str) -> dict:
    request = _request_values(target)
    return {
        "org_id": target["endpoint"].rstrip("/").rsplit("/", 1)[-1],
        "site_id": int(request["siteId"]),
        "mode": "campus",
        "page_size": target["pagination"]["page_size"],
        "max_pages": target["pagination"]["max_pages"],
        "request_delay_seconds": 1,
        "batch": _batch(source_key, company, target, audience),
    }


def _embedded_config(source_key: str, company: str, target: dict, audience: str) -> dict:
    return {
        "response_transform": target["response_kind"],
        "headers": target.get("headers", {"Accept": "text/html"}),
        "list_path": target["list_path"],
        "total_path": target.get("total_path", ""),
        "batch": _batch(source_key, company, target, audience),
        "field_map": {
            "position_key": _field_path(target, "id_path", "id_field"),
            "title": _title_path(target),
            "location": _location_path(target),
            # Apple calls this a posting date, not an update timestamp. Keep it
            # out of source_updated_on so a publication date is not mislabeled.
            "updated_at": "",
            "application_url": "href" if source_key == "J03" else "",
        },
        "row_filters": _row_filters(target),
    }


def build_rows() -> list[dict[str, str]]:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = []
    for source in ledger["sources"]:
        key = source["key"]
        relative_path, target_key, industry, official_domain, source_type, adapter, entrypoint, audience = SOURCE_META[key]
        target = _load_target(relative_path, target_key)
        company = source["company"]
        if adapter == "moka_public_api":
            parser_config = _moka_config(key, company, target, audience)
        elif adapter == "embedded_jobs":
            parser_config = _embedded_config(key, company, target, audience)
        else:
            parser_config = _generic_config(key, company, target, audience)
        if company in PARTITIONED_COMPANIES:
            parser_config = partitioned_parser_config(
                company,
                adapter,
                parser_config,
            )
        evidence = (
            f"T3 stable source {key}; {source['evidence_file']}; "
            f"official page {target['official_page_url']}; "
            f"{target.get('official_link_evidence', 'official recruitment page and endpoint were validated')}"
        )
        rows.append(
            {
                "organization_name": company,
                "company_type": TYPE_CODES[source["company_type"]],
                "industry": industry,
                "official_domain": official_domain,
                "source_type": source_type,
                "source_url": (
                    "https://hr-campus.vivo.com/jobs"
                    if company == "vivo"
                    else target["official_page_url"]
                ),
                "official_entrypoint_url": entrypoint,
                "admission_evidence": evidence,
                "adapter_name": adapter,
                "parser_config": json.dumps(parser_config, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                "is_active": "false",
            }
        )
    if len(rows) != 25 or len({row["organization_name"] for row in rows}) != 25:
        raise ValueError("T4 catalog must contain exactly 25 unique organizations")
    return rows


def write_catalog(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(build_rows())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "source_catalog.csv")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        temporary = args.output.with_suffix(args.output.suffix + ".generated")
        try:
            write_catalog(temporary)
            expected = temporary.read_text(encoding="utf-8")
        finally:
            temporary.unlink(missing_ok=True)
        if existing != expected:
            raise SystemExit("source catalog is not generated from the current T4 ledger")
        print("source_catalog_rows=25 generated=true")
        return 0
    write_catalog(args.output)
    print(f"source_catalog_rows=25 output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
