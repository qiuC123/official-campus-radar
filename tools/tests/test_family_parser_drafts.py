import json
import unittest
from pathlib import Path

from tools.family_parser_drafts import (
    DraftParseError,
    load_family_drafts,
    parse_fixture,
    parse_html_positions,
    parse_json_positions,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "recruitment-family-parser-drafts-cycle-02.json"
FIXTURES = ROOT / "tools" / "tests" / "fixtures"


class FamilyParserDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.drafts = load_family_drafts(CONFIG)

    def test_four_family_drafts_are_present_and_browser_stays_unapproved(self) -> None:
        self.assertEqual(
            set(self.drafts),
            {
                "beisen_zhiye",
                "wintalent_classic",
                "wintalent_modern",
                "zhaopin_custom_campus",
            },
        )
        self.assertFalse(self.payload["production_browser_authorized"])
        self.assertFalse(self.payload["source_admission_claimed"])

    def test_beisen_html_extracts_stable_job_ids_and_dates(self) -> None:
        result = parse_fixture(
            FIXTURES / "family_beisen.html", self.drafts["beisen_zhiye"]
        )
        self.assertEqual(result["position_count"], 2)
        self.assertEqual(result["positions"][0]["position_key"], "621117741")
        self.assertEqual(result["positions"][0]["location"], "广东省-广州市")
        self.assertEqual(result["positions"][0]["source_date"], "2026-07-15")
        self.assertEqual(result["positions"][0]["source_date_role"], "published_on")
        self.assertEqual(
            result["positions"][0]["application_url"],
            "https://gac-toyota.zhiye.com/zpdetail/621117741",
        )

    def test_wintalent_classic_html_extracts_post_id_and_location(self) -> None:
        result = parse_fixture(
            FIXTURES / "family_wintalent_classic.html",
            self.drafts["wintalent_classic"],
        )
        self.assertEqual(
            [position["position_key"] for position in result["positions"]],
            ["e0dc294d8c59ece8", "12dd0a250f3c7974"],
        )
        self.assertEqual(result["positions"][1]["location"], "西宁市")
        self.assertFalse(
            self.drafts["wintalent_classic"]["pagination"]["production_supported"]
        )

    def test_wintalent_modern_json_extracts_post_id_and_total_pages(self) -> None:
        result = parse_fixture(
            FIXTURES / "family_wintalent_modern.json",
            self.drafts["wintalent_modern"],
        )
        self.assertEqual(result["position_count"], 2)
        self.assertEqual(result["total"], 4)
        self.assertEqual(
            result["positions"][1]["position_key"], "6a8bf9d14315481304cda9b9"
        )
        self.assertEqual(result["positions"][1]["source_date"], "2026-08-24")
        self.assertEqual(result["positions"][1]["source_date_role"], "published_on")
        self.assertEqual(
            self.drafts["wintalent_modern"]["minimal_headers_replay"], "passed"
        )

    def test_zhaopin_rendered_dom_extracts_detail_ids_but_stays_dev_only(self) -> None:
        result = parse_fixture(
            FIXTURES / "family_zhaopin_rendered.html",
            self.drafts["zhaopin_custom_campus"],
        )
        self.assertEqual(result["position_count"], 2)
        self.assertEqual(
            result["positions"][0]["position_key"], "CC145093010J40891059705"
        )
        self.assertEqual(result["positions"][1]["title"], "网络维护支撑")
        self.assertEqual(
            self.drafts["zhaopin_custom_campus"]["transport"],
            "rendered_dom_dev_only",
        )

    def test_html_parser_fails_closed_when_stable_identity_is_missing(self) -> None:
        with self.assertRaisesRegex(DraftParseError, "stable key"):
            parse_html_positions(
                "<table class='jobsTable'><tr><td>岗位</td><td></td><td>北京</td><td>2026-08-01</td></tr></table>",
                self.drafts["beisen_zhiye"],
            )

    def test_json_parser_fails_closed_when_location_is_missing(self) -> None:
        payload = {
            "data": {
                "pageForm": {
                    "totalPage": 1,
                    "pageData": [{"postId": "one", "postName": "岗位"}],
                }
            }
        }
        with self.assertRaisesRegex(DraftParseError, "missing stable key"):
            parse_json_positions(payload, self.drafts["wintalent_modern"])


if __name__ == "__main__":
    unittest.main()
