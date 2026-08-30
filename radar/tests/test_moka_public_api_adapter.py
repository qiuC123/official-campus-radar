import copy
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from radar.collectors.base import EXPLICIT_MISSING
from radar.collectors.moka_api import MokaPublicApiAdapter
from radar.collectors.registry import AdapterRegistry


MOKA_CONFIG = {
    "org_id": "dji",
    "site_id": 143359,
    "mode": "campus",
    "page_size": 2,
    "max_pages": 3,
    "request_delay_seconds": 0.25,
    "batch": {
        "identity_key": "dji-campus-2027",
        "title": "大疆创新 2027 校园招聘",
        "official_page_url": (
            "https://apply.careers.dji.com/"
            "campus-recruitment/dji/143359?locale=zh-CN#/jobs"
        ),
        "recruitment_type": "campus_recruitment",
        "target_audience": "2027届",
        "published_on": "",
        "deadline": "",
    },
}


def make_source(config: dict | None = None):
    return SimpleNamespace(
        adapter_name="moka_public_api",
        parser_config=copy.deepcopy(config or MOKA_CONFIG),
        source_url=(
            "https://apply.careers.dji.com/"
            "campus-recruitment/dji/143359?locale=zh-CN#/jobs"
        ),
        official_entrypoint_url="https://careers.dji.com/zh-CN/campus/hot-jobs",
        organization=SimpleNamespace(official_domain="dji.com"),
    )


def response(payload: dict) -> Mock:
    result = Mock()
    result.status_code = 200
    result.json.return_value = payload
    return result


def job(job_id: str, *, status: str = "open", city: str = "深圳市") -> dict:
    return {
        "id": job_id,
        "title": f"岗位 {job_id}",
        "status": status,
        "description": "<p>工作职责</p><p>完成产品研发。</p>",
        "updatedAt": "2026-08-10T07:08:08Z",
        "locations": [
            {
                "province": "广东",
                "city": city,
                "area": None,
                "country": "中国",
                "address": f" {city}",
            }
        ],
    }


class MokaPublicApiConfigurationTests(SimpleTestCase):
    def test_registry_constructs_adapter(self) -> None:
        self.assertIsInstance(
            AdapterRegistry.get(make_source()),
            MokaPublicApiAdapter,
        )

    def test_verified_dji_style_configuration_is_accepted(self) -> None:
        self.assertIsNone(MokaPublicApiAdapter.validate_source_config(make_source()))

    def test_rejects_non_campus_or_malformed_tenant_configuration(self) -> None:
        cases = [
            ("mode", "social", "mode"),
            ("org_id", "../dji", "org_id"),
            ("site_id", 0, "site_id"),
            ("page_size", 0, "page_size"),
            ("max_pages", 101, "max_pages"),
        ]
        for key, value, message in cases:
            with self.subTest(key=key, value=value):
                config = copy.deepcopy(MOKA_CONFIG)
                config[key] = value
                with self.assertRaisesRegex(ValueError, message):
                    MokaPublicApiAdapter.validate_source_config(make_source(config))

    def test_requires_an_official_entrypoint_and_matching_batch_page(self) -> None:
        source = make_source()
        source.official_entrypoint_url = "https://untrusted.example/campus"
        with self.assertRaisesRegex(ValueError, "official entrypoint"):
            MokaPublicApiAdapter.validate_source_config(source)

        config = copy.deepcopy(MOKA_CONFIG)
        config["batch"]["official_page_url"] = "https://untrusted.example/jobs"
        with self.assertRaisesRegex(ValueError, "official_page_url"):
            MokaPublicApiAdapter.validate_source_config(make_source(config))


