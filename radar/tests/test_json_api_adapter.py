import copy
import importlib
import json
import warnings
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from bs4 import MarkupResemblesLocatorWarning
from django.test import SimpleTestCase, TestCase

from radar.collectors.json_api import JsonApiSourceAdapter
from radar.collectors.registry import AdapterRegistry
from radar.models import (
    Evidence,
    OfficialSource,
    Organization,
    RecruitmentBatch,
    SourceVersion,
)
from radar.services.admission import transition_source
from radar.services.publication import publish_candidates


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
    "batch": {
        "identity_key": "example-campus-2027",
        "title": "Example 2027 校园招聘",
        "official_page_url": "https://careers.example.test/campus",
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
    "request_delay_seconds": 0.25,
}

CTRIP_CONFIG = {
    "endpoint": "https://careers.ctrip.com/api/hrrecruit/getJobAd",
    "method": "POST",
    "body": {
        "condition": {
            "kind": ["1"],
            "category": 2,
            "city": [],
            "keyword": "",
            "fromId": [],
            "country": [],
            "bucode": [],
            "jobFamilyCode": [],
            "jobFamilyGroupCode": [],
        },
        "head": {"language": "zh_CN", "version": "1"},
    },
    "pagination": {
        "mode": "page_index",
        "page_param": "pager.index",
        "size_param": "pager.size",
        "page_size": 100,
        "start_page": 1,
        "max_pages": 20,
    },
    "list_path": "retValue.recruitJobAdList",
    "total_path": "retValue.total",
    "success": {"path": "retCode", "expect": "201"},
    "html_fields": ["raw_text"],
    "batch": {
        "identity_key": "ctrip-campus-2027",
        "title": "携程 2027 校园招聘",
        "official_page_url": "https://careers.ctrip.com/",
        "recruitment_type": "campus_recruitment",
        "target_audience": "2027届",
        "published_on": "2026-08-20",
        "deadline": "2027-08-31",
    },
    "field_map": {
        "position_key": "jobId",
        "title": "jobTitle",
        "location": "cityName",
        "raw_text": "requirements",
        "updated_at": "publishDate",
        "category": "jobFamilyGroupName",
        "recruit_kind": "kindName",
    },
    "valid_values": {
        "recruit_kind": ["应届校招生", "Fresh Graduates"]
    },
    "request_delay_seconds": 0.25,
}


def merge_config(patch: dict) -> dict:
    config = copy.deepcopy(BASE_CONFIG)
    for key, value in patch.items():
        config[key] = value
    return config


def make_source(
    config: dict,
    *,
    source_url: str = "https://careers.example.test/api/jobs",
    official_domain: str = "careers.example.test",
):
    return SimpleNamespace(
        adapter_name="json_api",
        parser_config=config,
        source_url=source_url,
        organization=SimpleNamespace(official_domain=official_domain),
    )


