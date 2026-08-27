from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campus_radar.settings")

import django

django.setup()

from radar.collectors.base import FetchedPage
from radar.collectors.embedded_jobs import EmbeddedJobsAdapter
from radar.collectors.json_api import _canonical_json, _set_path
from radar.collectors.moka_api import MokaPublicApiAdapter, _date_text, _location_text
from radar.collectors.registry import AdapterRegistry
from tools.build_t4_source_catalog import build_rows


LEDGER = ROOT / "tools" / "stable-sources-phase-02-t3.json"
DEFAULT_OUTPUT = ROOT / "work" / "phase-02-t4-offline-validation-cycle-02.json"
TENCENT_SAMPLE_REPORT = ROOT / "work" / "phase-02-t3-api-acceptance-cycle-13-tencent.json"


def _results(document: dict) -> list[dict]:
    results = list(document.get("results", []))
    if isinstance(document.get("result"), dict):
        results.append(document["result"])
    return results


def _result(document: dict, key: str) -> dict:
    matches = [item for item in _results(document) if str(item.get("key")) == key]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one saved result for {key!r}")
    return matches[0]


def _samples(result: dict) -> list[dict]:
    samples = list(result.get("samples", []))
    if samples:
        return samples
    for page in result.get("pages", []):
        samples.extend(page.get("samples", []))
    return samples


def _assign_projection(target: dict, path: str, value: object) -> None:
    parts = path.split(".")

    def assign(container: dict, index: int, projected: object) -> None:
        part = parts[index]
        is_array = part.endswith("[]")
        key = part[:-2] if is_array else part
        last = index == len(parts) - 1
        if is_array:
            values = projected if isinstance(projected, list) else [projected]
            if last:
                container[key] = copy.deepcopy(values)
                return
            children = []
            for item in values:
                child: dict = {}
                assign(child, index + 1, item)
                children.append(child)
            container[key] = children
            return
        if last:
            container[key] = copy.deepcopy(projected)
            return
        child = container.get(key)
        if not isinstance(child, dict):
            child = {}
            container[key] = child
        assign(child, index + 1, projected)

    assign(target, 0, value)


def inflate_sample(sample: dict) -> dict:
    """Rebuild nested JSON from the deliberately small T3 sample projection."""
    inflated: dict = {}
    plain = [(key, value) for key, value in sample.items() if "." not in key and "[]" not in key]
    projected = [(key, value) for key, value in sample.items() if (key, value) not in plain]
    for key, value in plain + projected:
        _assign_projection(inflated, key, value)
    return inflated


def _source(row: dict[str, str]) -> SimpleNamespace:
    return SimpleNamespace(
        organization=SimpleNamespace(
            name=row["organization_name"],
            official_domain=row["official_domain"],
        ),
        source_type=row["source_type"],
        source_url=row["source_url"],
        official_entrypoint_url=row["official_entrypoint_url"],
        admission_evidence=row["admission_evidence"],
        adapter_name=row["adapter_name"],
        parser_config=json.loads(row["parser_config"]),
    )


def _normalized_config(source: SimpleNamespace, rows: list[dict]) -> dict:
    if source.adapter_name == "moka_public_api":
        for row in rows:
            row["_radar_location_text"] = _location_text(row.get("locations"))
            row["_radar_updated_on"] = _date_text(row.get("updatedAt"))
        return MokaPublicApiAdapter._normalized_source(source).parser_config
    if source.adapter_name == "embedded_jobs":
        return EmbeddedJobsAdapter._normalized_source(source).parser_config
    return source.parser_config


def _canonical_page(source: SimpleNamespace, sample_rows: list[dict]) -> FetchedPage:
    rows = [inflate_sample(sample) for sample in sample_rows]
    config = _normalized_config(source, rows)
    document: dict = {}
    _set_path(document, config["list_path"], rows)
    document["_radar"] = {
        "positions_complete": True,
        "list_path": config["list_path"],
        "batch": copy.deepcopy(config["batch"]),
        "field_map": copy.deepcopy(config["field_map"]),
        "valid_values": copy.deepcopy(config.get("valid_values", {})),
        "row_filters": copy.deepcopy(config.get("row_filters", [])),
        "html_fields": copy.deepcopy(config.get("html_fields", [])),
        "pagination_total_kind": config.get("pagination", {}).get("total_kind", "items"),
        "pagination_mode": config.get("pagination", {}).get("mode", "single"),
    }
    body = _canonical_json(document)
    return FetchedPage(
        canonical_url=str(config.get("endpoint", source.source_url)),
        body=body,
        content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
        http_status=200,
        etag=None,
    )


def _pagination_passed(key: str, result: dict, correction: dict | None) -> bool:
    if key == "P01":
        return bool(correction and correction.get("checks", {}).get("complete"))
    if "complete" in result:
        return bool(result["complete"])
    pagination = result.get("pagination")
    if isinstance(pagination, dict) and "passed" in pagination:
        return bool(pagination["passed"])
    if key == "P08":
        return bool(
            result.get("reported_total_pages")
            and result.get("ids_are_unique")
            and result.get("different_from_observed_page_one")
        )
    return False


