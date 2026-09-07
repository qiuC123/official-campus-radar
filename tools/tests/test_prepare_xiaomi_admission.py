from contextlib import redirect_stdout
import copy
from datetime import datetime
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

    def test_confirmed_internship_run_matches_frozen_proposal_and_single_call(self):
        proposal_path = SOURCE.with_name("xiaomi-internship-mcp-proposal-20260907.json")
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        run = json.loads(SOURCE.with_name("xiaomi-internship-mcp-run-20260907.json").read_text(encoding="utf-8"))
        response = json.loads(SOURCE.with_name("xiaomi-internship-mcp-response-20260907.json").read_text(encoding="utf-8"))
        self.assertEqual(run["authorization"]["user_message"], "确认")
        self.assertEqual(run["authorization"]["proposal_sha256"], hashlib.sha256(proposal_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest())
        self.assertEqual(run["arguments"], proposal["arguments"])
        self.assertEqual(run["prior_budget"], proposal["prior_budget"])
        self.assertEqual(run["result"], response["result"])
        self.assertEqual(run["caller_calls_reserved"], proposal["max_calls"])
        self.assertEqual(run["state"], "stopped_after_single_call")
        self.assertFalse(run["retry_or_followup_allowed"])
        result = run["result"]
        elapsed = datetime.fromisoformat(result["updated_at"]) - datetime.fromisoformat(result["started_at"])
        self.assertLessEqual(elapsed.total_seconds(), proposal["timebox_seconds"])

    def test_internship_failure_budget_keeps_prior_requests_and_unused_balance(self):
        run = json.loads(SOURCE.with_name("xiaomi-internship-mcp-run-20260907.json").read_text(encoding="utf-8"))
        budget = run["result"]["endpoint_requests"]
        aggregate = run["aggregate_budget"]
        self.assertEqual(budget["used"], 57)
        for view in ("by_endpoint", "by_method_endpoint", "by_purpose"):
            self.assertEqual(sum(budget[view].values()), budget["used"])
        self.assertEqual(budget["observed_request_attempts"], budget["used"] + budget["blocked_before_send"]["total"])
        self.assertEqual(budget["blocked_before_send"]["by_resource_type"], {"image": 4})
        before = run["prior_budget"]["by_endpoint"]
        keys = before.keys() | budget["by_endpoint"].keys()
        expected = {key: before.get(key, 0) + budget["by_endpoint"].get(key, 0) for key in keys}
        self.assertEqual(aggregate["expanded_round_by_endpoint"], expected)
        self.assertEqual(sum(expected.values()), 257)
        self.assertEqual(aggregate["expanded_round_requests"], 257)
        self.assertEqual(aggregate["unspent_total_requests"], 143)
        job_key = run["arguments"]["json_response"]["response_endpoint"]
        self.assertEqual(budget["by_endpoint"][job_key], 1)
        self.assertEqual(aggregate["known_cumulative_job_requests"], run["prior_budget"]["known_job_requests"] + 1)
        self.assertEqual(aggregate["known_cumulative_job_requests"], 10)
        self.assertEqual(aggregate["unspent_job_requests"], 2)
        self.assertFalse(aggregate["further_calls_authorized"])
        for key, count in budget["by_endpoint"].items():
            self.assertLessEqual(count, budget["business_limits"].get(key, budget["per_endpoint_limit"]))

    def test_internship_http_error_cannot_prove_blocking_empty_jobs_or_admission(self):
        run = json.loads(SOURCE.with_name("xiaomi-internship-mcp-run-20260907.json").read_text(encoding="utf-8"))
        result = run["result"]
        self.assertFalse(run["protocol_is_error"])  # MCP delivery succeeded, collection did not.
        self.assertEqual(result["stop_reason"], "response_http_error")
        self.assertEqual(result["pages_completed"], 0)
        self.assertEqual(result["records_count"], 0)
        self.assertIsNone(result["declared_total"])
        self.assertEqual(result["pages"], [])
        self.assertFalse(result["complete"])
        for field in ("response_http_status_retained", "response_object_presence_retained",
                      "website_access_restriction_proven", "empty_or_closed_internship_proven",
                      "sample_goal_complete", "production_admitted"):
            self.assertFalse(run["verification"][field])
        self.assertIsNone(run["verification"]["response_http_status"])

    def test_diagnostic_upgrade_is_zero_network_and_does_not_rewrite_old_failure(self):
        receipt = json.loads(SOURCE.with_name("xiaomi-mcp-error-diagnostics-verification-20260907.json").read_text(encoding="utf-8"))
        old = json.loads(SOURCE.with_name("xiaomi-internship-mcp-run-20260907.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["historical_run_id"], old["result"]["run_id"])
        self.assertEqual(receipt["historical_summary_sha256"], old["persisted_summary_sha256"])
        self.assertEqual(receipt["historical_errors_bytes"], 0)
        self.assertFalse(receipt["historical_http_status_recovered"])
        self.assertEqual(receipt["arguments"]["endpoint_limit"], 0)
        result = receipt["result"]
        self.assertEqual(result["tool"], "crawl_site")
        self.assertEqual(result["stop_reason"], "endpoint_budget_exhausted")
        self.assertEqual(result["error_facts"], [])
        self.assertIn("errors", result["artifacts"])
        self.assertEqual(result["endpoint_requests"]["used"], 0)
        self.assertFalse(result["complete"])
        self.assertFalse(receipt["verification"]["live_company_retried"])
        self.assertTrue(receipt["verification"]["persisted_summary_matches"])
        self.assertNotIn("error_facts", old["result"])


if __name__ == "__main__":
    unittest.main()
