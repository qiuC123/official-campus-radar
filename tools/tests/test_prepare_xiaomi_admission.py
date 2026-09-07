from contextlib import redirect_stdout
import copy
import hashlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools.prepare_xiaomi_admission import OUTPUT, SOURCE, build_candidate, main


class XiaomiAdmissionCandidateTests(unittest.TestCase):
    def setUp(self):
        self.report = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_sample_projects_preserve_distinct_ids_and_do_not_guess_cohorts(self):
        result = build_candidate(self.report)
        projects = {row["subject_id"]: row for row in result["project_candidates"]}
        self.assertEqual(result["sample_unique_jobs"], 30)
        self.assertEqual({key: row["unique_job_count"] for key, row in projects.items()}, {
            "7618850506199533866": 4, "7659311908839262514": 16, "7659311908839360818": 10,
        })
        self.assertEqual(projects["7618850506199533866"]["label_candidates"], ["实习生招聘计划"])
        self.assertEqual(projects["7659311908839262514"]["label_candidates"], ["2027届校园招聘计划"])
        self.assertEqual(projects["7659311908839360818"]["label_candidates"], ["2027届新零售招聘计划"])
        for project in projects.values():
            self.assertIsNone(project["cohort"])
            self.assertIsNone(project["recruitment_phase"])
            self.assertFalse(project["admitted"])
        # Four same-title positions remain four jobs. Titles are not identity keys.
        repeated = [row for row in result["records"] if row["title"] == "交付体验助理"]
        self.assertEqual(len({row["id"] for row in repeated}), 4)
        self.assertTrue(all(row["title_occurrences_in_page"] == 4 for row in repeated))

    def test_sample_consistency_does_not_prove_coverage_or_availability(self):
        result = build_candidate(self.report)
        diagnostics = result["partition_diagnostics"]
        self.assertTrue(diagnostics["sample_partition_consistent"])
        self.assertEqual(diagnostics["navigation_labels_without_sample_mapping"], ["2027届境外招聘计划"])
        internship = next(page for page in result["pages"] if page["stage"] == "internship:first")
        self.assertFalse(internship["response_available"])
        self.assertIsNone(internship["declared_total"])
        self.assertFalse(result["production_admitted"])
        self.assertTrue(all(not gate["verified"] for gate in result["admission_gates"].values()))
        # Portal totals may overlap. A sum of 768 + 121 would be an unsupported company total.
        self.assertNotIn("company_job_total", result)
        self.assertEqual(result["network_requests"], 0)

    def test_missing_project_is_retained_as_unassigned(self):
        row = self.report["pages"][0]["job_responses"][0]["rows"][0]
        row["job_subject"] = None
        result = build_candidate(self.report)
        self.assertEqual(result["sample_unique_jobs"], 30)
        self.assertEqual(result["partition_diagnostics"]["missing_subject_job_ids"], [row["id"]])
        self.assertFalse(result["partition_diagnostics"]["sample_partition_consistent"])

    def test_conflicting_project_identity_across_portals_is_exposed(self):
        first = self.report["pages"][0]["job_responses"][0]["rows"][0]
        retail = self.report["pages"][2]["job_responses"][0]
        retail["rows"][0]["id"] = first["id"]
        retail["ids"][0] = first["id"]
        result = build_candidate(self.report)
        self.assertEqual(result["sample_unique_jobs"], 29)
        self.assertEqual(result["partition_diagnostics"]["conflicting_subject_job_ids"], [first["id"]])
        self.assertFalse(result["partition_diagnostics"]["sample_partition_consistent"])

    def test_ambiguous_same_title_cannot_assign_project_label(self):
        self.report["pages"][0]["job_responses"][0]["rows"][0]["job_subject"]["id"] = "unknown-project"
        result = build_candidate(self.report)
        repeated = [row for row in result["records"] if row["title"] == "交付体验助理"]
        self.assertTrue(all(row["label_candidates"] == [] for row in repeated))
        self.assertIn("unknown-project", {row["subject_id"] for row in result["project_candidates"]})

    def test_corrupt_identity_or_ambiguous_response_fails_instead_of_silent_deduplication(self):
        for defect in ("duplicate", "id_mismatch", "ambiguous", "empty_identity"):
            report = copy.deepcopy(self.report)
            page = report["pages"][0]
            response = page["job_responses"][0]
            if defect == "duplicate":
                response["rows"][1]["id"] = response["rows"][0]["id"]
            elif defect == "id_mismatch":
                response["ids"][0] = "not-the-row-id"
            elif defect == "ambiguous":
                page["job_responses"].append(copy.deepcopy(response))
            else:
                response["rows"][0]["id"] = ""
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                build_candidate(report)

    def test_default_command_does_not_write_and_frozen_output_matches_source(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            with patch("tools.prepare_xiaomi_admission.OUTPUT", path), redirect_stdout(StringIO()):
                self.assertEqual(main([]), 0)
                self.assertFalse(path.exists())
                self.assertEqual(main(["--write"]), 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), json.loads(OUTPUT.read_text(encoding="utf-8")))
        frozen = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(frozen["source"]["sha256"], hashlib.sha256(SOURCE.read_bytes().replace(b"\r\n", b"\n")).hexdigest())

    def test_proposed_internship_call_cannot_reset_or_expand_job_allowance(self):
        proposal = json.loads(SOURCE.with_name("xiaomi-internship-mcp-proposal-20260907.json").read_text(encoding="utf-8"))
        self.assertEqual(proposal["status"], "proposed_not_authorized")
        prior = proposal["prior_budget"]
        self.assertEqual(prior["by_endpoint"], self.report["budget"]["by_endpoint"])
        self.assertEqual(prior["approved_round_requests"], 200)
        self.assertEqual(prior["remaining_total_requests"], 0)
        args = proposal["arguments"]
        self.assertEqual(proposal["expanded_round_total_limit_if_approved"], prior["approved_round_requests"] + args["endpoint_limit"])
        self.assertEqual(args["endpoint_limit"], proposal["requested_additional_total_requests"])
        job_key = args["json_response"]["response_endpoint"]
        self.assertEqual(args["business_endpoint_limits"][job_key] + prior["known_job_requests"], prior["known_job_limit"])
        self.assertEqual(args["seed_url"], "https://xiaomi.jobs.f.mioffice.cn/internship/")
        self.assertEqual(args["page_limit"], 2)
        self.assertEqual(proposal["max_calls"], 1)
        self.assertEqual(proposal["max_next_clicks"], 1)
        self.assertEqual(proposal["timebox_seconds"], 900)
        self.assertFalse(proposal["retry_or_followup_allowed"])
        self.assertFalse(proposal["production_admission_authorized"])


if __name__ == "__main__":
    unittest.main()
