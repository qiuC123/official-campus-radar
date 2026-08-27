import copy
import json
import unittest
from pathlib import Path

from tools.validate_public_family_cycle11 import get_values, run, validate_target


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "api-acceptance-cycle-11-public-family.json"
OPPO_CONFIG = ROOT / "tools" / "api-acceptance-cycle-12-oppo.json"
TENCENT_CONFIG = ROOT / "tools" / "api-acceptance-cycle-13-tencent.json"
CATL_CONFIG = ROOT / "tools" / "api-acceptance-cycle-15-catl.json"


class PublicFamilyCycle11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_frozen_targets_are_the_five_expected_companies(self) -> None:
        self.assertEqual(
            [target["key"] for target in self.config["targets"]],
            ["P06", "P07", "P12", "P10", "P18"],
        )
        self.assertFalse(self.config["source_admission_claimed"])

    def test_cycle12_corrects_only_oppo_success_code(self) -> None:
        cycle12 = json.loads(OPPO_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(cycle12["cycle"], "Phase 02 / T3 Cycle 12")
        self.assertEqual([target["key"] for target in cycle12["targets"]], ["P12"])
        self.assertEqual(cycle12["targets"][0]["success"], {"path": "code", "expect": 0})

    def test_cycle13_freezes_current_tencent_mapping_ids(self) -> None:
        cycle13 = json.loads(TENCENT_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(cycle13["mapping_evidence"]["campus_mapping_ids"], [1, 14, 9])
        target = cycle13["targets"][0]
        self.assertEqual(target["request"]["projectIdList"], [])
        self.assertEqual(target["request"]["projectMappingIdList"], [1, 14, 9])

    def test_cycle15_uses_moka_offset_pagination(self) -> None:
        cycle15 = json.loads(CATL_CONFIG.read_text(encoding="utf-8"))
        target = cycle15["targets"][0]
        self.assertEqual(target["pagination"]["mode"], "offset")
        cursors = []

        def fake_request(_target, values):
            cursors.append(values["offset"])
            index = values["offset"] // 2
            rows = [
                {
                    "id": str(index * 2 + item),
                    "title": "岗位",
                    "locations": [{"city": "宁德市"}],
                    "status": "open",
                }
                for item in range(2 if index == 0 else 1)
            ]
            return 200, "application/json", {"total": 3, "jobs": rows}

        target = copy.deepcopy(target)
        target["pagination"].update(page_size=2, max_pages=2)
        result = validate_target(target, fake_request)
        self.assertTrue(result["passed"])
        self.assertEqual(cursors, [0, 2])

    def test_array_path_extracts_nested_locations(self) -> None:
        row = {"requirements": [{"city": "北京"}, {"city": "上海"}]}
        self.assertEqual(
            get_values(row, "requirements[].city"), ["北京", "上海"]
        )

    def test_complete_unique_rows_with_scope_pass(self) -> None:
        target = copy.deepcopy(self.config["targets"][2])
        target["pagination"]["page_size"] = 2
        target["pagination"]["max_pages"] = 2

        def fake_request(_target, values):
            page = values["pageNum"]
            rows = [
                {
                    "idRecruitPosition": page,
                    "positionName": f"岗位 {page}",
                    "workCityName": "深圳市",
                    "recruitmentType": "Graduate",
                }
            ]
            return 200, "application/json", {
                "code": 200,
                "data": {"total": 1, "records": rows},
            }

        result = validate_target(target, fake_request)
        self.assertTrue(result["passed"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["scope_raw_values"], ["Graduate"])

    def test_missing_location_or_wrong_scope_fails_closed(self) -> None:
        target = copy.deepcopy(self.config["targets"][2])
        for row in (
            {
                "idRecruitPosition": 1,
                "positionName": "岗位",
                "workCityName": "",
                "recruitmentType": "Graduate",
            },
            {
                "idRecruitPosition": 1,
                "positionName": "岗位",
                "workCityName": "深圳",
                "recruitmentType": "Social",
            },
        ):
            with self.subTest(row=row):
                result = validate_target(
                    target,
                    lambda *_args, row=row: (
                        200,
                        "application/json",
                        {"code": 200, "data": {"total": 1, "records": [row]}},
                    ),
                )
                self.assertFalse(result["passed"])

    def test_report_does_not_persist_unlisted_fields(self) -> None:
        def fake_request(target, _values):
            row = {
                target["id_field"]: "1",
                target["title_field"]: "岗位",
                "secret": "not persisted",
            }
            first_location = target["location_paths"][0]
            if "[]" not in first_location and "." not in first_location:
                row[first_location] = "北京"
            elif target["key"] == "P07":
                row["requirementVoList"] = [{"workCity": "北京"}]
            elif target["key"] == "P10":
                row["workPlaceNameList"] = ["北京"]
            scope = target.get("scope")
            if scope:
                row[scope["field"]] = scope["allowed"][0]
            payload = {}
            current = payload
            for part in target["list_path"].split(".")[:-1]:
                current[part] = {}
                current = current[part]
            current[target["list_path"].split(".")[-1]] = [row]
            current = payload
            for part in target["total_path"].split(".")[:-1]:
                current = current.setdefault(part, {})
            current[target["total_path"].split(".")[-1]] = 1
            success = target.get("success")
            if success:
                current = payload
                for part in success["path"].split(".")[:-1]:
                    current = current.setdefault(part, {})
                current[success["path"].split(".")[-1]] = success["expect"]
            return 200, "application/json", payload

        report = run(CONFIG, fake_request)
        self.assertFalse(report["source_admission_claimed"])
        self.assertFalse(report["raw_response_persisted"])
        self.assertNotIn("secret", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
