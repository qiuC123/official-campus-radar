import copy
import importlib
from types import SimpleNamespace

from django.test import SimpleTestCase


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

