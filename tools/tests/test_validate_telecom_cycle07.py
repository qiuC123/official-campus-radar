import json
import unittest
from pathlib import Path

from tools.validate_telecom_cycle07 import (
    CompletenessError,
    run,
    validate_target,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "api-completeness-cycle-07-telecom.json"


class TelecomCycle07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.target = cls.config["target"]

    def test_budget_is_exactly_one_anonymous_empty_body_request(self) -> None:
        self.assertEqual(self.target["body"], {})
        self.assertEqual(
            self.target["request_budget"],
            {"maximum": 1, "already_spent": 0, "planned": 1},
        )
        self.assertFalse(self.config["source_admission_claimed"])

    def test_equal_nonempty_count_unique_ids_and_campus_rows_pass(self) -> None:
        def fake_request(_target):
            return 200, "application/json; charset=utf-8", {
                "data": {
                    "rowCount": 2,
                    "details": [
                        {
                            "PostId": 1,
                            "PostName": "岗位一",
                            "WorkPlace": "北京市",
                            "RecruitTypeName": "校园招聘",
                        },
                        {
                            "PostId": 2,
                            "PostName": "岗位二",
                            "WorkPlace": "北京市",
                            "RecruitTypeName": "校园招聘",
                        },
                    ],
                }
            }

        result = validate_target(self.target, fake_request)

        self.assertTrue(result["passed"])
        self.assertTrue(result["list_is_complete"])
        self.assertEqual(result["row_count"], result["reported_total"])
        self.assertEqual(result["campus_raw_values"], ["校园招聘"])

    def test_partial_or_mixed_scope_list_fails_closed(self) -> None:
        def fake_request(_target):
            return 200, "application/json", {
                "data": {
                    "rowCount": 3,
                    "details": [
                        {
                            "PostId": 1,
                            "PostName": "岗位一",
                            "WorkPlace": "北京市",
                            "RecruitTypeName": "校园招聘",
                        },
                        {
                            "PostId": 2,
                            "PostName": "岗位二",
                            "WorkPlace": "北京市",
                            "RecruitTypeName": "社会招聘",
                        },
                    ],
                }
            }

        result = validate_target(self.target, fake_request)

        self.assertFalse(result["passed"])
        self.assertFalse(result["list_is_complete"])
        self.assertEqual(result["campus_raw_values"], ["校园招聘", "社会招聘"])

    def test_invalid_budget_is_rejected_before_request(self) -> None:
        target = json.loads(json.dumps(self.target))
        target["request_budget"]["planned"] = 2
        with self.assertRaisesRegex(CompletenessError, "exactly one"):
            validate_target(target, lambda *_args: self.fail("request must not run"))

    def test_report_does_not_store_raw_response_or_claim_admission(self) -> None:
        def fake_request(_target):
            return 200, "application/json", {
                "data": {
                    "rowCount": 1,
                    "details": [
                        {
                            "PostId": 1,
                            "PostName": "岗位",
                            "WorkPlace": "北京",
                            "RecruitTypeName": "校园招聘",
                            "secret": "not persisted",
                        }
                    ],
                }
            }

        report = run(CONFIG, fake_request)

        self.assertTrue(report["passed"])
        self.assertFalse(report["source_admission_claimed"])
        self.assertFalse(report["database_writes"])
        self.assertFalse(report["raw_response_persisted"])
        self.assertNotIn("secret", report["result"]["samples"][0])


if __name__ == "__main__":
    unittest.main()
