import copy
import json
from unittest.mock import patch

from django.test import TestCase

from radar.collectors.isolated_browser_json import IsolatedBrowserJsonSourceAdapter
from radar.collectors.registry import AdapterRegistry
from radar.models import OfficialSource, Organization
from tools.build_t4_source_catalog import build_rows
from tools.t6_cycle03_unicom_config import COMPANY, corrected_parser_config
from tools.t6_cycle05_unicom_browser_config import browser_parser_config


class IsolatedBrowserJsonAdapterTests(TestCase):
    def setUp(self) -> None:
        row = next(
            row for row in build_rows() if row["organization_name"] == COMPANY
        )
        base_config = corrected_parser_config(json.loads(row["parser_config"]))
        organization = Organization.objects.create(
            name=COMPANY,
            company_type="state_owned",
            industry="通信",
            official_domain="chinaunicom.com.cn",
        )
        self.source = OfficialSource.objects.create(
            organization=organization,
            source_type=OfficialSource.SourceType.ATS,
            source_url="https://zglt.zhaopin.com/",
            official_entrypoint_url=(
                "https://www.chinaunicom.com.cn/46/menu01/528/column06"
            ),
            admission_evidence="reviewed official entrypoint",
            adapter_name="isolated_browser_json",
            parser_config=browser_parser_config(base_config),
        )

    @staticmethod
    def _payload(rows: list[dict], total: int | None = None) -> dict:
        return {
            "code": 200,
            "data": {
                "jobList": rows,
                "pageInfo": {"totalNum": len(rows) if total is None else total},
            },
        }

    @staticmethod
    def _row(key: str, title: str = "软件开发工程师") -> dict:
        return {
            "job": {
                "id": key,
                "title": title,
                "cityName": "北京",
                "modifiedTime": "2026-08-27T08:00:00+08:00",
            }
        }

    def test_registry_validates_the_narrow_reviewed_source(self) -> None:
        AdapterRegistry.validate_source_config(self.source)
        self.assertIsInstance(
            AdapterRegistry.get(self.source), IsolatedBrowserJsonSourceAdapter
        )

    def test_forbidden_profile_or_proxy_settings_are_rejected(self) -> None:
        for forbidden_name in ("user_data_dir", "storage_state", "proxy", "cookies"):
            with self.subTest(forbidden_name=forbidden_name):
                source = copy.copy(self.source)
                source.parser_config = copy.deepcopy(self.source.parser_config)
                source.parser_config["isolated_browser"][forbidden_name] = "forbidden"
                with self.assertRaisesMessage(ValueError, "forbidden settings"):
                    IsolatedBrowserJsonSourceAdapter.validate_source_config(source)

    def test_fetch_reuses_json_extraction_contract(self) -> None:
        adapter = IsolatedBrowserJsonSourceAdapter()
        rows = [self._row("job-1"), self._row("job-2", "数据分析师")]
        with patch.object(adapter, "_collect_payloads", return_value=([self._payload(rows)], 200)):
            fetched = adapter.fetch(self.source)
        candidates = adapter.extract(self.source, fetched)

        self.assertEqual(fetched.http_status, 200)
        self.assertEqual(len(candidates), 1)
        self.assertTrue(candidates[0].positions_complete)
        self.assertEqual(
            [position.position_key for position in candidates[0].positions],
            ["job-1", "job-2"],
        )
        self.assertEqual(candidates[0].target_audience, "2027届")

    def test_incomplete_page_sequence_is_rejected(self) -> None:
        adapter = IsolatedBrowserJsonSourceAdapter()
        payload = self._payload([self._row("job-1")], total=101)
        with patch.object(adapter, "_collect_payloads", return_value=([payload], 200)):
            with self.assertRaisesMessage(ValueError, "incomplete page sequence"):
                adapter.fetch(self.source)

    def test_exact_duplicates_are_removed_but_conflicts_fail(self) -> None:
        adapter = IsolatedBrowserJsonSourceAdapter()
        row = self._row("job-1")
        payload = self._payload([row, copy.deepcopy(row)])
        with patch.object(adapter, "_collect_payloads", return_value=([payload], 200)):
            fetched = adapter.fetch(self.source)
        body = json.loads(fetched.body)
        self.assertEqual(len(body["data"]["jobList"]), 1)
        self.assertEqual(body["_radar"]["duplicate_rows_removed"], 1)

        conflicting_payload = self._payload(
            [row, self._row("job-1", "冲突岗位标题")]
        )
        with patch.object(
            adapter,
            "_collect_payloads",
            return_value=([conflicting_payload], 200),
        ):
            with self.assertRaisesMessage(ValueError, "conflicting rows"):
                adapter.fetch(self.source)
