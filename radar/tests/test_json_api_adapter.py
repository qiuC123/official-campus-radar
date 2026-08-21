import copy
import importlib
import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from radar.collectors.json_api import JsonApiSourceAdapter


BASE_CONFIG = {
    "endpoint": "https://careers.example.test/api/jobs",
    "method": "GET",
    "params": {"language": "zh-cn"},
    "pagination": {
        "mode": "page_index",
        "page_param": "pageIndex",
        "size_param": "pageSize",
        "page_size": 2,
        "start_page": 1,
        "max_pages": 3,
    },
    "list_path": "Data.Posts",
    "total_path": "Data.Count",
    "notice": {
        "identity_key": "example-campus-2027",
        "title": "Example 2027 校园招聘",
        "official_notice_url": "https://careers.example.test/campus",
        "recruitment_type": "campus_recruitment",
        "target_audience": "2027届",
        "published_on": "2026-08-20",
        "deadline": "2026-12-31",
    },
    "field_map": {
        "position_key": "PostId",
        "title": "RecruitPostName",
        "location": "LocationName",
        "raw_text": "Responsibility",
        "application_url": "PostURL",
        "updated_at": "LastUpdateTime",
        "is_valid": "IsValid",
    },
    "valid_values": {"is_valid": ["True", True]},
    "request_delay_seconds": 0,
}


def merge_config(patch: dict) -> dict:
    config = copy.deepcopy(BASE_CONFIG)
    for key, value in patch.items():
        config[key] = value
    return config


def make_source(config: dict):
    return SimpleNamespace(
        parser_config=config,
        source_url="https://careers.example.test/api/jobs",
        organization=SimpleNamespace(official_domain="careers.example.test"),
    )


def adapter_type():
    try:
        module = importlib.import_module("radar.collectors.json_api")
    except ModuleNotFoundError:
        return None
    return getattr(module, "JsonApiSourceAdapter", None)


class JsonApiConfigurationTests(SimpleTestCase):
    def test_valid_configuration_is_accepted(self) -> None:
        adapter = adapter_type()
        self.assertIsNotNone(adapter, "JsonApiSourceAdapter must exist")
        self.assertIsNone(adapter.validate_source_config(make_source(BASE_CONFIG)))

    def test_invalid_configuration_names_the_broken_contract(self) -> None:
        adapter = adapter_type()
        self.assertIsNotNone(adapter, "JsonApiSourceAdapter must exist")
        cases = [
            ({"endpoint": ""}, "endpoint"),
            ({"endpoint": "http://careers.example.test/api/jobs"}, "HTTPS"),
            ({"endpoint": "https://untrusted.example/api/jobs"}, "official domain"),
            ({"method": "PUT"}, "method"),
            ({"list_path": ""}, "list_path"),
            (
                {
                    "field_map": {
                        **BASE_CONFIG["field_map"],
                        "position_key": "",
                    }
                },
                "position_key",
            ),
            (
                {
                    "field_map": {
                        **BASE_CONFIG["field_map"],
                        "title": "",
                    }
                },
                "title",
            ),
            ({"pagination": {"mode": "page_index"}}, "max_pages"),
            (
                {
                    "pagination": {
                        **BASE_CONFIG["pagination"],
                        "max_pages": 0,
                    }
                },
                "max_pages",
            ),
            (
                {
                    "pagination": {
                        **BASE_CONFIG["pagination"],
                        "max_pages": 101,
                    }
                },
                "max_pages",
            ),
            ({"request_delay_seconds": -1}, "request_delay_seconds"),
        ]
        for patch, message in cases:
            with self.subTest(patch=patch):
                with self.assertRaisesRegex(ValueError, message):
                    adapter.validate_source_config(make_source(merge_config(patch)))

    def test_dates_require_fixed_values_or_field_paths(self) -> None:
        adapter = adapter_type()
        self.assertIsNotNone(adapter, "JsonApiSourceAdapter must exist")
        for name in ("published_on", "deadline"):
            config = copy.deepcopy(BASE_CONFIG)
            config["notice"].pop(name)
            config["field_map"].pop(name, None)
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, name):
                    adapter.validate_source_config(make_source(config))

    def test_fixed_notice_dates_must_be_valid_iso_dates(self) -> None:
        for name in ("published_on", "deadline"):
            config = copy.deepcopy(BASE_CONFIG)
            config["notice"][name] = "not-a-date"
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, name):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )

    def test_official_notice_url_must_be_https_on_source_host(self) -> None:
        for url in (
            "http://careers.example.test/campus",
            "https://jobs.example.test/campus",
        ):
            config = copy.deepcopy(BASE_CONFIG)
            config["notice"]["official_notice_url"] = url
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "official_notice_url"):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )


