from collections import Counter
from contextlib import redirect_stdout
from io import StringIO
import json
import unittest
from unittest.mock import patch

from tools.validate_xiaomi_browser_sample import Budget, JOB_ENDPOINT, REPORT, endpoint, job_sample, main, sample_verdict


class XiaomiBrowserSampleTests(unittest.TestCase):
    def test_default_command_does_not_start_browser(self):
        with patch("sys.argv", ["validate_xiaomi_browser_sample.py"]), patch(
            "tools.validate_xiaomi_browser_sample.experiment"
        ) as experiment, redirect_stdout(StringIO()) as output:
            self.assertEqual(main(), 0)
        experiment.assert_not_called()
        self.assertTrue(json.loads(output.getvalue())["dry_run"])

    def test_frozen_live_report_matches_budget_and_verdict(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        used = Counter({JOB_ENDPOINT: 1})
        for event in report["endpoint_request_events"]:
            used[event["endpoint"]] += 1
            self.assertEqual(event["cumulative_count"], used[event["endpoint"]])
            self.assertLessEqual(used[event["endpoint"]], 6)
        self.assertEqual(dict(used), report["cumulative_endpoint_counts"])
        self.assertEqual(report["verdict"], sample_verdict(report["pages"], report["stop_reason"]))

    def test_mcp_http_inspection_did_not_spend_job_or_telemetry_budget(self):
        record = json.loads(REPORT.with_name("company-expansion-xiaomi-mcp-http-20260907.json").read_text(encoding="utf-8"))
        actual = record["result"]["endpoint_requests"]
        self.assertEqual(actual["used"], 2)
        self.assertEqual(actual["by_method_endpoint"], {
            "GET xiaomi.jobs.f.mioffice.cn/campus/": 1,
            "GET xiaomi.jobs.f.mioffice.cn/robots.txt": 1,
        })
        self.assertEqual(record["interpretation"]["known_cumulative_job_requests"], 4)
        self.assertFalse(record["interpretation"]["full_collection_verified"])

    def test_previous_request_leaves_five_and_stops_all_endpoints(self):
        budget = Budget()
        self.assertTrue(all(budget.allow(JOB_ENDPOINT) for _ in range(5)))
        self.assertFalse(budget.allow(JOB_ENDPOINT))
        self.assertFalse(budget.allow("GET https://example.com/another"))
        self.assertEqual(budget.used[JOB_ENDPOINT], 6)

    def test_approved_mcp_browser_ledger_reconciles_all_request_views_and_history(self):
        record = json.loads(REPORT.with_name("company-expansion-xiaomi-mcp-browser-20260907.json").read_text(encoding="utf-8"))
        aggregate = record["aggregate"]
        by_endpoint = Counter()
        for call in record["calls"]:
            actual = call["result"]["endpoint_requests"]
            self.assertEqual(sum(actual["by_endpoint"].values()), actual["used"])
            self.assertEqual(sum(actual["by_purpose"].values()), actual["used"])
            by_method = Counter()
            for key, count in actual["by_method_endpoint"].items():
                method, endpoint_key = key.split(" ", 1)
                self.assertIn(method, {"GET", "POST"})
                self.assertNotIn("?", endpoint_key)
                by_method[endpoint_key] += count
            self.assertEqual(dict(by_method), actual["by_endpoint"])
            self.assertLessEqual(actual["used"], call["arguments"]["endpoint_limit"])
            by_endpoint.update(actual["by_endpoint"])
        self.assertEqual(sum(by_endpoint.values()), aggregate["request_used"])
        self.assertEqual(aggregate["request_used"] + aggregate["unspent_request_allowance"], record["authorization"]["requests"])
        job_key = "xiaomi.jobs.f.mioffice.cn/api/v1/search/job/posts"
        self.assertEqual(by_endpoint[job_key], aggregate["job_requests_used"])
        old = json.loads(REPORT.read_text(encoding="utf-8"))
        prior = old["cumulative_endpoint_counts"][JOB_ENDPOINT]
        self.assertEqual(prior, record["historical"]["known_job_requests_before"])
        self.assertEqual(prior + by_endpoint[job_key], aggregate["known_job_requests_cumulative"])
        for endpoint_key, used in by_endpoint.items():
            cap = record["authorization"]["jobRequests" if endpoint_key == job_key else "otherEndpointRequests"]
            self.assertLessEqual(used, cap)

    def test_approved_mcp_call_exhaustion_stops_round_despite_unspent_total_allowance(self):
        record = json.loads(REPORT.with_name("company-expansion-xiaomi-mcp-browser-20260907.json").read_text(encoding="utf-8"))
        self.assertEqual(len(record["calls"]), 1)
        result = record["calls"][0]["result"]
        self.assertEqual(result["inspection_status"], "endpoint_budget_exhausted")
        self.assertEqual(result["endpoint_requests"]["remaining"], 0)
        self.assertGreater(record["aggregate"]["unspent_request_allowance"], 0)
        self.assertTrue(record["aggregate"]["round_stopped"])
        self.assertFalse(record["aggregate"]["unspent_allowance_reusable_in_this_round"])
        self.assertEqual(record["aggregate"]["followup_calls"], 0)
        self.assertEqual(record["aggregate"]["logical_pages_captured"], 0)
        self.assertEqual(record["aggregate"]["pagination_clicks"], 0)
        self.assertIsNone(result["status"])
        self.assertFalse(result["sanitized_html_excerpt"])
        for field in ("sample_complete", "natural_pagination_verified", "site_access_restriction_proven",
                      "job_response_captured", "current_applicability_verified", "full_collection_verified", "production_admitted"):
            self.assertFalse(record["conclusions"][field])

    def test_denial_stops_every_endpoint_without_retry(self):
        for status in (401, 403, 412, 429):
            budget = Budget()
            budget.response_status(status)
            self.assertFalse(budget.allow(JOB_ENDPOINT))
            self.assertEqual(budget.used[JOB_ENDPOINT], 1)

    def test_request_identity_never_retains_signature_or_csrf_values(self):
        result = endpoint("POST", "https://example.com/jobs?_signature=secret&_csrf=secret")
        self.assertEqual(result, "POST https://example.com/jobs")

    def test_only_job_business_fields_are_retained(self):
        sample = job_sample({"data": {"count": 10, "job_post_list": [{"id": "a", "title": "Engineer",
                             "token": "secret", "job_category": {"name": "R&D", "csrf": "secret"}}]}})
        self.assertEqual(sample["rows"], [{"id": "a", "title": "Engineer", "job_category": {"name": "R&D"}}])

    def test_missing_or_duplicate_ids_cannot_prove_distinct_pages(self):
        for rows in ([{"title": "Engineer"}], [{"id": "a"}, {"id": "a"}]):
            self.assertFalse(job_sample({"data": {"count": 5, "job_post_list": rows}})["identity_complete"])

    def test_sample_never_proves_full_collection_or_admission(self):
        a = job_sample({"data": {"count": 767, "job_post_list": [{"id": "a"}]}})
        b = job_sample({"data": {"count": 767, "job_post_list": [{"id": "b"}]}})
        pages = [{"stage": "campus:first", "job_responses": [a]}, {"stage": "campus:next", "job_responses": [b]}]
        verdict = sample_verdict(pages, None)
        self.assertTrue(verdict["two_distinct_campus_pages"])
        self.assertFalse(verdict["full_collection_verified"])
        self.assertFalse(verdict["production_admitted"])
        self.assertFalse(sample_verdict(pages, "access_restricted_http_403")["two_distinct_campus_pages"])
        b["ids"] = ["a"]
        self.assertFalse(sample_verdict(pages, None)["two_distinct_campus_pages"])


if __name__ == "__main__":
    unittest.main()
