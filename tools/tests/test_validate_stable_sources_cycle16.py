import copy
import json
import unittest
from pathlib import Path

from tools.validate_stable_sources_cycle16 import (
    get_values,
    parse_apple_hydration,
    parse_gac_toyota_jobs,
    run,
    validate_target,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "api-acceptance-cycle-16-seven-sources.json"
CYCLE17_CONFIG = ROOT / "tools" / "api-acceptance-cycle-17-faw-midea-pagination.json"
CYCLE18_CONFIG = ROOT / "tools" / "api-acceptance-cycle-18-evidence-backfill.json"


class StableSourcesCycle16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_cycle_contains_the_seven_expected_frozen_companies(self) -> None:
        self.assertEqual(
            [target["key"] for target in self.config["targets"]],
            ["J02", "P17", "P19", "S03", "S04", "F02", "F06"],
        )
        self.assertFalse(self.config["source_admission_claimed"])

    def test_cycle17_retries_only_server_capped_sources_at_ten_rows(self) -> None:
        config = json.loads(CYCLE17_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual([target["key"] for target in config["targets"]], ["J02", "P17"])
        self.assertTrue(config["retry_reason"])
        self.assertEqual(
            [target["pagination"]["page_size"] for target in config["targets"]],
            [10, 10],
        )

    def test_cycle18_backfills_six_expected_sources(self) -> None:
        config = json.loads(CYCLE18_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(
            [target["key"] for target in config["targets"]],
            ["P02", "P14", "P16", "J04", "F05", "J03"],
        )

    def test_gac_toyota_server_html_parser_detects_rows_and_empty_pager(self) -> None:
        document = parse_gac_toyota_jobs(
            '<table class="jobsTable"><tr class="title"><td>职位</td></tr>'
            '<tr><td><a href="/zpdetail/1">应届可投</a></td><td></td>'
            '<td>广州</td><td>2026-08-01</td></tr></table><div class="pager"></div>'
        )
        self.assertEqual(document["total"], 1)
        self.assertEqual(document["jobs"][0]["location"], "广州")
        self.assertEqual(document["pager_link_count"], 0)

    def test_nested_array_values_are_readable(self) -> None:
        row = {"locations": [{"name": "上海"}, {"name": "深圳"}]}
        self.assertEqual(get_values(row, "locations[].name"), ["上海", "深圳"])

    def test_apple_hydration_parser_decodes_server_payload(self) -> None:
        payload = {"loaderData": {"search": {"totalRecords": 1}}}
        encoded = json.dumps(json.dumps(payload))
        html = (
            '<script nonce="x">window.__staticRouterHydrationData = '
            f"JSON.parse({encoded});</script>"
        )
        self.assertEqual(parse_apple_hydration(html), payload)

    def test_complete_filtered_source_passes_and_counts_only_matching_rows(self) -> None:
        target = copy.deepcopy(self.config["targets"][5])
        target["pagination"].update(page_size=1, max_pages=2)

        def fake_request(_target, values):
            offset = values["offset"]
            rows = [
                {
                    "id": str(offset + 1),
                    "title": "Intern",
                    "location": "Shanghai" if offset == 0 else "Seattle",
                    "country_code": "CHN" if offset == 0 else "USA",
                }
            ]
            return 200, "application/json", {"hits": 2, "jobs": rows}

        result = validate_target(target, fake_request)
        self.assertTrue(result["passed"])
        self.assertEqual(result["unique_ids"], 2)
        self.assertEqual(result["accepted_unique_ids"], 1)

    def test_missing_location_fails_closed(self) -> None:
        target = copy.deepcopy(self.config["targets"][2])
        target["pagination"].update(page_size=1, max_pages=1)
        row = {
            "id": "1",
            "jobName": "岗位",
            "workPlace": "",
            "batch": 2027,
            "campusNature": "008501",
        }
        result = validate_target(
            target,
            lambda *_args: (
                200,
                "application/json",
                {"code": 0, "data": [row], "page": {"totalCount": 1}},
            ),
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["missing_required_fields"], ["location"])

    def test_report_does_not_persist_unlisted_fields(self) -> None:
        def fake_request(target, _values):
            row = {
                "id": "1",
                "postingTitle": "Intern",
                "locations": [{"name": "上海"}],
                "secret": "not persisted",
            }
            payload = {
                "loaderData": {
                    "search": {"totalRecords": 1, "searchResults": [row]}
                }
            }
            return 200, "text/html", payload

        one = copy.deepcopy(self.config)
        one["targets"] = [one["targets"][-1]]
        temp = ROOT / "work" / "cycle16-test-config.json"
        try:
            temp.write_text(json.dumps(one), encoding="utf-8")
            report = run(temp, fake_request)
        finally:
            temp.unlink(missing_ok=True)
        self.assertFalse(report["raw_response_persisted"])
        self.assertNotIn("secret", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