def _scope_passed(key: str, result: dict, correction: dict | None) -> bool:
    if key == "P01":
        checks = (correction or {}).get("checks", {})
        return all(
            bool(checks.get(name))
            for name in ("mapping_ids", "mapping_names", "observed_labels")
        )
    if "scope_ok" in result:
        return bool(result["scope_ok"])
    campus = result.get("campus_evidence")
    if isinstance(campus, dict):
        return bool(campus.get("passed"))
    checks = result.get("scope_checks")
    if isinstance(checks, list) and checks:
        return all(bool(check.get("passed")) for check in checks)
    if key == "P08":
        return bool(result.get("campus_raw_values"))
    return bool(result.get("scope_evidence"))


def validate_offline() -> dict:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    catalog = build_rows()
    catalog_by_company = {row["organization_name"]: row for row in catalog}
    results = []

    for entry in ledger["sources"]:
        key = entry["key"]
        evidence_path = ROOT / entry["evidence_file"]
        evidence_document = json.loads(evidence_path.read_text(encoding="utf-8"))
        correction = evidence_document if key == "P01" else None
        if key == "P01":
            sample_document = json.loads(TENCENT_SAMPLE_REPORT.read_text(encoding="utf-8"))
            saved_result = _result(sample_document, "P01")
            evidence_passed = bool(evidence_document.get("passed"))
            sample_evidence_file = str(TENCENT_SAMPLE_REPORT.relative_to(ROOT)).replace("\\", "/")
        else:
            saved_result = _result(evidence_document, str(entry["evidence_result_key"]))
            # Multi-target T3 cycles may have an overall failure caused by a
            # different company. The frozen ledger points to this exact result.
            evidence_passed = bool(saved_result.get("passed"))
            sample_evidence_file = entry["evidence_file"]

        sample_rows = _samples(saved_result)
        row = catalog_by_company[entry["company"]]
        source = _source(row)
        errors: list[str] = []
        candidates = []
        try:
            AdapterRegistry.validate_source_config(source)
            candidates = AdapterRegistry.get(source).extract(
                source, _canonical_page(source, sample_rows)
            )
        except (KeyError, TypeError, ValueError) as error:
            errors.append(str(error))

        positions = list(candidates[0].positions) if len(candidates) == 1 else []
        position_keys = [position.position_key for position in positions]
        location_count = sum(
            bool(position.location_text.strip())
            and position.location_text.strip() != "未说明"
            for position in positions
        )
        updated_count = sum(position.source_updated_on is not None for position in positions)
        parser_config = source.parser_config
        if source.adapter_name == "moka_public_api":
            location_path = "locations"
            update_path = "updatedAt"
        else:
            location_path = str(parser_config.get("field_map", {}).get("location", ""))
            update_path = str(parser_config.get("field_map", {}).get("updated_at", ""))
        report_location_proof = saved_result.get("missing_required_fields") == []
        checks = {
            "saved_acceptance_passed": evidence_passed,
            "samples_present": bool(sample_rows),
            "adapter_contract_passed": not errors,
            "one_batch_extracted": len(candidates) == 1,
            "all_sample_rows_retained": len(positions) == len(sample_rows),
            "position_keys_present": bool(positions) and all(position_keys),
            "position_keys_unique": len(position_keys) == len(set(position_keys)),
            "titles_present": bool(positions) and all(position.title.strip() for position in positions),
            "location_mapping_present": bool(location_path),
            "location_evidence_present": bool(location_count) or report_location_proof,
            "configured_update_time_parsed": not update_path or bool(updated_count),
            "positions_complete": bool(candidates and candidates[0].positions_complete),
            "pagination_evidence_passed": _pagination_passed(key, saved_result, correction),
            "campus_scope_evidence_passed": _scope_passed(key, saved_result, correction),
        }
        passed = all(checks.values()) and not errors
        results.append(
            {
                "key": key,
                "company": entry["company"],
                "adapter_name": source.adapter_name,
                "evidence_file": entry["evidence_file"],
                "sample_evidence_file": sample_evidence_file,
                "sample_count": len(sample_rows),
                "extracted_position_count": len(positions),
                "locations_observed": location_count,
                "updated_dates_observed": updated_count,
                "checks": checks,
                "errors": errors,
                "passed": passed,
            }
        )

    passed_count = sum(bool(result["passed"]) for result in results)
    return {
        "cycle": "Phase 02 / T4 Cycle 02",
        "mode": "offline saved-sample contract validation",
        "as_of": ledger["as_of"],
        "network_requests_made": 0,
        "database_writes": False,
        "source_count": len(results),
        "passed_count": passed_count,
        "failed_count": len(results) - passed_count,
        "results": results,
        "passed": passed_count == len(results) == 25,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = validate_offline()
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        existing = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        if existing != rendered:
            raise SystemExit("T4 Cycle 02 offline report is stale")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(
        f"sources={report['source_count']} passed={report['passed_count']} "
        f"failed={report['failed_count']} network_requests=0"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
