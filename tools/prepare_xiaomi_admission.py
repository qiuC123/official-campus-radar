"""Build an offline Xiaomi admission candidate from frozen browser evidence.

This command never imports a crawler, opens the network, or writes the database.
It preserves job identities and distinguishes sampled partitions from admission.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/company-expansion-xiaomi-browser-followup-20260907.json"
OUTPUT = ROOT / "work/xiaomi-admission-candidate-20260907.json"


def navigation_labels(lines):
    """Read only the observed project filter section, not arbitrary body mentions."""
    if "招聘项目" not in lines:
        return []
    start = lines.index("招聘项目") + 1
    end = lines.index("城市", start) if "城市" in lines[start:] else start
    return [line for line in lines[start:end] if line.endswith("招聘计划")]


def build_candidate(report):
    pages = []
    records = []
    seen_stages = set()
    all_labels = set()
    for page in report["pages"]:
        stage = page["stage"]
        if stage in seen_stages:
            raise ValueError("duplicate_stage")
        seen_stages.add(stage)
        lines = [line.strip() for line in page.get("visible_text_excerpt", "").splitlines()]
        labels = navigation_labels(lines)
        all_labels.update(labels)
        responses = page["job_responses"]
        if len(responses) > 1:
            raise ValueError("ambiguous_page_responses")
        summary = {
            "stage": stage, "url": page["url"], "http_status": page["http_status"],
            "navigation_project_labels": labels, "records_observed": 0,
            "declared_total": None, "response_available": bool(responses),
        }
        pages.append(summary)
        if not responses:
            continue
        response = responses[0]
        rows = response["rows"]
        ids = [row.get("id") for row in rows]
        if any(not isinstance(value, str) or not value.strip() for value in ids):
            raise ValueError("missing_job_identity")
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate_identity_within_page")
        if ids != response["ids"] or len(rows) != response["row_count"]:
            raise ValueError("inconsistent_page_identity_metadata")
        summary.update(records_observed=len(rows), declared_total=response["declared_total"])
        title_subjects = defaultdict(set)
        for row in rows:
            subject = row.get("job_subject") or {}
            title_subjects[row.get("title")].add(subject.get("id"))
        for row in rows:
            title = row.get("title")
            if not isinstance(title, str) or not title.strip():
                raise ValueError("missing_title")
            subject_id = (row.get("job_subject") or {}).get("id")
            if subject_id is not None and (not isinstance(subject_id, str) or not subject_id.strip()):
                raise ValueError("invalid_subject_identity")
            indices = [index for index, line in enumerate(lines) if line == title.strip()]
            # Repeated titles cannot identify a city or an individual card. Even project
            # label hints are withheld when same-title rows belong to different subjects.
            label_hints = sorted({label for index in indices if index + 1 < len(lines)
                                  for label in labels if label in lines[index + 1]})
            if len(title_subjects[title]) != 1:
                label_hints = []
            recruit_type = row.get("recruit_type") or {}
            records.append({
                "id": row["id"], "title": title, "subject_id": subject_id,
                "recruit_type_id": recruit_type.get("id"),
                "recruit_type_name": recruit_type.get("name"),
                "stage": stage, "title_occurrences_in_page": len(indices),
                "label_candidates": label_hints,
            })

    by_id = defaultdict(list)
    by_subject = defaultdict(list)
    for row in records:
        by_id[row["id"]].append(row)
        if row["subject_id"] is not None:
            by_subject[row["subject_id"]].append(row)
    conflicts = sorted(job_id for job_id, rows in by_id.items()
                       if len({row["subject_id"] for row in rows}) != 1)
    missing = sorted({row["id"] for row in records if row["subject_id"] is None})
    projects = []
    for subject_id, rows in sorted(by_subject.items()):
        projects.append({
            "subject_id": subject_id,
            "label_candidates": sorted({label for row in rows for label in row["label_candidates"]}),
            "unique_job_count": len({row["id"] for row in rows}),
            "observations_by_stage": dict(sorted(Counter(row["stage"] for row in rows).items())),
            "job_ids": sorted({row["id"] for row in rows}),
            "recruit_type_ids": sorted({row["recruit_type_id"] for row in rows if row["recruit_type_id"]}),
            "recruit_type_names": sorted({row["recruit_type_name"] for row in rows if row["recruit_type_name"]}),
            "cohort": None, "recruitment_phase": None, "admitted": False,
        })
    observed_labels = {label for row in records for label in row["label_candidates"]}
    return {
        "schema_version": 1, "company": "小米", "evidence_kind": "offline_sample_candidate",
        "network_requests": 0, "database_writes": 0,
        "source_run_state": report["state"], "source_stop_reason": report["stop_reason"],
        "sample_observations": len(records), "sample_unique_jobs": len(by_id),
        "project_candidates": projects, "pages": pages, "records": records,
        "partition_diagnostics": {
            "missing_subject_job_ids": missing, "conflicting_subject_job_ids": conflicts,
            "sample_partition_consistent": bool(records) and not missing and not conflicts,
            "repeated_job_ids_across_pages": sorted(job_id for job_id, rows in by_id.items() if len(rows) > 1),
            "navigation_labels_without_sample_mapping": sorted(all_labels - observed_labels),
        },
        "admission_gates": {
            "official_announcement_and_cohort": {"verified": False, "reason": "official_original_and_project_specific_scope_not_frozen"},
            "complete_pagination": {"verified": False, "reason": "bounded_samples_only"},
            "exhaustive_project_coverage": {"verified": False, "reason": "incomplete_portals_and_unresolved_navigation_projects"},
            "current_application_availability": {"verified": False, "reason": "no_independent_application_state_evidence"},
        },
        "production_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write the deterministic offline candidate file")
    args = parser.parse_args(argv)
    raw = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    candidate = build_candidate(json.loads(raw))
    candidate["source"] = {"file": SOURCE.relative_to(ROOT).as_posix(),
                           "sha256": hashlib.sha256(raw).hexdigest(),
                           "hash_normalization": "utf8_lf_line_endings"}
    if args.write:
        OUTPUT.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT) if args.write else None,
                      "sample_unique_jobs": candidate["sample_unique_jobs"],
                      "project_candidates": len(candidate["project_candidates"]),
                      "production_admitted": False, "network_requests": 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
