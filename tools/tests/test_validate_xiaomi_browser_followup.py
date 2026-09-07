from contextlib import redirect_stdout
from io import StringIO
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


if __name__ == "__main__":
    unittest.main()
