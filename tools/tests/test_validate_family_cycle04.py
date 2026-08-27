import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_family_cycle04 import (
    Cycle04Error,
    inspect_html,
    inspect_javascript,
    load_followups,
    load_targets,
    run_followups,
    run_page_one,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "targets-phase-02-t3-cycle-04.json"
FOLLOWUPS = ROOT / "tools" / "targets-phase-02-t3-cycle-04-followups.json"


class FamilyCycle04Tests(unittest.TestCase):
    def test_six_frozen_targets_have_one_page_one_request_each(self) -> None:
        payload = load_targets(CONFIG)
        self.assertEqual(len(payload["targets"]), 6)
        self.assertEqual(
            {target["expected_family"] for target in payload["targets"]},
            {"beisen_zhiye", "wintalent_classic"},
        )
        self.assertTrue(
            all(target["request_budget"]["page1_planned"] == 1 for target in payload["targets"])
        )

    def test_beisen_html_extracts_only_allowlisted_position_fields(self) -> None:
        target = {"expected_family": "beisen_zhiye"}
        html = """
        <html><head><title>校园招聘</title></head><body>
          <script>function gotoPage(pageIndex) { return pageIndex; }</script>
          <table class="jobsTable"><tr><td><a href="/zpdetail/123">研发工程师</a></td>
          <td>技术</td><td>北京市</td><td>2026-08-01</td></tr></table>
          <!-- zhiye.com --><input name="secret" value="not retained">
        </body></html>
        """
        result = inspect_html(html, target)
        self.assertEqual(result["position_samples"][0]["position_key"], "123")
        self.assertEqual(result["position_samples"][0]["title"], "研发工程师")
        self.assertIn("校园招聘", result["campus_terms"])
        self.assertNotIn("not retained", json.dumps(result, ensure_ascii=False))

    def test_wintalent_html_records_form_names_and_change_page_only(self) -> None:
        target = {"expected_family": "wintalent_classic"}
        html = """
        <html><head><title>校招岗位</title></head><body>
          <form id="pageForm" method="post" action="/jobs">
            <input name="currentPage" value="1"><input name="pageSize" value="10">
          </form>
          <script>changePage('/jobs', 2, 10)</script>
          <table class="search_result"><tr><td><a href="/detail?postIdEnc=abc">算法岗</a></td>
          <td>研发</td><td>硕士</td><td>上海市</td><td>2026-08-02</td></tr></table>
          <!-- /wt/ WinTalent -->
        </body></html>
        """
        result = inspect_html(html, target)
        self.assertEqual(result["position_samples"][0]["position_key"], "abc")
        self.assertEqual(result["forms"][0]["field_names"], ["currentPage", "pageSize"])
        self.assertTrue(any("changePage" in value for value in result["pagination_snippets"]))

    def test_invalid_budget_fails_before_network(self) -> None:
        payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        payload["targets"][0]["request_budget"]["page1_planned"] = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(Cycle04Error, "exactly one"):
                load_targets(path)

    def test_offline_run_makes_six_calls_and_persists_no_cookies(self) -> None:
        calls = []

        def fake_request(target):
            calls.append(target["id"])
            return 302, {"Location": "https://example.test/new"}, b""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = run_page_one(
                CONFIG,
                root / "report.json",
                root / "captures",
                requester=fake_request,
                delay_seconds=0,
            )
        self.assertEqual(len(calls), 6)
        self.assertEqual(report["requests_made"], 6)
        self.assertFalse(report["source_admission_claimed"])
        self.assertTrue(all(not item["cookies_sent"] for item in report["results"]))
        self.assertTrue(all(not item["redirects_followed"] for item in report["results"]))

    def test_followups_are_derived_and_stay_inside_each_budget(self) -> None:
        payload = load_followups(FOLLOWUPS)
        self.assertEqual(len(payload["followups"]), 4)
        for item in payload["followups"]:
            budget = item["request_budget"]
            self.assertEqual(budget["planned"], 1)
            self.assertLessEqual(
                budget["prior_requests"] + budget["planned"], budget["maximum"]
            )

    def test_javascript_inspection_keeps_candidate_strings_not_whole_bundle(self) -> None:
        javascript = "const a='/api/jobs/list'; const b='plain'; const c='/campus/position';"
        result = inspect_javascript(javascript)
        self.assertEqual(result["candidate_strings"], ["/api/jobs/list", "/campus/position"])
        self.assertNotIn("plain", result["candidate_strings"])

    def test_offline_followup_run_makes_one_call_per_frozen_item(self) -> None:
        calls = []

        def fake_request(target):
            calls.append(target["id"])
            return 200, {"Content-Type": "application/javascript"}, b"const x='/api/jobs';"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = run_followups(
                FOLLOWUPS,
                root / "report.json",
                root / "captures",
                requester=fake_request,
                delay_seconds=0,
            )
        self.assertEqual(len(calls), 4)
        self.assertEqual(report["requests_made"], 4)
        self.assertFalse(report["source_admission_claimed"])


if __name__ == "__main__":
    unittest.main()