class MokaPublicApiFetchAndExtractionTests(SimpleTestCase):
    @patch("radar.collectors.json_api.time.sleep")
    @patch("radar.collectors.json_api.requests.Session")
    def test_fetch_uses_offset_pagination_and_collects_the_complete_list(
        self, session_type: Mock, sleep: Mock
    ) -> None:
        session = session_type.return_value
        session.request.side_effect = [
            response({"total": 3, "jobs": [job("a"), job("b")]}),
            response({"total": 3, "jobs": [job("c")]}),
        ]

        page = MokaPublicApiAdapter().fetch(make_source())
        document = json.loads(page.body)

        self.assertEqual([row["id"] for row in document["jobs"]], ["a", "b", "c"])
        self.assertTrue(document["_radar"]["positions_complete"])
        self.assertEqual(session.request.call_count, 2)
        self.assertFalse(session.trust_env)
        self.assertEqual(session.cookies.clear.call_count, 2)
        first, second = session.request.call_args_list
        self.assertEqual(first.args[0], "GET")
        self.assertEqual(
            first.args[1],
            "https://api.mokahr.com/api-platform/v1/jobs/dji",
        )
        self.assertEqual(
            first.kwargs["params"],
            {"mode": "campus", "siteId": 143359, "offset": 0, "limit": 2},
        )
        self.assertEqual(second.kwargs["params"]["offset"], 2)
        self.assertFalse(first.kwargs["allow_redirects"])
        self.assertNotIn("Cookie", first.kwargs["headers"])
        sleep.assert_called_once_with(0.25)

    @patch("radar.collectors.json_api.requests.Session")
    def test_extract_normalizes_locations_html_timestamp_and_unknown_dates(
        self, session_type: Mock
    ) -> None:
        session_type.return_value.request.return_value = response(
            {"total": 2, "jobs": [job("open"), job("closed", status="closed")]}
        )
        adapter = MokaPublicApiAdapter()

        candidate = adapter.extract(make_source(), adapter.fetch(make_source()))[0]

        self.assertEqual(len(candidate.positions), 1)
        position = candidate.positions[0]
        self.assertEqual(position.position_key, "open")
        self.assertEqual(position.title, "岗位 open")
        self.assertEqual(position.location_text, "广东·深圳市")
        self.assertEqual(position.raw_text, "工作职责\n完成产品研发。")
        self.assertEqual(position.source_updated_on.isoformat(), "2026-08-10")
        self.assertIsNone(position.application_url)
        self.assertIsNone(candidate.published_on)
        self.assertIsNone(candidate.deadline)
        self.assertEqual(
            candidate.field_evidence["deadline"].raw_value,
            EXPLICIT_MISSING,
        )
        self.assertTrue(candidate.positions_complete)

    @patch("radar.collectors.json_api.requests.Session")
    def test_batch_partitions_pass_through_moka_normalization(
        self, session_type: Mock
    ) -> None:
        regular = job("regular")
        special = job("special")
        special["attribute_id"] = 132985
        session_type.return_value.request.return_value = response(
            {"total": 2, "jobs": [regular, special]}
        )
        config = copy.deepcopy(MOKA_CONFIG)
        config["batch_partitions"] = [
            {
                "batch": {
                    **copy.deepcopy(MOKA_CONFIG["batch"]),
                    "identity_key": "dji-campus-2027-regular",
                    "title": "大疆 2027 拓疆者计划",
                    "official_page_url": (
                        "https://apply.careers.dji.com/"
                        "campus-recruitment/dji/143359?locale=zh-CN&plan=regular"
                    ),
                },
                "row_filters": [
                    {"path": "attribute_id", "not_equals_any": [132985]}
                ],
            },
            {
                "batch": {
                    **copy.deepcopy(MOKA_CONFIG["batch"]),
                    "identity_key": "dji-campus-2027-digital",
                    "title": "大疆数字管理构建者计划",
                    "official_page_url": (
                        "https://apply.careers.dji.com/"
                        "campus-recruitment/dji/143359?locale=zh-CN&plan=digital"
                    ),
                },
                "row_filters": [
                    {"path": "attribute_id", "equals_any": [132985]}
                ],
            },
        ]
        source = make_source(config)
        adapter = MokaPublicApiAdapter()

        candidates = adapter.extract(source, adapter.fetch(source))

        self.assertEqual(
            [[position.position_key for position in candidate.positions]
             for candidate in candidates],
            [["regular"], ["special"]],
        )
