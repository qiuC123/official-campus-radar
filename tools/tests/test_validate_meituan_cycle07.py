import json
import unittest
from pathlib import Path

from tools.validate_meituan_cycle07 import AcceptanceError, run, validate_target


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "api-acceptance-cycle-07-meituan.json"


class MeituanCycle07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.target = cls.config["target"]

    def row(self, job_id: str, job_type: str = "2") -> dict:
        return {
            "jobUnionId": job_id,
            "name": f"岗位 {job_id}",
            "cityList": [{"name": "北京市"}],
            "jobType": job_type,
            "jobStatus": "000",
            "firstPostTime": None,
        }

    def test_budget_is_only_the_sixth_request_and_page_two(self) -> None:
        self.assertEqual(
            self.target["request_budget"],
            {"maximum": 6, "already_spent": 5, "planned": 1},
        )
        self.assertEqual(self.target["body"]["page"], {"pageNo": 2, "pageSize": 10})
        self.assertFalse(self.config["source_admission_claimed"])

    def test_nonempty_distinct_page_with_required_fields_passes(self) -> None:
        def fake_request(_target):
            return 200, "application/json; charset=utf-8", {
                "data": {
                    "page": {"totalPage": 3},
                    "list": [self.row("page-two-1"), self.row("page-two-2")],
                }
            }

        result = validate_target(self.target, fake_request)

        self.assertTrue(result["passed"])
        self.assertTrue(result["different_from_observed_page_one"])
        self.assertEqual(result["campus_raw_values"], ["2"])

    def test_overlap_missing_field_or_wrong_scope_fails_closed(self) -> None:
        cases = [
            [self.row(self.target["observed_page_one_ids"][0])],
            [{**self.row("new-id"), "cityList": []}],
            [self.row("new-id", job_type="1")],
        ]
        for rows in cases:
            with self.subTest(rows=rows):
                result = validate_target(
                    self.target,
                    lambda _target, rows=rows: (
                        200,
                        "application/json",
                        {"data": {"page": {"totalPage": 3}, "list": rows}},
                    ),
                )
                self.assertFalse(result["passed"])

    def test_invalid_budget_is_rejected_before_request(self) -> None:
        target = json.loads(json.dumps(self.target))
        target["request_budget"]["planned"] = 2
        with self.assertRaisesRegex(AcceptanceError, "sixth and final"):
            validate_target(target, lambda *_args: self.fail("request must not run"))

    def test_report_does_not_store_unlisted_fields_or_claim_admission(self) -> None:
        def fake_request(_target):
            row = self.row("page-two")
            row["secret"] = "not persisted"
            return 200, "application/json", {
                "data": {"page": {"totalPage": 3}, "list": [row]}
            }

        report = run(CONFIG, fake_request)

        self.assertTrue(report["passed"])
        self.assertFalse(report["source_admission_claimed"])
        self.assertFalse(report["database_writes"])
        self.assertFalse(report["raw_response_persisted"])
        self.assertNotIn("secret", report["result"]["samples"][0])


if __name__ == "__main__":
    unittest.main()
