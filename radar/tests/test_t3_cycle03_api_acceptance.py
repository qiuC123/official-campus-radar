import json
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase

from radar.collectors.base import FetchedPage
from radar.collectors.json_api import JsonApiSourceAdapter


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "work" / "phase-02-t3-api-acceptance-cycle-03.json"


class T3Cycle03AdapterExtractionTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.results = {result["key"]: result for result in report["results"]}

    def canonical_page(self, key: str) -> tuple[SimpleNamespace, FetchedPage]:
        result = self.results[key]
        rows = [sample for page in result["pages"] for sample in page["samples"]]
        if key == "pinduoduo":
            rows = [
                {**row, "name": f"真实职位-{row['id']}"}
                for row in rows
            ]
        definitions = {
            "pinduoduo": {
                "list_path": "result.list",
                "document": {"result": {"list": rows}},
                "field_map": {"position_key": "id", "title": "name", "location": "workLocation"},
                "title": "拼多多校园招聘",
                "official_page_url": "https://careers.pddglobalhr.com/campus/grad",
                "target_audience": "管培生",
            },
            "li_auto": {
                "list_path": "data.items",
                "document": {"data": {"items": rows}},
                "field_map": {"position_key": "id", "title": "title", "location": "location_title"},
                "title": "理想汽车校园招聘",
                "official_page_url": "https://www.lixiang.com/employ/campus/list.html",
                "target_audience": "校招/实习",
            },
            "crrc": {
                "list_path": "data.pageForm.pageData",
                "document": {"data": {"pageForm": {"pageData": rows}}},
                "field_map": {"position_key": "postId", "title": "postName", "location": "workPlaceStr"},
                "title": "中国中车校园招聘",
                "official_page_url": "https://sp.wintalent.cn/CRRC/homeMobile/index.html",
                "target_audience": "校招",
            },
        }
        definition = definitions[key]
        document = definition["document"]
        document["_radar"] = {
            "list_path": definition["list_path"],
            "positions_complete": False,
            "batch": {
                "identity_key": f"cycle03-{key}",
                "title": definition["title"],
                "official_page_url": definition["official_page_url"],
                "recruitment_type": "campus_recruitment",
                "target_audience": definition["target_audience"],
            },
            "field_map": definition["field_map"],
            "valid_values": {},
            "html_fields": [],
        }
        source = SimpleNamespace()
        page = FetchedPage(
            result["endpoint"],
            json.dumps(document, ensure_ascii=False),
            "cycle03-sanitized-evidence",
            200,
            None,
        )
        return source, page

    def test_saved_samples_extract_with_current_batch_position_contract(self) -> None:
        expected_counts = {"pinduoduo": 8, "li_auto": 10, "crrc": 10}
        adapter = JsonApiSourceAdapter()

        for key, expected_count in expected_counts.items():
            with self.subTest(target=key):
                source, page = self.canonical_page(key)
                candidate = adapter.extract(source, page)[0]
                self.assertEqual(len(candidate.positions), expected_count)
                self.assertTrue(all(position.position_key for position in candidate.positions))
                self.assertTrue(all(position.title for position in candidate.positions))
                self.assertFalse(candidate.positions_complete)

    def test_publish_dates_are_not_misrepresented_as_official_updates(self) -> None:
        adapter = JsonApiSourceAdapter()

        for key in self.results:
            with self.subTest(target=key):
                source, page = self.canonical_page(key)
                candidate = adapter.extract(source, page)[0]
                self.assertTrue(
                    all(position.source_updated_on is None for position in candidate.positions)
                )

    def test_crrc_parses_offline_but_live_transport_stays_explicitly_unsupported(self) -> None:
        result = self.results["crrc"]
        source, page = self.canonical_page("crrc")
        candidate = JsonApiSourceAdapter().extract(source, page)[0]

        self.assertEqual(candidate.positions[0].title, "市场投标报价岗")
        self.assertFalse(result["adapter_transport_supported"])
        self.assertIn("x-www-form-urlencoded", result["adapter_note"])
