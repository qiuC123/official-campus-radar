import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_live_api_cycle03 import (
    AcceptanceError,
    make_values,
    run,
    validate_target,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "api-acceptance-cycle-03.json"


class LiveApiCycle03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.targets = {target["key"]: target for target in cls.config["targets"]}

    def test_request_shapes_include_two_page_parameters(self) -> None:
        pdd = make_values(self.targets["pinduoduo"], 2)
        li_auto = make_values(self.targets["li_auto"], 2)
        crrc = make_values(self.targets["crrc"], 2)
        self.assertEqual((pdd["page"], pdd["pageSize"]), (2, 10))
        self.assertEqual((li_auto["page"], li_auto["page_size"]), (2, 10))
        self.assertEqual((crrc["currentPage"], crrc["pageSize"]), (2, 10))
        self.assertEqual(crrc["recruitType"], "1")

    def test_crrc_budget_includes_three_discovery_requests(self) -> None:
        budget = self.targets["crrc"]["request_budget"]
        self.assertEqual(budget["already_spent"], 3)
        self.assertEqual(budget["already_spent"] + budget["planned"], 5)
        self.assertLessEqual(5, budget["maximum"])

    def test_distinct_pages_and_raw_campus_value_pass(self) -> None:
        target = self.targets["pinduoduo"]

        def fake_request(_target, values):
            page = values["page"]
            return 200, "application/json; charset=utf-8", {
                "result": {
                    "list": [
                        {
                            "id": f"p{page}",
                            "jobName": f"岗位{page}",
                            "workLocation": "上海",
                            "releaseTime": "2026-08-20",
                            "recruitTypeName": "管培生",
                            "secret": "must not be persisted",
                        }
                    ]
                }
            }

        result = validate_target(target, fake_request)
        self.assertTrue(result["passed"])
        self.assertEqual(result["requests_made"], 2)
        self.assertEqual(result["campus_evidence"]["raw_values"], ["管培生"])
        self.assertNotIn("secret", result["pages"][0]["samples"][0])

    def test_repeated_page_ids_fail_closed(self) -> None:
        target = self.targets["li_auto"]

        def fake_request(_target, _values):
            return 200, "application/json", {
                "data": {
                    "items": [{"id": "same", "title": "实习生", "location_title": "北京"}],
                    "total_pages": 3,
                }
            }

        result = validate_target(target, fake_request)
        self.assertFalse(result["passed"])
        self.assertFalse(result["pagination"]["passed"])

    def test_missing_required_field_fails_closed(self) -> None:
        target = self.targets["crrc"]

        def fake_request(_target, values):
            page = values["currentPage"]
            return 200, "application/json", {
                "data": {
                    "pageForm": {
                        "pageData": [{"postId": f"c{page}", "postName": ""}],
                        "totalPage": 2,
                    }
                }
            }

        result = validate_target(target, fake_request)
        self.assertFalse(result["passed"])
        self.assertEqual(result["pages"][0]["missing_required_fields"], ["postName"])

    def test_budget_overrun_is_rejected_before_request(self) -> None:
        target = json.loads(json.dumps(self.targets["crrc"]))
        target["request_budget"] = {"maximum": 4, "already_spent": 3, "planned": 2}
        with self.assertRaisesRegex(AcceptanceError, "budget exceeded"):
            validate_target(target, lambda *_args: self.fail("request must not run"))

    def test_full_offline_run_has_no_database_or_admission_claim(self) -> None:
        def fake_request(target, values):
            page_key = target["pagination"]["page_param"]
            page = values[page_key]
            if target["key"] == "pinduoduo":
                payload = {"result": {"list": [{"id": f"p{page}", "jobName": "岗位", "recruitTypeName": "校招"}]}}
            elif target["key"] == "li_auto":
                payload = {"data": {"items": [{"id": f"l{page}", "title": "实习"}], "total_pages": 2}}
            else:
                payload = {"data": {"pageForm": {"pageData": [{"postId": f"c{page}", "postName": "岗位"}], "totalPage": 2}}}
            return 200, "application/json", payload

        report = run(CONFIG, fake_request)
        self.assertTrue(report["passed"])
        self.assertFalse(report["source_admission_claimed"])
        self.assertFalse(report["database_writes"])
        self.assertFalse(report["raw_responses_persisted"])


if __name__ == "__main__":
    unittest.main()
