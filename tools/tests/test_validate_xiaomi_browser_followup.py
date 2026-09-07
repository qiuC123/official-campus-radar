from contextlib import redirect_stdout
from io import StringIO
import hashlib
import json
import unittest
from unittest.mock import patch

from tools.validate_xiaomi_browser_followup import FollowupBudget, JOB_KEY, PRIOR, REPORT, main, safe_next, summarize_evidence
from tools.validate_xiaomi_browser_sample import job_sample


class XiaomiBrowserFollowupTests(unittest.TestCase):
    def budget(self):
        return FollowupBudget(json.loads(PRIOR.read_text(encoding="utf-8")))

    def test_default_command_never_starts_browser(self):
        with patch("sys.argv", ["validate_xiaomi_browser_followup.py"]), patch(
            "tools.validate_xiaomi_browser_followup.experiment"
        ) as experiment, redirect_stdout(StringIO()):
            self.assertEqual(main(), 0)
        experiment.assert_not_called()

    def test_job_requests_inherit_prior_and_merge_methods_without_query_values(self):
        budget = self.budget()
        for index in range(7):
            self.assertTrue(budget.allow("GET" if index % 2 else "POST", "https://" + JOB_KEY + "?_signature=secret", "fetch"))
        self.assertEqual(budget.summary()["known_cumulative_job_requests"], 12)
        self.assertFalse(budget.allow("POST", "https://" + JOB_KEY, "fetch"))
        self.assertFalse(budget.allow("GET", "https://example.com/another", "document"))
        self.assertNotIn("secret", json.dumps(budget.summary()))

    def test_static_navigation_and_api_share_remaining_total_budget(self):
        budget = self.budget()
        for index in range(150):
            self.assertTrue(budget.allow("GET", f"https://example.com/resource/{index}", "script"))
        self.assertFalse(budget.allow("GET", "https://example.com/next", "document"))
        self.assertEqual(budget.summary()["approved_round_requests"], 200)
        self.assertEqual(budget.summary()["new_requests"], 150)

    def test_other_endpoint_inherits_two_old_requests_and_stops_at_twenty(self):
        budget = self.budget()
        url = "https://xiaomi.jobs.f.mioffice.cn/api/v1/ip/location"
        self.assertTrue(all(budget.allow("GET", url, "fetch") for _ in range(18)))
        self.assertFalse(budget.allow("POST", url, "fetch"))

    def test_real_next_container_is_accepted_but_jump_form_and_disabled_are_rejected(self):
        metadata = {"tag": "li", "title": "下一页", "classes": ["atsx-pagination-next"],
                    "visible": True, "disabled": False, "form": False, "unsafe_descendants": False}
        self.assertTrue(safe_next(metadata))
        for change in ({"classes": ["atsx-pagination-jump-next"]}, {"title": "向后 5 页"},
                       {"form": True}, {"disabled": True}, {"unsafe_descendants": True}, {"visible": False}):
            self.assertFalse(safe_next(metadata | change))

    def test_project_field_values_are_retained_without_unrelated_sensitive_fields(self):
        sample = job_sample({"data": {"count": 1, "job_post_list": [{"id": "1",
            "job_subject": {"id": "project-1", "name": "校园招聘", "token": "secret"},
            "job_process_id": "process-1", "process_type": 2, "csrf": "secret"}]}})
        self.assertEqual(sample["rows"][0]["job_subject"], {"id": "project-1", "name": "校园招聘"})
        self.assertEqual(sample["rows"][0]["job_process_id"], "process-1")
        self.assertNotIn("secret", json.dumps(sample))

    def test_frozen_followup_reconciles_with_inherited_ledger_without_exceeding_it(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        budget = self.budget()
        for event in report["budget"]["new_request_events"]:
            self.assertTrue(budget.allow(event["method"], "https://" + event["endpoint"], event["resource_type"]))
            self.assertEqual(budget.used[event["endpoint"]], event["approved_round_count"])
        self.assertEqual(dict(budget.used), report["budget"]["by_endpoint"])
        self.assertEqual(budget.summary()["new_requests"], 150)
        self.assertEqual(budget.summary()["known_cumulative_job_requests"], 9)
        self.assertFalse(budget.allow("GET", "https://example.com/unused", "script"))
        self.assertLessEqual(report["elapsed_seconds"], report["plan"]["deadline_seconds"])

    def test_observed_pagination_is_preserved_without_promoting_partial_run(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        evidence = summarize_evidence(report)
        self.assertTrue(evidence["campus_natural_next_observed"])
        self.assertEqual(evidence["captured_unique_jobs"], 30)
        self.assertEqual(evidence["stages"]["newretailing:first"]["declared_total"], 121)
        for key in ("whole_experiment_complete", "full_collection_verified", "project_coverage_verified",
                    "application_availability_verified", "production_admitted"):
            self.assertFalse(evidence[key])
        # An unchanged second page or no click cannot support the page-pair claim.
        report["pages"][1]["job_responses"] = report["pages"][0]["job_responses"]
        self.assertFalse(summarize_evidence(report)["campus_natural_next_observed"])
        report["pagination_clicks"] = 0
        self.assertFalse(summarize_evidence(report)["campus_natural_next_observed"])

    def test_mcp_reference_is_only_a_projection_of_frozen_two_page_evidence(self):
        reference = json.loads(REPORT.with_name("xiaomi-natural-json-mcp-reference-20260907.json").read_text(encoding="utf-8"))
        # Git may check text files out as CRLF on Windows; the evidence hash is LF-normalized.
        raw = REPORT.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(reference["source_hash_normalization"], "utf8_lf_line_endings")
        self.assertEqual(reference["source_sha256"], hashlib.sha256(raw).hexdigest())
        source = json.loads(raw)
        ids = []
        for page, original in zip(reference["pages"], source["pages"][:2], strict=True):
            self.assertEqual(page["stage"], original["stage"])
            response = original["job_responses"][0]
            self.assertEqual(page["declared_total"], response["declared_total"])
            expected = [{"id": row["id"], "title": row["title"], "subject_id": row["job_subject"]["id"],
                         "recruit_type": row["recruit_type"]["name"]} for row in response["rows"]]
            self.assertEqual(page["records"], expected)
            ids.extend(row["id"] for row in page["records"])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), reference["expected_unique_ids"])
        self.assertFalse(reference["complete_collection"])
        self.assertEqual(reference["network_requests"], 0)

    def test_mcp_zero_budget_example_cannot_allocate_new_requests(self):
        args = json.loads(REPORT.with_name("xiaomi-observe-browser-json-zero-budget-20260907.json").read_text(encoding="utf-8"))
        self.assertEqual(args["endpoint_limit"], 0)
        self.assertEqual(args["per_endpoint_limit"], 0)
        self.assertEqual(args["business_endpoint_limits"], {JOB_KEY: 0})
        reference = json.loads(REPORT.with_name("xiaomi-natural-json-mcp-reference-20260907.json").read_text(encoding="utf-8"))
        self.assertEqual({field["name"]: field["path"] for field in args["fields"]}, reference["field_paths"])

    def test_mcp_stdio_evidence_matches_zero_budget_example_and_bounds(self):
        evidence = json.loads(REPORT.with_name("xiaomi-observe-browser-json-protocol-20260907.json").read_text(encoding="utf-8"))
        args = json.loads(REPORT.with_name("xiaomi-observe-browser-json-zero-budget-20260907.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["arguments"], args)
        props = evidence["tool_schema"]["properties"]
        for name, maximum in (("page_limit", 20), ("endpoint_limit", 200), ("per_endpoint_limit", 20)):
            self.assertEqual(props[name]["maximum"], maximum)
        result = evidence["result"]
        self.assertEqual(result["tool"], "observe_browser_json")
        self.assertEqual(result["stop_reason"], "endpoint_budget_exhausted")
        self.assertEqual(result["endpoint_requests"]["used"], 0)
        self.assertEqual(result["pages_completed"], 0)
        self.assertEqual(result["records_count"], 0)
        self.assertFalse(result["complete"])
        self.assertFalse(evidence["verification"]["live_company_collection_tested"])

    def test_unified_mcp_example_preserves_projection_and_exhausted_budget(self):
        old = json.loads(REPORT.with_name("xiaomi-observe-browser-json-zero-budget-20260907.json").read_text(encoding="utf-8"))
        new = json.loads(REPORT.with_name("xiaomi-crawl-site-json-zero-budget-20260907.json").read_text(encoding="utf-8"))
        self.assertEqual(new["extraction_mode"], "browser_json")
        for name in ("seed_url", "page_limit", "endpoint_limit", "per_endpoint_limit", "business_endpoint_limits"):
            self.assertEqual(new[name], old[name])
        self.assertEqual(new["json_response"], {
            name: old[name] for name in ("response_endpoint", "records_path", "fields", "identity_path", "total_path")
        })
        self.assertEqual(new["pagination"], {"next_selector": old["next_selector"]})
        self.assertNotIn("fields", new)

    def test_unified_stdio_evidence_preserves_alias_and_zero_request_stops(self):
        evidence = json.loads(REPORT.with_name("xiaomi-crawl-site-json-protocol-20260907.json").read_text(encoding="utf-8"))
        args = json.loads(REPORT.with_name("xiaomi-crawl-site-json-zero-budget-20260907.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["calls"]["browser_json"]["arguments"], args)
        props = evidence["tool_schemas"]["crawl_site"]["properties"]
        self.assertEqual(props["extraction_mode"]["default"], "html")
        self.assertEqual(set(props["extraction_mode"]["enum"]), {"html", "browser_json"})
        self.assertIn("json_response", props)
        self.assertEqual(props["page_limit"]["default"], 20)
        self.assertEqual(evidence["tool_schemas"]["observe_browser_json"]["properties"]["page_limit"]["default"], 2)
        for name, maximum in (("page_limit", 20), ("endpoint_limit", 200), ("per_endpoint_limit", 20)):
            self.assertEqual(props[name]["maximum"], maximum)
        for name in ("browser_json", "legacy_alias"):
            call = evidence["calls"][name]
            result = call["result"]
            self.assertEqual(result, call["persisted_summary"])
            self.assertEqual(result["tool"], "crawl_site")
            self.assertEqual(result["extraction_mode"], "browser_json")
            self.assertEqual(result["stop_reason"], "endpoint_budget_exhausted")
            self.assertEqual(result["endpoint_requests"]["used"], 0)
            self.assertEqual(result["pages_completed"], 0)
            self.assertEqual(result["records_count"], 0)
            self.assertFalse(result["complete"])
            self.assertFalse(result["resumable"])
        self.assertTrue(evidence["verification"]["html_default_unchanged"])
        self.assertFalse(evidence["verification"]["live_company_collection_tested"])


if __name__ == "__main__":
    unittest.main()
