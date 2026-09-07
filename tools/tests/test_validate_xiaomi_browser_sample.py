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

    def test_previous_request_leaves_five_and_stops_all_endpoints(self):
        budget = Budget()
        self.assertTrue(all(budget.allow(JOB_ENDPOINT) for _ in range(5)))
        self.assertFalse(budget.allow(JOB_ENDPOINT))
        self.assertFalse(budget.allow("GET https://example.com/another"))
        self.assertEqual(budget.used[JOB_ENDPOINT], 6)

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
