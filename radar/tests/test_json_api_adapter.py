import copy
import importlib
import json
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
