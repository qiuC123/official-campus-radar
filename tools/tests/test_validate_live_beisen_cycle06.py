import json
import unittest
from pathlib import Path

from tools.validate_live_beisen_cycle06 import (
    AcceptanceError,
    make_body,
    run,
    validate_target,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "api-acceptance-cycle-06-beisen.json"


class LiveBeisenCycle06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.target = cls.config["targets"][0]

    def test_only_vivo_is_requested_and_empty_csvw_campus_is_skipped(self) -> None:
        self.assertEqual([target["key"] for target in self.config["targets"]], ["vivo_autumn_campus"])
        skipped = self.config["skipped_targets"]
        self.assertEqual(skipped[0]["key"], "saic_volkswagen_campus")
        self.assertEqual(skipped[0]["api_requests_planned"], 0)
        self.assertIn("共 0 个", skipped[0]["reason"])

    def test_request_body_uses_observed_autumn_filter_and_zero_based_pages(self) -> None:
        first = make_body(self.target, 0)
        second = make_body(self.target, 1)
        self.assertEqual(first["ClassificationOne"], ["2"])
        self.assertEqual((first["PageIndex"], second["PageIndex"]), (0, 1))
        self.assertEqual(first["PageSize"], 20)

    def test_two_distinct_pages_with_required_fields_pass(self) -> None:
        def fake_request(_target, body):
            page = body["PageIndex"]
            return 200, "application/json; charset=utf-8", {
                "Code": 200,
                "Count": 137,
                "Data": [
                    {
                        "JobAdId": 100 + page,
                        "JobAdName": f"工程师{page}",
                        "LocNames": ["深圳"],
                        "Category": "秋季校园招聘",
                        "secret": "not persisted",
                    }
                ],
            }

        result = validate_target(self.target, fake_request)

        self.assertTrue(result["passed"])
        self.assertEqual(result["requests_made"], 2)
        self.assertEqual(result["campus_evidence"]["raw_value"], ["2"])
        self.assertNotIn("secret", result["pages"][0]["samples"][0])

    def test_repeated_page_or_missing_location_fails_closed(self) -> None:
        def fake_request(_target, _body):
            return 200, "application/json", {
                "Code": 200,
                "Count": 137,
                "Data": [{"JobAdId": 100, "JobAdName": "工程师", "LocNames": []}],
            }

        result = validate_target(self.target, fake_request)

        self.assertFalse(result["passed"])
        self.assertFalse(result["pagination"]["passed"])
        self.assertFalse(result["required_fields_passed"])

    def test_budget_overrun_is_rejected_before_request(self) -> None:
        target = json.loads(json.dumps(self.target))
        target["request_budget"] = {"maximum": 1, "already_spent": 0, "planned": 2}
        with self.assertRaisesRegex(AcceptanceError, "budget exceeded"):
            validate_target(target, lambda *_args: self.fail("request must not run"))

    def test_report_never_claims_admission_or_raw_response_storage(self) -> None:
        def fake_request(_target, body):
            page = body["PageIndex"]
            return 200, "application/json", {
                "Code": 200,
                "Count": 40,
                "Data": [
                    {
                        "JobAdId": page + 1,
                        "JobAdName": "岗位",
                        "LocNames": ["东莞"],
                    }
                ],
            }

        report = run(CONFIG, fake_request)

        self.assertTrue(report["passed"])
        self.assertFalse(report["source_admission_claimed"])
        self.assertFalse(report["database_writes"])
        self.assertFalse(report["raw_responses_persisted"])


if __name__ == "__main__":
    unittest.main()