def json_response(payload: dict, *, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.url = BASE_CONFIG["endpoint"]
    response.headers = {"Content-Type": "application/json"}
    response.json.return_value = payload
    return response


class JsonApiFetchTests(SimpleTestCase):
    def fetch(self, config: dict):
        fetch = getattr(JsonApiSourceAdapter(), "fetch", None)
        self.assertIsNotNone(fetch, "JsonApiSourceAdapter.fetch must exist")
        return fetch(make_source(config))

    @patch("radar.collectors.json_api.time.sleep")
    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_combines_pages_and_stops_at_total(
        self, request: Mock, sleep: Mock
    ) -> None:
        request.side_effect = [
            json_response(
                {
                    "Code": 200,
                    "Data": {
                        "Count": 3,
                        "Posts": [{"PostId": "1"}, {"PostId": "2"}],
                    },
                }
            ),
            json_response(
                {
                    "Code": 200,
                    "Data": {"Count": 3, "Posts": [{"PostId": "3"}]},
                }
            ),
        ]

        page = self.fetch(BASE_CONFIG)

        document = json.loads(page.body)
        self.assertEqual(
            document["Data"]["Posts"],
            [{"PostId": "1"}, {"PostId": "2"}, {"PostId": "3"}],
        )
        self.assertTrue(document["_radar"]["positions_complete"])
        self.assertEqual(page.canonical_url, BASE_CONFIG["endpoint"])
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once_with(0)
        first_call = request.call_args_list[0]
        self.assertEqual(first_call.args[:2], ("GET", BASE_CONFIG["endpoint"]))
        self.assertEqual(first_call.kwargs["params"]["pageIndex"], 1)
        self.assertEqual(first_call.kwargs["params"]["pageSize"], 2)
        self.assertNotIn("json", first_call.kwargs)

    @patch("radar.collectors.json_api.time.sleep")
    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_stops_at_an_empty_page_without_total(
        self, request: Mock, sleep: Mock
    ) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config.pop("total_path")
        request.side_effect = [
            json_response({"Data": {"Posts": [{"PostId": "1"}]}}),
            json_response({"Data": {"Posts": []}}),
        ]

        page = self.fetch(config)

        document = json.loads(page.body)
        self.assertEqual(document["Data"]["Posts"], [{"PostId": "1"}])
        self.assertTrue(document["_radar"]["positions_complete"])
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once_with(0)

    @patch("radar.collectors.json_api.time.sleep")
    @patch("radar.collectors.json_api.requests.Session.request")
    def test_max_pages_marks_a_nonempty_truncated_result_incomplete(
        self, request: Mock, sleep: Mock
    ) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["pagination"]["max_pages"] = 1
        request.return_value = json_response(
            {
                "Data": {
                    "Count": 3,
                    "Posts": [{"PostId": "1"}, {"PostId": "2"}],
                }
            }
        )

        page = self.fetch(config)

        document = json.loads(page.body)
        self.assertFalse(document["_radar"]["positions_complete"])
        self.assertEqual(request.call_count, 1)
        sleep.assert_not_called()

    @patch("radar.collectors.json_api.time.sleep")
    @patch("radar.collectors.json_api.requests.Session.request")
    def test_canonical_hash_is_stable_across_response_key_order(
        self, request: Mock, _sleep: Mock
    ) -> None:
        request.side_effect = [
            json_response(
                {
                    "Code": 200,
                    "Data": {
                        "Count": 1,
                        "Posts": [{"PostId": "1", "Name": "A"}],
                    },
                }
            ),
            json_response(
                {
                    "Data": {
                        "Posts": [{"Name": "A", "PostId": "1"}],
                        "Count": 1,
                    },
                    "Code": 200,
                }
            ),
        ]
        first = self.fetch(BASE_CONFIG)
        second = self.fetch(BASE_CONFIG)

        self.assertEqual(first.body, second.body)
        self.assertEqual(first.content_hash, second.content_hash)

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fixed_notice_change_updates_the_canonical_hash(
        self, request: Mock
    ) -> None:
        payload = {"Data": {"Count": 0, "Posts": []}}
        request.side_effect = [json_response(payload), json_response(payload)]
        changed_config = copy.deepcopy(BASE_CONFIG)
        changed_config["notice"]["title"] = "Updated campus notice"

        first = self.fetch(BASE_CONFIG)
        second = self.fetch(changed_config)

        self.assertNotEqual(first.content_hash, second.content_hash)
        self.assertEqual(
            json.loads(second.body)["_radar"]["notice"]["title"],
            "Updated campus notice",
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_post_places_pagination_in_the_json_body(self, request: Mock) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["method"] = "POST"
        request.return_value = json_response(
            {"Data": {"Count": 0, "Posts": []}}
        )

        self.fetch(config)

        call = request.call_args
        self.assertEqual(call.args[:2], ("POST", BASE_CONFIG["endpoint"]))
        self.assertEqual(call.kwargs["json"]["pageIndex"], 1)
        self.assertEqual(call.kwargs["json"]["pageSize"], 2)
        self.assertNotIn("params", call.kwargs)


class JsonApiExtractionTests(SimpleTestCase):
    def fixture_page(self, config: dict | None = None):
        fixture = json.loads(
            (Path(__file__).parent / "fixtures" / "json_api_page.json").read_text(
                encoding="utf-8"
            )
        )
        effective_config = copy.deepcopy(config or BASE_CONFIG)
        with patch(
            "radar.collectors.json_api.requests.Session.request",
            return_value=json_response(fixture),
        ):
            return JsonApiSourceAdapter().fetch(make_source(effective_config))

    def extract(self, config: dict | None = None):
        adapter = JsonApiSourceAdapter()
        extract = getattr(adapter, "extract", None)
        self.assertIsNotNone(extract, "JsonApiSourceAdapter.extract must exist")
        effective_config = copy.deepcopy(config or BASE_CONFIG)
        return extract(
            make_source(effective_config),
            self.fixture_page(effective_config),
        )

    def test_extract_groups_valid_positions_under_one_notice(self) -> None:
        candidates = self.extract()

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.identity_key, "example-campus-2027")
        self.assertEqual(candidate.title, "Example 2027 校园招聘")
        self.assertEqual(candidate.published_on, date(2026, 8, 20))
        self.assertEqual(candidate.deadline, date(2026, 12, 31))
        self.assertTrue(candidate.positions_complete)
        self.assertEqual(
            [position.position_key for position in candidate.positions],
            ["2034975730101809152", "2034975730101809153"],
        )

    def test_extract_audits_skipped_and_filtered_position_counts(self) -> None:
        candidate = self.extract()[0]

        self.assertIn("rows=4", candidate.evidence_excerpt)
        self.assertIn("retained=2", candidate.evidence_excerpt)
        self.assertIn("skipped_missing_identity=1", candidate.evidence_excerpt)
        self.assertIn("filtered_invalid=1", candidate.evidence_excerpt)

    def test_extract_writes_exact_json_path_evidence(self) -> None:
        candidate = self.extract()[0]
        first = candidate.positions[0]

        self.assertEqual(first.locator, "$.Data.Posts[0]")
        self.assertEqual(
            first.field_evidence["position_title"].locator,
            "$.Data.Posts[0].RecruitPostName",
        )
        self.assertEqual(
            first.field_evidence["location"].raw_value,
            "深圳",
        )
        self.assertEqual(
            first.field_evidence["application_link"].parsed_value,
            "https://careers.example.test/jobs/2034975730101809152",
        )
        self.assertEqual(
            candidate.field_evidence["title"].locator,
            "$._radar.notice.title",
        )
        self.assertEqual(
            candidate.field_evidence["deadline"].parsed_value,
            "2026-12-31",
        )

    def test_published_on_can_come_from_a_mapped_chinese_date(self) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["notice"].pop("published_on")
        config["field_map"]["published_on"] = "LastUpdateTime"

        candidate = self.extract(config)[0]

        self.assertEqual(candidate.published_on, date(2026, 8, 20))
        self.assertEqual(
            candidate.field_evidence["published_on"].locator,
            "$.Data.Posts[0].LastUpdateTime",
        )
        self.assertEqual(
            candidate.field_evidence["published_on"].parsed_value,
            "2026-08-20",
        )

    def test_bad_date_falls_back_to_none_without_aborting_extraction(self) -> None:
        parse_date = getattr(JsonApiSourceAdapter, "_parse_date", None)
        self.assertIsNotNone(parse_date, "JsonApiSourceAdapter._parse_date must exist")

        self.assertIsNone(parse_date("2026/08/20"))
        self.assertIsNone(parse_date("not-a-date"))