def load_json_fixture(name: str) -> dict:
    return json.loads(
        (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")
    )


def adapter_type():
    try:
        module = importlib.import_module("radar.collectors.json_api")
    except ModuleNotFoundError:
        return None
    return getattr(module, "JsonApiSourceAdapter", None)


class JsonApiConfigurationTests(SimpleTestCase):
    def test_registry_constructs_the_json_api_adapter(self) -> None:
        self.assertIsInstance(
            AdapterRegistry.get(make_source(BASE_CONFIG)),
            JsonApiSourceAdapter,
        )

    def test_registry_still_rejects_an_unknown_adapter(self) -> None:
        source = make_source(BASE_CONFIG)
        source.adapter_name = "unknown"
        with self.assertRaisesRegex(ValueError, "unregistered adapter"):
            AdapterRegistry.get(source)

    def test_valid_configuration_is_accepted(self) -> None:
        adapter = adapter_type()
        self.assertIsNotNone(adapter, "JsonApiSourceAdapter must exist")
        self.assertIsNone(adapter.validate_source_config(make_source(BASE_CONFIG)))

    def test_public_json_content_type_header_is_allowed(self) -> None:
        config = merge_config(
            {"headers": {"Content-Type": "application/json;charset=UTF-8"}}
        )

        self.assertIsNone(
            JsonApiSourceAdapter.validate_source_config(make_source(config))
        )

    def test_credential_header_is_still_rejected(self) -> None:
        config = merge_config({"headers": {"Cookie": "session=secret"}})

        with self.assertRaisesRegex(ValueError, "not allowed"):
            JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_endpoint_rejects_userinfo(self) -> None:
        endpoints = [
            "https://user@careers.example.test/api/jobs",
            "https://:pass@careers.example.test/api/jobs",
            "https://@careers.example.test/api/jobs",
            "https://:@careers.example.test/api/jobs",
        ]
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                config = merge_config({"endpoint": endpoint})
                with self.assertRaisesRegex(ValueError, "userinfo"):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )

    def test_success_config_must_be_an_object(self) -> None:
        config = merge_config({"success": "Code == 200"})

        with self.assertRaisesRegex(ValueError, "success"):
            JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_success_config_requires_a_nonempty_path(self) -> None:
        config = merge_config(
            {"success": {"path": "  ", "expect": 200}}
        )

        with self.assertRaisesRegex(ValueError, "success.path"):
            JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_success_config_requires_an_explicit_expect(self) -> None:
        config = merge_config({"success": {"path": "Code"}})

        with self.assertRaisesRegex(ValueError, "success.expect"):
            JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_body_config_must_be_an_object(self) -> None:
        config = merge_config({"method": "POST", "body": []})

        with self.assertRaisesRegex(ValueError, "body"):
            JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_body_encoding_must_match_http_method(self) -> None:
        cases = [
            ("GET", "form"),
            ("GET", "json"),
            ("POST", "query"),
            ("POST", "xml"),
        ]
        for method, body_encoding in cases:
            config = copy.deepcopy(BASE_CONFIG)
            config.update({"method": method, "body_encoding": body_encoding})
            with self.subTest(method=method, body_encoding=body_encoding):
                with self.assertRaisesRegex(ValueError, "body_encoding"):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )

    def test_form_body_rejects_nested_values_and_pagination_paths(self) -> None:
        nested_value = copy.deepcopy(BASE_CONFIG)
        nested_value.update(
            {
                "method": "POST",
                "body_encoding": "form",
                "body": {"filter": {"recruitType": 1}},
            }
        )
        with self.assertRaisesRegex(ValueError, "scalar"):
            JsonApiSourceAdapter.validate_source_config(make_source(nested_value))

        nested_path = copy.deepcopy(BASE_CONFIG)
        nested_path.update(
            {
                "method": "POST",
                "body_encoding": "form",
                "body": {"recruitType": 1},
            }
        )
        nested_path["pagination"].update(
            {"page_param": "pager.index", "size_param": "pager.size"}
        )
        with self.assertRaisesRegex(ValueError, "top-level"):
            JsonApiSourceAdapter.validate_source_config(make_source(nested_path))

    def test_total_kind_requires_supported_value_and_total_path(self) -> None:
        invalid = copy.deepcopy(BASE_CONFIG)
        invalid["pagination"]["total_kind"] = "records"
        with self.assertRaisesRegex(ValueError, "total_kind"):
            JsonApiSourceAdapter.validate_source_config(make_source(invalid))

        missing_path = copy.deepcopy(BASE_CONFIG)
        missing_path.pop("total_path")
        missing_path["pagination"]["total_kind"] = "pages"
        with self.assertRaisesRegex(ValueError, "total_path"):
            JsonApiSourceAdapter.validate_source_config(make_source(missing_path))

    def test_html_fields_config_must_be_a_list(self) -> None:
        config = merge_config({"html_fields": "raw_text"})

        with self.assertRaisesRegex(ValueError, "html_fields"):
            JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_html_fields_roles_must_be_unique_nonempty_and_supported(
        self,
    ) -> None:
        cases = [
            ["title", "title"],
            ["  "],
            ["deadline"],
        ]
        for html_fields in cases:
            with self.subTest(html_fields=html_fields):
                config = merge_config({"html_fields": html_fields})
                with self.assertRaisesRegex(ValueError, "html_fields"):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )

    def test_html_fields_roles_require_mapped_field_paths(self) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["html_fields"] = ["location"]
        config["field_map"]["location"] = "  "

        with self.assertRaisesRegex(ValueError, "field_map.location"):
            JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_pagination_paths_reject_empty_segments(self) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["pagination"]["page_param"] = "pager..index"

        with self.assertRaisesRegex(ValueError, "pagination.page_param"):
            JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_pagination_paths_reject_selected_template_collisions(self) -> None:
        cases = []

        get_config = copy.deepcopy(BASE_CONFIG)
        get_config["params"] = {"pager": 1}
        get_config["pagination"]["page_param"] = "pager.index"
        cases.append(("get_params", get_config))

        post_body_config = copy.deepcopy(BASE_CONFIG)
        post_body_config["method"] = "POST"
        post_body_config["body"] = {"pager": "fixed"}
        post_body_config["pagination"]["page_param"] = "pager.index"
        cases.append(("post_body", post_body_config))

        post_legacy_config = copy.deepcopy(BASE_CONFIG)
        post_legacy_config["method"] = "POST"
        post_legacy_config["params"] = {"pager": []}
        post_legacy_config["pagination"]["page_param"] = "pager.index"
        cases.append(("post_legacy_params", post_legacy_config))

        for name, config in cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    ValueError, "pagination.page_param"
                ):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )

    def test_pagination_paths_reject_equal_or_prefix_overlap(self) -> None:
        cases = [
            ("pageIndex", "pageIndex"),
            ("pager", "pager.size"),
            ("pager.index", "pager"),
        ]
        for page_param, size_param in cases:
            with self.subTest(
                page_param=page_param,
                size_param=size_param,
            ):
                config = copy.deepcopy(BASE_CONFIG)
                config["pagination"].update(
                    {
                        "page_param": page_param,
                        "size_param": size_param,
                    }
                )
                with self.assertRaisesRegex(ValueError, "pagination.*overlap"):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )

    def test_sibling_pagination_paths_are_accepted(self) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["pagination"].update(
            {
                "page_param": "pager.index",
                "size_param": "pager.size",
            }
        )

        self.assertIsNone(
            JsonApiSourceAdapter.validate_source_config(make_source(config))
        )

    def test_request_delay_must_be_positive(self) -> None:
        config = merge_config({"request_delay_seconds": 0})

        with self.assertRaisesRegex(ValueError, "request_delay_seconds"):
            JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_request_delay_must_be_finite(self) -> None:
        non_finite_delays = [
            float("nan"),
            float("inf"),
            float("-inf"),
        ]
        for delay in non_finite_delays:
            with self.subTest(delay=delay):
                config = merge_config({"request_delay_seconds": delay})
                with self.assertRaisesRegex(
                    ValueError, "request_delay_seconds"
                ):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )

    def test_invalid_configuration_names_the_broken_contract(self) -> None:
        adapter = adapter_type()
        self.assertIsNotNone(adapter, "JsonApiSourceAdapter must exist")
        cases = [
            ({"endpoint": ""}, "endpoint"),
            ({"endpoint": "http://careers.example.test/api/jobs"}, "HTTPS"),
            ({"endpoint": "https://untrusted.example/api/jobs"}, "official domain"),
            ({"method": "PUT"}, "method"),
            ({"list_path": ""}, "list_path"),
            ({"list_path": "_radar.positions"}, "reserved"),
            ({"params": []}, "params"),
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
            (
                {
                    "pagination": {
                        **BASE_CONFIG["pagination"],
                        "start_page": -1,
                    }
                },
                "start_page",
            ),
            (
                {
                    "pagination": {
                        **BASE_CONFIG["pagination"],
                        "page_param": "",
                    }
                },
                "page_param",
            ),
            (
                {
                    "pagination": {
                        **BASE_CONFIG["pagination"],
                        "size_param": "",
                    }
                },
                "size_param",
            ),
            ({"valid_values": []}, "valid_values"),
            ({"valid_values": {"unknown": [True]}}, "valid_values.unknown"),
            ({"valid_values": {"is_valid": "True"}}, "valid_values.is_valid"),
            ({"valid_values": {"is_valid": []}}, "valid_values.is_valid"),
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
            config["batch"].pop(name)
            config["field_map"].pop(name, None)
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, name):
                    adapter.validate_source_config(make_source(config))

    def test_fixed_notice_dates_must_be_valid_iso_dates(self) -> None:
        for name in ("published_on", "deadline"):
            config = copy.deepcopy(BASE_CONFIG)
            config["batch"][name] = "not-a-date"
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, name):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )

    def test_official_page_url_must_be_https_on_source_host(self) -> None:
        for url in (
            "http://careers.example.test/campus",
            "https://jobs.example.test/campus",
        ):
            config = copy.deepcopy(BASE_CONFIG)
            config["batch"]["official_page_url"] = url
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "official_page_url"):
                    JsonApiSourceAdapter.validate_source_config(
                        make_source(config)
                    )

    def test_batch_partitions_require_unique_complete_trusted_metadata(self) -> None:
        partition = {
            "batch": {
                **copy.deepcopy(BASE_CONFIG["batch"]),
                "identity_key": "example-plan-a",
                "title": "Example A 计划",
                "official_page_url": "https://careers.example.test/campus?plan=a",
            },
            "row_filters": [{"path": "Plan", "equals_any": ["a"]}],
        }
        valid = copy.deepcopy(BASE_CONFIG)
        valid["batch_partitions"] = [partition]
        self.assertIsNone(
            JsonApiSourceAdapter.validate_source_config(make_source(valid))
        )

        cases = []
        duplicate = copy.deepcopy(valid)
        duplicate["batch_partitions"].append(copy.deepcopy(partition))
        cases.append((duplicate, "identities"))
        untrusted = copy.deepcopy(valid)
        untrusted["batch_partitions"][0]["batch"]["official_page_url"] = (
            "https://jobs.example.test/campus"
        )
        cases.append((untrusted, "official_page_url"))
        missing_date_provenance = copy.deepcopy(valid)
        missing_date_provenance["batch_partitions"][0]["batch"].pop("deadline")
        missing_date_provenance["field_map"].pop("deadline", None)
        cases.append((missing_date_provenance, "deadline"))
        bad_filter = copy.deepcopy(valid)
        bad_filter["batch_partitions"][0]["row_filters"][0]["contains_any"] = ["a"]
        cases.append((bad_filter, "exactly one"))
        for config, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    JsonApiSourceAdapter.validate_source_config(make_source(config))

    def test_partition_coverage_requires_unfiltered_disjoint_equality_partitions(self) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["params"]["Project"] = []
        config["partition_coverage"] = {
            "request_path": "Project",
            "row_path": "Plan",
        }
        config["batch_partitions"] = [
            {
                "batch": {
                    **copy.deepcopy(BASE_CONFIG["batch"]),
                    "identity_key": "plan-a",
                },
                "row_filters": [{"path": "Plan", "equals_any": ["a"]}],
            },
            {
                "batch": {
                    **copy.deepcopy(BASE_CONFIG["batch"]),
                    "identity_key": "plan-b",
                },
                "row_filters": [{"path": "Plan", "equals_any": ["b"]}],
            },
        ]
        self.assertIsNone(
            JsonApiSourceAdapter.validate_source_config(make_source(config))
        )

        filtered = copy.deepcopy(config)
        filtered["params"]["Project"] = ["a"]
        with self.assertRaisesRegex(ValueError, "explicit empty list"):
            JsonApiSourceAdapter.validate_source_config(make_source(filtered))

        overlapping = copy.deepcopy(config)
        overlapping["batch_partitions"][1]["row_filters"][0]["equals_any"] = [
            "a"
        ]
        with self.assertRaisesRegex(ValueError, "disjoint"):
            JsonApiSourceAdapter.validate_source_config(make_source(overlapping))

        catch_all = copy.deepcopy(config)
        catch_all["batch_partitions"][1]["row_filters"] = [
            {"path": "Plan", "not_equals_any": ["a"]}
        ]
        with self.assertRaisesRegex(ValueError, "one equals_any filter"):
            JsonApiSourceAdapter.validate_source_config(make_source(catch_all))


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

    @patch("radar.collectors.json_api.requests.Session")
    def test_fetch_ignores_environment_proxy_and_auth_configuration(
        self, session_type: Mock
    ) -> None:
        session = session_type.return_value
        session.request.return_value = json_response(
            {"Data": {"Count": 0, "Posts": []}}
        )

        self.fetch(BASE_CONFIG)

        self.assertIs(session.trust_env, False)

    @patch("radar.collectors.json_api.requests.Session")
    def test_fetch_clears_session_cookies_before_each_page(
        self, session_type: Mock
    ) -> None:
        session = session_type.return_value
        session.request.side_effect = [
            json_response(
                {"Data": {"Count": 2, "Posts": [{"PostId": "1"}]}}
            ),
            json_response(
                {"Data": {"Count": 2, "Posts": [{"PostId": "2"}]}}
            ),
        ]

        self.fetch(BASE_CONFIG)

        self.assertEqual(session.request.call_count, 2)
        self.assertEqual(session.cookies.clear.call_count, 2)
        for call in session.request.call_args_list:
            self.assertNotIn("Cookie", call.kwargs["headers"])

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_does_not_follow_redirects(self, request: Mock) -> None:
        response = json_response(
            {"Data": {"Count": 0, "Posts": []}},
            status_code=302,
        )
        response.headers["Location"] = "https://untrusted.example/api/jobs"
        request.return_value = response

        with self.assertRaisesRegex(requests.HTTPError, "HTTP 302"):
            self.fetch(BASE_CONFIG)

        self.assertFalse(request.call_args.kwargs["allow_redirects"])

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_rejects_an_upstream_reserved_metadata_key(
        self, request: Mock
    ) -> None:
        request.return_value = json_response(
            {
                "_radar": {"upstream": True},
                "Data": {"Count": 0, "Posts": []},
            }
        )

        with self.assertRaisesRegex(ValueError, "reserved"):
            self.fetch(BASE_CONFIG)

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_rejects_a_configured_business_failure(
        self, request: Mock
    ) -> None:
        config = merge_config(
            {"success": {"path": "Code", "expect": 200}}
        )
        request.return_value = json_response(
            {"Code": "500", "Data": {"Count": 0, "Posts": []}}
        )

        with self.assertRaisesRegex(ValueError, "success"):
            self.fetch(config)

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_compares_business_success_values_as_strings(
        self, request: Mock
    ) -> None:
        config = merge_config(
            {"success": {"path": "Code", "expect": 200}}
        )
        request.return_value = json_response(
            {"Code": "200", "Data": {"Count": 0, "Posts": []}}
        )

        try:
            page = self.fetch(config)
        except ValueError as error:
            self.fail(f"equivalent success values were rejected: {error}")

        self.assertTrue(json.loads(page.body)["_radar"]["positions_complete"])

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_without_success_config_uses_http_status_only(
        self, request: Mock
    ) -> None:
        request.return_value = json_response(
            {"Code": "500", "Data": {"Count": 0, "Posts": []}}
        )

        page = self.fetch(BASE_CONFIG)

        self.assertTrue(json.loads(page.body)["_radar"]["positions_complete"])

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
        sleep.assert_called_once_with(0.25)
        first_call = request.call_args_list[0]
        self.assertEqual(first_call.args[:2], ("GET", BASE_CONFIG["endpoint"]))
        self.assertEqual(first_call.kwargs["params"]["pageIndex"], 1)
        self.assertEqual(first_call.kwargs["params"]["pageSize"], 2)
        self.assertNotIn("json", first_call.kwargs)

    @patch("radar.collectors.json_api.time.sleep")
    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_deduplicates_identical_position_keys(
        self, request: Mock, sleep: Mock
    ) -> None:
        duplicate = {"PostId": "same", "RecruitPostName": "工程师"}
        request.side_effect = [
            json_response(
                {"Data": {"Count": 2, "Posts": [duplicate]}}
            ),
            json_response(
                {"Data": {"Count": 2, "Posts": [copy.deepcopy(duplicate)]}}
            ),
        ]

        document = json.loads(self.fetch(BASE_CONFIG).body)

        self.assertEqual(document["Data"]["Posts"], [duplicate])
        self.assertEqual(document["_radar"]["duplicate_rows_removed"], 1)

    @patch("radar.collectors.json_api.time.sleep")
    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_deduplicates_rows_when_only_page_views_change(
        self, request: Mock, sleep: Mock
    ) -> None:
        first_row = {
            "PostId": "same",
            "RecruitPostName": "工程师",
            "pageViews": 101,
        }
        request.side_effect = [
            json_response(
                {"Data": {"Count": 2, "Posts": [first_row]}}
            ),
            json_response(
                {
                    "Data": {
                        "Count": 2,
                        "Posts": [
                            {
                                "PostId": "same",
                                "RecruitPostName": "工程师",
                                "pageViews": 102,
                            }
                        ],
                    }
                }
            ),
        ]

        document = json.loads(self.fetch(BASE_CONFIG).body)

        self.assertEqual(document["Data"]["Posts"], [first_row])
        self.assertEqual(document["_radar"]["duplicate_rows_removed"], 1)

    @patch("radar.collectors.json_api.time.sleep")
    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_rejects_conflicting_duplicate_position_keys(
        self, request: Mock, sleep: Mock
    ) -> None:
        request.side_effect = [
            json_response(
                {
                    "Data": {
                        "Count": 2,
                        "Posts": [{"PostId": "same", "RecruitPostName": "工程师"}],
                    }
                }
            ),
            json_response(
                {
                    "Data": {
                        "Count": 2,
                        "Posts": [{"PostId": "same", "RecruitPostName": "产品经理"}],
                    }
                }
            ),
        ]

        with self.assertRaisesRegex(ValueError, "conflicting rows"):
            self.fetch(BASE_CONFIG)

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_rejects_non_integer_totals(self, request: Mock) -> None:
        invalid_totals = [True, False, 1.0, 1.5, "01", "+1", "1.0", " 1 "]
        for raw_total in invalid_totals:
            with self.subTest(raw_total=raw_total):
                request.return_value = json_response(
                    {
                        "Data": {
                            "Count": raw_total,
                            "Posts": [{"PostId": "1"}],
                        }
                    }
                )
                with self.assertRaisesRegex(ValueError, "total_path"):
                    self.fetch(BASE_CONFIG)

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_fetch_accepts_a_canonical_integer_string_total(
        self, request: Mock
    ) -> None:
        request.return_value = json_response(
            {"Data": {"Count": "1", "Posts": [{"PostId": "1"}]}}
        )

        page = self.fetch(BASE_CONFIG)

        self.assertTrue(json.loads(page.body)["_radar"]["positions_complete"])

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
        sleep.assert_called_once_with(0.25)

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
        changed_config["batch"]["title"] = "Updated campus batch"

        first = self.fetch(BASE_CONFIG)
        second = self.fetch(changed_config)

        self.assertNotEqual(first.content_hash, second.content_hash)
        self.assertEqual(
            json.loads(second.body)["_radar"]["batch"]["title"],
            "Updated campus batch",
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
        self.assertEqual(call.kwargs["json"].get("language"), "zh-cn")
        self.assertEqual(call.kwargs["json"]["pageIndex"], 1)
        self.assertEqual(call.kwargs["json"]["pageSize"], 2)
        self.assertNotIn("params", call.kwargs)

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_post_form_places_flat_pagination_in_form_data(
        self, request: Mock
    ) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config.update(
            {
                "method": "POST",
                "body_encoding": "form",
                "body": {
                    "recruitType": "1",
                    "coordinateLat": "",
                    "coordinateLng": "",
                },
            }
        )
        config["pagination"].update(
            {"page_param": "currentPage", "size_param": "pageSize"}
        )
        request.return_value = json_response(
            {"Data": {"Count": 0, "Posts": []}}
        )

        self.fetch(config)

        call = request.call_args
        self.assertEqual(call.args[:2], ("POST", BASE_CONFIG["endpoint"]))
        self.assertEqual(
            call.kwargs["data"],
            {
                "recruitType": "1",
                "coordinateLat": "",
                "coordinateLng": "",
                "currentPage": 1,
                "pageSize": 2,
            },
        )
        self.assertNotIn("json", call.kwargs)
        self.assertNotIn("params", call.kwargs)

    @patch("radar.collectors.json_api.time.sleep")
    @patch("radar.collectors.json_api.requests.Session.request")
    def test_total_pages_fetches_every_reported_page(
        self, request: Mock, sleep: Mock
    ) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["pagination"]["total_kind"] = "pages"
        request.side_effect = [
            json_response(
                {
                    "Data": {
                        "Count": 2,
                        "Posts": [{"PostId": str(index)} for index in range(1, 11)],
                    }
                }
            ),
            json_response(
                {
                    "Data": {
                        "Count": 2,
                        "Posts": [{"PostId": str(index)} for index in range(11, 16)],
                    }
                }
            ),
        ]

        page = self.fetch(config)

        document = json.loads(page.body)
        self.assertEqual(len(document["Data"]["Posts"]), 15)
        self.assertTrue(document["_radar"]["positions_complete"])
        self.assertEqual(document["_radar"]["pagination_total_kind"], "pages")
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once_with(0.25)

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_total_pages_rejects_zero_with_nonempty_rows(self, request: Mock) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["pagination"]["total_kind"] = "pages"
        request.return_value = json_response(
            {"Data": {"Count": 0, "Posts": [{"PostId": "1"}]}}
        )

        with self.assertRaisesRegex(ValueError, "page count"):
            self.fetch(config)

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_post_merges_pagination_into_the_fixed_body_template(
        self, request: Mock
    ) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["method"] = "POST"
        config["body"] = {
            "condition": {"kind": ["1"], "category": 2},
            "head": {"language": "zh_CN", "version": "1"},
        }
        request.return_value = json_response(
            {"Data": {"Count": 0, "Posts": []}}
        )

        self.fetch(config)

        self.assertEqual(
            request.call_args.kwargs["json"],
            {
                "condition": {"kind": ["1"], "category": 2},
                "head": {"language": "zh_CN", "version": "1"},
                "pageIndex": 1,
                "pageSize": 2,
            },
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_post_writes_pagination_at_nested_body_paths(
        self, request: Mock
    ) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["method"] = "POST"
        config["body"] = {"head": {"language": "zh_CN"}}
        config["pagination"].update(
            {"page_param": "pager.index", "size_param": "pager.size"}
        )
        request.return_value = json_response(
            {"Data": {"Count": 0, "Posts": []}}
        )

        self.fetch(config)

        self.assertEqual(
            request.call_args.kwargs["json"],
            {
                "head": {"language": "zh_CN"},
                "pager": {"index": 1, "size": 2},
            },
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_ctrip_fixture_uses_its_configured_response_and_request_shapes(
        self, request: Mock
    ) -> None:
        request.return_value = json_response(
            load_json_fixture("json_api_ctrip.json")
        )
        source = make_source(
            CTRIP_CONFIG,
            source_url=CTRIP_CONFIG["endpoint"],
            official_domain="careers.ctrip.com",
        )

        page = JsonApiSourceAdapter().fetch(source)

        request_body = request.call_args.kwargs["json"]
        self.assertEqual(
            request.call_args.args[:2],
            ("POST", "https://careers.ctrip.com/api/hrrecruit/getJobAd"),
        )
        self.assertEqual(
            request_body["condition"],
            {
                "kind": ["1"],
                "category": 2,
                "city": [],
                "keyword": "",
                "fromId": [],
                "country": [],
                "bucode": [],
                "jobFamilyCode": [],
                "jobFamilyGroupCode": [],
            },
        )
        self.assertEqual(
            request_body["head"],
            {"language": "zh_CN", "version": "1"},
        )
        self.assertEqual(request_body["pager"], {"index": 1, "size": 100})
        document = json.loads(page.body)
        self.assertEqual(
            document["retValue"]["recruitJobAdList"][0]["jobId"],
            "535f2df5-32a7-4857-9fdf-fad0acef18bb",
        )
        self.assertTrue(document["_radar"]["positions_complete"])
        candidate = JsonApiSourceAdapter().extract(source, page)[0]
        self.assertEqual(candidate.positions[0].source_updated_on, date(2026, 8, 20))
        self.assertEqual(
            candidate.positions[0].field_evidence["source_updated_on"].parsed_value,
            "2026-08-20",
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_ctrip_fixture_rejects_its_configured_business_failure(
        self, request: Mock
    ) -> None:
        payload = load_json_fixture("json_api_ctrip.json")
        payload["retCode"] = "500"
        request.return_value = json_response(payload)
        source = make_source(
            CTRIP_CONFIG,
            source_url=CTRIP_CONFIG["endpoint"],
            official_domain="careers.ctrip.com",
        )

        with self.assertRaisesRegex(ValueError, "success"):
            JsonApiSourceAdapter().fetch(source)


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

    @staticmethod
    def partition_config() -> dict:
        config = copy.deepcopy(BASE_CONFIG)
        config["batch_partitions"] = [
            {
                "batch": {
                    **copy.deepcopy(BASE_CONFIG["batch"]),
                    "identity_key": "example-plan-a",
                    "title": "Example A 计划",
                    "recruitment_type": "special_program",
                },
                "row_filters": [{"path": "Plan", "equals_any": ["a"]}],
            },
            {
                "batch": {
                    **copy.deepcopy(BASE_CONFIG["batch"]),
                    "identity_key": "example-other-plans",
                    "title": "Example 其他计划",
                },
                "row_filters": [{"path": "Plan", "not_equals_any": ["a"]}],
            },
        ]
        return config

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_batch_partitions_are_mutually_exclusive_and_exhaustive(
        self, request: Mock
    ) -> None:
        payload = load_json_fixture("json_api_page.json")
        payload["Data"]["Posts"][0]["Plan"] = "a"
        payload["Data"]["Posts"][1]["Plan"] = "b"
        request.return_value = json_response(payload)
        config = self.partition_config()
        source = make_source(config)
        adapter = JsonApiSourceAdapter()

        candidates = adapter.extract(source, adapter.fetch(source))

        self.assertEqual(
            [candidate.identity_key for candidate in candidates],
            ["example-plan-a", "example-other-plans"],
        )
        self.assertEqual(
            [[position.position_key for position in candidate.positions]
             for candidate in candidates],
            [["2034975730101809152"], ["2034975730101809153"]],
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_batch_partitions_reject_overlap(self, request: Mock) -> None:
        payload = load_json_fixture("json_api_page.json")
        for row in payload["Data"]["Posts"]:
            row["Plan"] = "a"
        request.return_value = json_response(payload)
        config = self.partition_config()
        config["batch_partitions"][1]["row_filters"] = [
            {"path": "Plan", "contains_any": ["a"]}
        ]
        source = make_source(config)
        adapter = JsonApiSourceAdapter()

        with self.assertRaisesRegex(ValueError, "overlap"):
            adapter.extract(source, adapter.fetch(source))

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_batch_partitions_reject_uncovered_rows(self, request: Mock) -> None:
        payload = load_json_fixture("json_api_page.json")
        payload["Data"]["Posts"][0]["Plan"] = "a"
        payload["Data"]["Posts"][1]["Plan"] = "c"
        request.return_value = json_response(payload)
        config = self.partition_config()
        config["batch_partitions"][1]["row_filters"] = [
            {"path": "Plan", "equals_any": ["b"]}
        ]
        source = make_source(config)
        adapter = JsonApiSourceAdapter()

        with self.assertRaisesRegex(ValueError, "cover every retained position"):
            adapter.extract(source, adapter.fetch(source))

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_partition_equality_tolerates_numeric_string_type_drift(
        self, request: Mock
    ) -> None:
        payload = load_json_fixture("json_api_page.json")
        payload["Data"]["Posts"][0]["Plan"] = "1"
        payload["Data"]["Posts"][1]["Plan"] = 2
        request.return_value = json_response(payload)
        config = self.partition_config()
        config["batch_partitions"][0]["row_filters"] = [
            {"path": "Plan", "equals_any": [1]}
        ]
        config["batch_partitions"][1]["row_filters"] = [
            {"path": "Plan", "not_equals_any": ["1"]}
        ]
        source = make_source(config)
        adapter = JsonApiSourceAdapter()

        candidates = adapter.extract(source, adapter.fetch(source))

        self.assertEqual(
            [[position.position_key for position in candidate.positions]
             for candidate in candidates],
            [["2034975730101809152"], ["2034975730101809153"]],
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
            "$._radar.batch.title",
        )
        self.assertEqual(
            candidate.field_evidence["deadline"].parsed_value,
            "2026-12-31",
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_missing_location_is_retained_as_explicitly_unknown(
        self, request: Mock
    ) -> None:
        payload = load_json_fixture("json_api_page.json")
        payload["Data"]["Posts"][0]["LocationName"] = ""
        request.return_value = json_response(payload)
        source = make_source(copy.deepcopy(BASE_CONFIG))
        adapter = JsonApiSourceAdapter()

        position = adapter.extract(source, adapter.fetch(source))[0].positions[0]

        self.assertEqual(position.location_text, "未说明")
        self.assertEqual(
            position.field_evidence["location"].raw_value,
            "[not-provided]",
        )
        self.assertEqual(
            position.field_evidence["location"].parsed_value,
            "未说明",
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_extract_joins_array_locations_without_losing_raw_evidence(
        self, request: Mock
    ) -> None:
        payload = load_json_fixture("json_api_page.json")
        payload["Data"]["Posts"][0]["LocationName"] = [
            "广东省·东莞市",
            "浙江省·杭州市",
        ]
        request.return_value = json_response(payload)
        source = make_source(copy.deepcopy(BASE_CONFIG))
        adapter = JsonApiSourceAdapter()

        position = adapter.extract(source, adapter.fetch(source))[0].positions[0]

        self.assertEqual(position.location_text, "广东省·东莞市、浙江省·杭州市")
        self.assertEqual(
            position.field_evidence["location"].raw_value,
            '["广东省·东莞市","浙江省·杭州市"]',
        )

    def test_published_on_can_come_from_a_mapped_chinese_date(self) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["batch"].pop("published_on")
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

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_html_field_is_readable_while_evidence_keeps_original_html(
        self, request: Mock
    ) -> None:
        request.return_value = json_response(
            load_json_fixture("json_api_ctrip.json")
        )
        source = make_source(
            CTRIP_CONFIG,
            source_url=CTRIP_CONFIG["endpoint"],
            official_domain="careers.ctrip.com",
        )
        adapter = JsonApiSourceAdapter()

        candidate = adapter.extract(source, adapter.fetch(source))[0]
        position = candidate.positions[0]

        self.assertEqual(
            position.raw_text,
            "招聘对象：本、硕、博。\n"
            "毕业时间：2026 年 9 月至 2027 年 8 月期间毕业",
        )
        self.assertEqual(
            position.field_evidence["raw_text"].raw_value,
            "<p>招聘对象：本、硕、博。</p>"
            "<p>毕业时间：2026 年 9 月至 2027 年 8 月期间毕业</p>",
        )
        self.assertEqual(
            position.field_evidence["raw_text"].parsed_value,
            position.raw_text,
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_all_supported_html_fields_expose_clean_evidence_excerpts(
        self, request: Mock
    ) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["html_fields"] = [
            "title",
            "location",
            "raw_text",
            "application_url",
        ]
        payload = load_json_fixture("json_api_page.json")
        first_row = payload["Data"]["Posts"][0]
        first_row["RecruitPostName"] = "<h2>AI 产品经理</h2>"
        first_row["LocationName"] = "<span>深圳</span>"
        first_row["Responsibility"] = (
            "<p>Campus role.</p><p>Build products.</p>"
        )
        first_row["PostURL"] = (
            "<a>https://careers.example.test/jobs/html-role</a>"
        )
        request.return_value = json_response(payload)
        source = make_source(config)
        adapter = JsonApiSourceAdapter()

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            position = adapter.extract(
                source, adapter.fetch(source)
            )[0].positions[0]

        self.assertEqual(position.title, "AI 产品经理")
        self.assertEqual(position.location_text, "深圳")
        self.assertEqual(position.raw_text, "Campus role.\nBuild products.")
        self.assertEqual(
            position.application_url,
            "https://careers.example.test/jobs/html-role",
        )
        expected_evidence = {
            "position_title": (
                "<h2>AI 产品经理</h2>",
                "AI 产品经理",
                "AI 产品经理",
            ),
            "location": ("<span>深圳</span>", "深圳", "深圳"),
            "raw_text": (
                "<p>Campus role.</p><p>Build products.</p>",
                "Campus role.\nBuild products.",
                "Campus role.\nBuild products.",
            ),
            "application_link": (
                "<a>https://careers.example.test/jobs/html-role</a>",
                "https://careers.example.test/jobs/html-role",
                "https://careers.example.test/jobs/html-role",
            ),
        }
        for field_name, expected in expected_evidence.items():
            with self.subTest(field_name=field_name):
                evidence = position.field_evidence[field_name]
                self.assertEqual(
                    (evidence.raw_value, evidence.parsed_value, evidence.excerpt),
                    expected,
                )
        self.assertFalse(
            any(
                isinstance(warning.message, MarkupResemblesLocatorWarning)
                for warning in caught_warnings
            )
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_non_html_application_url_keeps_raw_evidence_excerpt_semantics(
        self, request: Mock
    ) -> None:
        payload = load_json_fixture("json_api_page.json")
        raw_url = (
            "HTTPS://CAREERS.EXAMPLE.TEST/jobs/2034975730101809152#apply"
        )
        payload["Data"]["Posts"][0]["PostURL"] = raw_url
        request.return_value = json_response(payload)
        adapter = JsonApiSourceAdapter()

        position = adapter.extract(
            make_source(BASE_CONFIG), adapter.fetch(make_source(BASE_CONFIG))
        )[0].positions[0]

        evidence = position.field_evidence["application_link"]
        self.assertEqual(evidence.raw_value, raw_url)
        self.assertEqual(
            evidence.parsed_value,
            "https://careers.example.test/jobs/2034975730101809152",
        )
        self.assertIsNone(evidence.excerpt)

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_tencent_fixture_uses_the_same_config_driven_extraction(
        self, request: Mock
    ) -> None:
        config = merge_config(
            {"success": {"path": "Code", "expect": 200}}
        )
        request.side_effect = [
            json_response(load_json_fixture("json_api_tencent.json")),
            json_response({"Code": 200, "Data": {"Count": 2, "Posts": []}}),
        ]
        source = make_source(config)
        adapter = JsonApiSourceAdapter()

        candidate = adapter.extract(source, adapter.fetch(source))[0]

        self.assertEqual(len(candidate.positions), 1)
        self.assertEqual(
            candidate.positions[0].title,
            "腾讯云- MaaS高级产品经理",
        )
        self.assertEqual(
            candidate.positions[0].field_evidence["position_title"].locator,
            "$.Data.Posts[0].RecruitPostName",
        )
        self.assertEqual(candidate.positions[0].source_updated_on, date(2026, 8, 20))

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_ctrip_iso_date_can_feed_a_mapped_notice_date(
        self, request: Mock
    ) -> None:
        config = copy.deepcopy(CTRIP_CONFIG)
        config["batch"].pop("published_on")
        config["field_map"]["published_on"] = "publishDate"
        request.return_value = json_response(
            load_json_fixture("json_api_ctrip.json")
        )
        source = make_source(
            config,
            source_url=config["endpoint"],
            official_domain="careers.ctrip.com",
        )
        adapter = JsonApiSourceAdapter()

        candidate = adapter.extract(source, adapter.fetch(source))[0]

        self.assertEqual(candidate.published_on, date(2026, 8, 20))
        self.assertEqual(
            candidate.field_evidence["published_on"].locator,
            "$.retValue.recruitJobAdList[0].publishDate",
        )

    @patch("radar.collectors.json_api.requests.Session.request")
    def test_ctrip_campus_whitelist_excludes_a_mixed_social_row(
        self, request: Mock
    ) -> None:
        payload = load_json_fixture("json_api_ctrip.json")
        social_row = copy.deepcopy(
            payload["retValue"]["recruitJobAdList"][0]
        )
        social_row["jobId"] = "social-job"
        social_row["jobTitle"] = "社会招聘岗位"
        social_row["kindName"] = ""
        payload["retValue"]["recruitJobAdList"].append(social_row)
        payload["retValue"]["total"] = 2
        request.return_value = json_response(payload)
        source = make_source(
            CTRIP_CONFIG,
            source_url=CTRIP_CONFIG["endpoint"],
            official_domain="careers.ctrip.com",
        )
        adapter = JsonApiSourceAdapter()

        candidate = adapter.extract(source, adapter.fetch(source))[0]

        self.assertEqual(
            [position.position_key for position in candidate.positions],
            ["535f2df5-32a7-4857-9fdf-fad0acef18bb"],
        )
        self.assertIn("filtered_invalid=1", candidate.evidence_excerpt)


class JsonApiPublicationIntegrationTests(TestCase):
    def setUp(self) -> None:
        organization = Organization.objects.create(
            name="Example API Organization",
            company_type="internet",
            industry="technology",
            official_domain="careers.example.test",
        )
        self.source = OfficialSource.objects.create(
            organization=organization,
            source_type=OfficialSource.SourceType.API,
            source_url=BASE_CONFIG["endpoint"],
            admission_evidence="official API reviewed offline",
            adapter_name="json_api",
            parser_config=copy.deepcopy(BASE_CONFIG),
        )
        transition_source(
            self.source,
            to_state=OfficialSource.AdmissionState.VERIFIED,
            actor_label="test-owner",
            reason="official domain verified",
            evidence="offline endpoint review",
        )
        transition_source(
            self.source,
            to_state=OfficialSource.AdmissionState.ENABLED,
            actor_label="test-owner",
            reason="adapter contract verified",
            evidence="offline fixture passed",
        )
        self.source.refresh_from_db()
        self.payload = json.loads(
            (
                Path(__file__).parent / "fixtures" / "json_api_page.json"
            ).read_text(encoding="utf-8")
        )

    def publish_payload(self, payload: dict):
        adapter = JsonApiSourceAdapter()
        with patch(
            "radar.collectors.json_api.requests.Session.request",
            return_value=json_response(payload),
        ):
            page = adapter.fetch(self.source)
        version = SourceVersion.objects.create(
            source=self.source,
            canonical_url=page.canonical_url,
            content_hash=page.content_hash,
        )
        result = publish_candidates(
            self.source,
            adapter.extract(self.source, page),
            version,
        )[0]
        return result, version

    def test_adapter_output_satisfies_existing_formal_evidence_gates(self) -> None:
        result, version = self.publish_payload(self.payload)

        self.assertEqual(result.action, "created")
        version.is_applied = True
        version.save(update_fields=["is_applied"])
        batch = RecruitmentBatch.objects.formal().get(pk=result.batch_id)
        self.assertEqual(batch.source, self.source)
        self.assertEqual(batch.positions.filter(is_current=True).count(), 2)
        position = batch.positions.get(position_key="2034975730101809152")
        self.assertEqual(position.source_updated_on, date(2026, 8, 20))
        self.assertTrue(
            Evidence.objects.filter(
                batch=batch,
                position=position,
                field_name="source_updated_on",
                parsed_value="2026-08-20",
            ).exists()
        )
        self.assertContains(self.client.get("/"), position.title)

    def test_partitioned_projects_can_share_one_real_portal_url(self) -> None:
        config = JsonApiExtractionTests.partition_config()
        self.source.parser_config = config
        self.source.save(update_fields=["parser_config"])
        payload = copy.deepcopy(self.payload)
        payload["Data"]["Posts"][0]["Plan"] = "a"
        payload["Data"]["Posts"][1]["Plan"] = "b"
        adapter = JsonApiSourceAdapter()
        with patch(
            "radar.collectors.json_api.requests.Session.request",
            return_value=json_response(payload),
        ):
            page = adapter.fetch(self.source)
        version = SourceVersion.objects.create(
            source=self.source,
            canonical_url=page.canonical_url,
            content_hash=page.content_hash,
        )

        results = publish_candidates(
            self.source,
            adapter.extract(self.source, page),
            version,
        )

        self.assertEqual([result.action for result in results], ["created", "created"])
        self.assertEqual(
            list(
                RecruitmentBatch.objects.order_by("identity_key").values_list(
                    "identity_key", "official_page_url", "recruitment_type"
                )
            ),
            [
                (
                    "example-other-plans",
                    "https://careers.example.test/campus",
                    "campus_recruitment",
                ),
                (
                    "example-plan-a",
                    "https://careers.example.test/campus",
                    "special_program",
                ),
            ],
        )

    def test_html_raw_text_evidence_is_persisted_with_a_plain_excerpt(
        self,
    ) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["html_fields"] = ["raw_text"]
        self.source.parser_config = config
        self.source.save(update_fields=["parser_config"])
        payload = copy.deepcopy(self.payload)
        original_html = (
            "<p>Campus graduates.</p>"
            "<p>Apply before 2027-08-31.</p>"
        )
        payload["Data"]["Posts"][0]["Responsibility"] = original_html

        result, version = self.publish_payload(payload)

        evidence_rows = list(
            Evidence.objects.filter(
                source_version=version,
                position__position_key="2034975730101809152",
                field_name="raw_text",
            ).values(
                "field_name",
                "raw_value",
                "parsed_value",
                "excerpt",
            )
        )
        self.assertEqual(result.action, "created")
        self.assertEqual(
            evidence_rows,
            [
                {
                    "field_name": "raw_text",
                    "raw_value": original_html,
                    "parsed_value": (
                        "Campus graduates. Apply before 2027-08-31."
                    ),
                    "excerpt": (
                        "Campus graduates.\nApply before 2027-08-31."
                    ),
                }
            ],
        )

    def test_html_title_and_location_evidence_persist_clean_excerpts(
        self,
    ) -> None:
        config = copy.deepcopy(BASE_CONFIG)
        config["html_fields"] = ["title", "location"]
        self.source.parser_config = config
        self.source.save(update_fields=["parser_config"])
        payload = copy.deepcopy(self.payload)
        payload["Data"]["Posts"][0]["RecruitPostName"] = (
            "<strong>Campus Product Manager</strong>"
        )
        payload["Data"]["Posts"][0]["LocationName"] = "<span>深圳</span>"

        result, version = self.publish_payload(payload)

        evidence_rows = list(
            Evidence.objects.filter(
                source_version=version,
                position__position_key="2034975730101809152",
                field_name__in=("position_title", "location"),
            )
            .order_by("field_name")
            .values(
                "field_name",
                "raw_value",
                "parsed_value",
                "excerpt",
            )
        )
        self.assertEqual(result.action, "created")
        self.assertEqual(
            evidence_rows,
            [
                {
                    "field_name": "location",
                    "raw_value": "<span>深圳</span>",
                    "parsed_value": "深圳",
                    "excerpt": "深圳",
                },
                {
                    "field_name": "position_title",
                    "raw_value": "<strong>Campus Product Manager</strong>",
                    "parsed_value": "Campus Product Manager",
                    "excerpt": "Campus Product Manager",
                },
            ],
        )

    def test_existing_gate_rejects_an_untrusted_application_url(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["Data"]["Posts"][0]["PostURL"] = (
            "https://untrusted.example/jobs/1"
        )

        result, _version = self.publish_payload(payload)

        self.assertEqual(result.action, "rejected")
        self.assertIn("untrusted_application_url", result.reasons)
