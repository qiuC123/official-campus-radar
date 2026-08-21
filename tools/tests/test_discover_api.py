import importlib
import io
import unittest


CTRIP_PAYLOAD = {
    "retCode": "201",
    "retValue": {
        "total": 2,
        "recruitJobAdList": [
            {
                "jobId": "2034975730101809152",
                "jobTitle": "后端研发工程师",
                "cityName": "上海",
                "publishDate": "2026-08-20",
                "kindName": "校园招聘",
            },
            {
                "jobId": "2034975730101809153",
                "jobTitle": "客户端研发工程师",
                "cityName": "北京",
                "publishDate": "2026-08-21",
                "kindName": "校园招聘",
            },
        ],
    },
}

TENCENT_PAYLOAD = {
    "Code": 200,
    "Data": {
        "Count": 2,
        "Posts": [
            {
                "PostId": "2034975730101809152",
                "RecruitPostName": "后台开发",
                "LocationName": "深圳",
                "LastUpdateTime": "2026年08月20日",
                "RequireWorkYearsName": "不限",
            },
            {
                "PostId": "2034975730101809153",
                "RecruitPostName": "测试开发",
                "LocationName": "上海",
                "LastUpdateTime": "2026年08月21日",
                "RequireWorkYearsName": "不限",
            },
        ],
    },
}


def load_function(name):
    try:
        module = importlib.import_module("tools.discover_api")
    except ModuleNotFoundError as error:
        if error.name not in {"tools", "tools.discover_api"}:
            raise
        return None
    return getattr(module, name, None)


class PureInferenceTests(unittest.TestCase):
    def require_function(self, name):
        function = load_function(name)
        self.assertTrue(callable(function), f"{name} must be implemented")
        return function

    def test_finds_ctrip_job_array_at_expected_path(self):
        find_candidate_arrays = self.require_function("find_candidate_arrays")

        candidates = find_candidate_arrays(CTRIP_PAYLOAD)

        self.assertEqual(
            [candidate.path for candidate in candidates],
            ["retValue.recruitJobAdList"],
        )

    def test_finds_tencent_job_array_at_expected_path(self):
        find_candidate_arrays = self.require_function("find_candidate_arrays")

        candidates = find_candidate_arrays(TENCENT_PAYLOAD)

        self.assertEqual(
            [candidate.path for candidate in candidates],
            ["Data.Posts"],
        )

    def test_rejects_city_dictionary_with_name_but_no_location_or_time_key(self):
        find_candidate_arrays = self.require_function("find_candidate_arrays")
        payload = {"cities": [{"code": "CO0009", "name": "上海"}]}

        self.assertEqual(find_candidate_arrays(payload), [])

    def test_rejects_location_dictionaries_when_one_key_matches_both_signals(self):
        find_candidate_arrays = self.require_function("find_candidate_arrays")
        payloads = (
            {"cities": [{"code": "CO0009", "cityName": "上海"}]},
            {"locations": [{"code": "SZ", "LocationName": "深圳"}]},
        )

        for payload in payloads:
            with self.subTest(payload=payload):
                self.assertEqual(find_candidate_arrays(payload), [])

    def test_finds_total_nearest_each_candidate_array(self):
        infer_total_path = self.require_function("infer_total_path")

        self.assertEqual(
            infer_total_path(CTRIP_PAYLOAD, "retValue.recruitJobAdList"),
            "retValue.total",
        )
        self.assertEqual(
            infer_total_path(TENCENT_PAYLOAD, "Data.Posts"),
            "Data.Count",
        )

    def test_finds_allowed_top_level_business_success_markers(self):
        infer_success = self.require_function("infer_success")

        self.assertEqual(
            infer_success(CTRIP_PAYLOAD),
            {"path": "retCode", "value": "201"},
        )
        self.assertEqual(
            infer_success(TENCENT_PAYLOAD),
            {"path": "Code", "value": 200},
        )

    def test_infers_nested_body_pagination_paths(self):
        infer_pagination_parameters = self.require_function(
            "infer_pagination_parameters"
        )

        parameters = infer_pagination_parameters(
            {"condition": {"kind": ["1"]}, "pager": {"index": "1", "size": "10"}},
            None,
        )

        self.assertEqual(
            parameters,
            {"pager.index": "1", "pager.size": "10"},
        )

    def test_infers_top_level_query_pagination_names(self):
        infer_pagination_parameters = self.require_function(
            "infer_pagination_parameters"
        )

        parameters = infer_pagination_parameters(
            None,
            "https://careers.tencent.com/tencentcareer/api/post/Query"
            "?timestamp=0&pageIndex=1&pageSize=10&language=zh-cn&area=cn&attrId=",
        )

        self.assertEqual(parameters, {"pageIndex": "1", "pageSize": "10"})

    def test_infers_ctrip_field_map_and_unique_long_numeric_identity(self):
        infer_field_map = self.require_function("infer_field_map")
        rows = CTRIP_PAYLOAD["retValue"]["recruitJobAdList"]

        field_map = infer_field_map(rows)

        self.assertEqual(field_map["title"], "jobTitle")
        self.assertEqual(field_map["location"], "cityName")
        self.assertEqual(field_map["updated_at"], "publishDate")
        self.assertEqual(field_map["position_key"], "jobId")

    def test_replay_header_ladder_has_five_bounded_compliance_levels(self):
        build_replay_header_profiles = self.require_function(
            "build_replay_header_profiles"
        )
        captured = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "CapturedBrowser/1.0",
            "Cookie": "session=browser-cookie",
            "X-Signature": "generated-signature",
            "X-Trace-Id": "trace-id",
            "Referer": "https://careers.example/",
        }

        profiles = build_replay_header_profiles(captured)

        self.assertEqual(
            [profile.name for profile in profiles],
            [
                "完整头 + Cookie（基线）",
                "去掉疑似签名头",
                "去掉 Cookie",
                "同时去掉两者",
                "最简合规头",
            ],
        )
        self.assertLessEqual(len(profiles), 6)
        self.assertIn("cookie", profiles[1].headers)
        self.assertNotIn("x-signature", profiles[1].headers)
        self.assertNotIn("x-trace-id", profiles[1].headers)
        self.assertNotIn("cookie", profiles[2].headers)
        self.assertIn("x-signature", profiles[2].headers)
        self.assertNotIn("cookie", profiles[3].headers)
        self.assertNotIn("x-signature", profiles[3].headers)
        self.assertEqual(
            set(profiles[4].headers),
            {"accept", "content-type", "user-agent"},
        )
        self.assertEqual(
            profiles[4].headers["user-agent"],
            "OfficialCampusRadar/0.1 (local low-frequency collector)",
        )

    def test_sample_fields_keep_recruitment_discriminator_values(self):
        select_sample_fields = self.require_function("select_sample_fields")
        ctrip_row = {
            **CTRIP_PAYLOAD["retValue"]["recruitJobAdList"][0],
            "description": "long full job description",
        }
        tencent_row = TENCENT_PAYLOAD["Data"]["Posts"][0]

        ctrip_sample = select_sample_fields(
            ctrip_row,
            {
                "position_key": "jobId",
                "title": "jobTitle",
                "location": "cityName",
                "updated_at": "publishDate",
                "raw_text": "description",
            },
        )
        tencent_sample = select_sample_fields(
            tencent_row,
            {"position_key": "PostId", "title": "RecruitPostName"},
        )

        self.assertEqual(ctrip_sample["kindName"], "校园招聘")
        self.assertNotIn("description", ctrip_sample)
        self.assertEqual(tencent_sample["RequireWorkYearsName"], "不限")


class PureConfigurationAndReportingTests(unittest.TestCase):
    def require_function(self, name):
        function = load_function(name)
        self.assertTrue(callable(function), f"{name} must be implemented")
        return function

    def test_builds_ctrip_adapter_shaped_config_with_nested_pagination(self):
        build_config_draft = self.require_function("build_config_draft")
        request_body = {
            "condition": {
                "kind": ["1"],
                "category": 2,
                "city": [],
                "keyword": "",
            },
            "pager": {"index": "1", "size": "10"},
            "head": {"language": "zh_CN", "version": "1"},
        }

        draft = build_config_draft(
            "https://careers.ctrip.com/api/hrrecruit/getJobAd",
            "POST",
            request_body,
            CTRIP_PAYLOAD,
            "retValue.recruitJobAdList",
        )

        self.assertEqual(
            draft["endpoint"],
            "https://careers.ctrip.com/api/hrrecruit/getJobAd",
        )
        self.assertEqual(draft["method"], "POST")
        self.assertEqual(draft["params"], request_body)
        self.assertEqual(
            draft["pagination"],
            {
                "mode": "page_index",
                "page_param": "pager.index",
                "size_param": "pager.size",
                "page_size": 10,
                "start_page": 1,
                "max_pages": 10,
            },
        )
        self.assertEqual(draft["list_path"], "retValue.recruitJobAdList")
        self.assertEqual(draft["total_path"], "retValue.total")
        self.assertEqual(draft["success"], {"path": "retCode", "value": "201"})
        self.assertEqual(draft["field_map"]["title"], "jobTitle")

    def test_builds_tencent_adapter_shaped_config_from_query(self):
        build_config_draft = self.require_function("build_config_draft")
        request_url = (
            "https://careers.tencent.com/tencentcareer/api/post/Query"
            "?timestamp=0&pageIndex=1&pageSize=10&language=zh-cn&area=cn&attrId="
        )

        draft = build_config_draft(
            request_url,
            "GET",
            None,
            TENCENT_PAYLOAD,
            "Data.Posts",
        )

        self.assertEqual(
            draft["endpoint"],
            "https://careers.tencent.com/tencentcareer/api/post/Query",
        )
        self.assertEqual(draft["params"]["attrId"], "")
        self.assertEqual(draft["pagination"]["page_param"], "pageIndex")
        self.assertEqual(draft["pagination"]["size_param"], "pageSize")
        self.assertEqual(draft["list_path"], "Data.Posts")
        self.assertEqual(draft["total_path"], "Data.Count")
        self.assertEqual(draft["success"], {"path": "Code", "value": 200})

    def test_detects_suspicious_query_and_nested_body_keys(self):
        find_suspicious_request_inputs = self.require_function(
            "find_suspicious_request_inputs"
        )
        request_url = (
            "https://careers.example/api/jobs?pageIndex=1&token=query-secret"
        )
        request_body = {
            "condition": {"kind": ["1"], "nonce": "nested-secret"},
            "head": {"w-signature": "body-signature", "language": "zh_CN"},
        }

        paths = find_suspicious_request_inputs(request_url, request_body)

        self.assertEqual(
            paths,
            [
                "query.token",
                "body.condition.nonce",
                "body.head.w-signature",
            ],
        )

    def test_config_redacts_suspicious_query_and_nested_body_values(self):
        build_config_draft = self.require_function("build_config_draft")
        query_secret = "query-secret-value"
        body_secret = "nested-body-secret"
        get_draft = build_config_draft(
            "https://careers.tencent.com/tencentcareer/api/post/Query"
            f"?pageIndex=1&pageSize=10&token={query_secret}&language=zh-cn",
            "GET",
            None,
            TENCENT_PAYLOAD,
            "Data.Posts",
        )
        post_draft = build_config_draft(
            "https://careers.ctrip.com/api/hrrecruit/getJobAd",
            "POST",
            {
                "condition": {"kind": ["1"], "nonce": body_secret},
                "pager": {"index": "1", "size": "10"},
            },
            CTRIP_PAYLOAD,
            "retValue.recruitJobAdList",
        )

        serialized = str(get_draft) + str(post_draft)

        self.assertNotIn(query_secret, serialized)
        self.assertNotIn(body_secret, serialized)
        self.assertEqual(get_draft["params"]["token"], "[REDACTED]")
        self.assertEqual(
            post_draft["params"]["condition"]["nonce"],
            "[REDACTED]",
        )

    def test_endpoint_identity_deduplicates_pages_but_keeps_methods_distinct(self):
        endpoint_identity = self.require_function("endpoint_identity")
        page_one = "https://careers.example/api/jobs?pageIndex=1&pageSize=10"
        page_two = "https://careers.example/api/jobs?pageIndex=2&pageSize=10"

        self.assertEqual(
            endpoint_identity("GET", page_one),
            endpoint_identity("get", page_two),
        )
        self.assertNotEqual(
            endpoint_identity("GET", page_one),
            endpoint_identity("POST", page_one),
        )

    def test_detects_http_captcha_login_and_empty_page_blocks_honestly(self):
        detect_page_block = self.require_function("detect_page_block")

        self.assertIn(
            "HTTP 403",
            detect_page_block(403, "https://careers.example/jobs", "Forbidden", 0),
        )
        self.assertIn(
            "验证码",
            detect_page_block(
                200,
                "https://careers.example/jobs",
                "请完成人机验证码后继续",
                0,
            ),
        )
        self.assertIn(
            "登录",
            detect_page_block(
                200,
                "https://careers.example/login",
                "账号 密码 登录",
                0,
            ),
        )
        self.assertIn(
            "无可见内容",
            detect_page_block(200, "https://careers.example/jobs", "  ", 0),
        )
        self.assertIsNone(
            detect_page_block(200, "https://careers.example/jobs", "  ", 2)
        )

    def test_rejects_clicks_that_can_submit_forms(self):
        click_safety_reason = self.require_function("click_safety_reason")

        self.assertIn(
            "提交",
            click_safety_reason(
                {"tag_name": "button", "type": "submit", "inside_form": True}
            ),
        )
        self.assertIn(
            "表单",
            click_safety_reason(
                {"tag_name": "button", "type": "button", "inside_form": True}
            ),
        )
        self.assertIn(
            "新页面",
            click_safety_reason(
                {
                    "tag_name": "a",
                    "type": "",
                    "inside_form": False,
                    "target": "_blank",
                }
            ),
        )
        self.assertIn(
            "新页面",
            click_safety_reason(
                {
                    "tag_name": "a",
                    "type": "",
                    "inside_form": False,
                    "target": "recruitment-results",
                }
            ),
        )

    def test_browser_guards_are_installed_before_page_creation_and_block_effects(self):
        create_guarded_page = self.require_function("create_guarded_page")
        guard_violation_reason = self.require_function("guard_violation_reason")

        class FakePopup:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        class FakePage:
            def __init__(self, events):
                self.events = events
                self.handlers = {}

            def on(self, event, callback):
                self.events.append(f"page.on:{event}")
                self.handlers[event] = callback

        class FakeContext:
            def __init__(self):
                self.events = []
                self.handlers = {}
                self.binding = None
                self.init_script = ""
                self.page = FakePage(self.events)

            def expose_binding(self, name, callback):
                self.events.append(f"expose_binding:{name}")
                self.binding = callback

            def add_init_script(self, *, script):
                self.events.append("add_init_script")
                self.init_script = script

            def new_page(self):
                self.events.append("new_page")
                return self.page

            def on(self, event, callback):
                self.events.append(f"context.on:{event}")
                self.handlers[event] = callback

        context = FakeContext()
        violations = []

        page = create_guarded_page(context, violations)

        self.assertIs(page, context.page)
        self.assertEqual(
            context.events,
            [
                "expose_binding:__officialCampusRadarViolation",
                "add_init_script",
                "new_page",
                "context.on:page",
                "page.on:popup",
            ],
        )
        self.assertIn("HTMLFormElement.prototype.submit", context.init_script)
        self.assertIn("requestSubmit", context.init_script)
        self.assertIn("window.open", context.init_script)
        self.assertIn("base[target]", context.init_script)

        context.binding(None, "form.requestSubmit")
        popup = FakePopup()
        context.handlers["page"](popup)
        second_popup = FakePopup()
        page.handlers["popup"](second_popup)

        self.assertTrue(popup.closed)
        self.assertTrue(second_popup.closed)
        reason = guard_violation_reason(violations)
        self.assertIn("form.requestSubmit", reason)
        self.assertIn("new page", reason)

    def test_classifies_only_minimal_header_success_as_connectable(self):
        classify_replay_results = self.require_function("classify_replay_results")
        connectable = [
            {"name": "完整头 + Cookie（基线）", "equivalent": True},
            {"name": "去掉疑似签名头", "equivalent": True},
            {"name": "去掉 Cookie", "equivalent": True},
            {"name": "同时去掉两者", "equivalent": True},
            {"name": "最简合规头", "equivalent": True},
        ]
        signature_required = [
            {"name": "完整头 + Cookie（基线）", "equivalent": True},
            {"name": "去掉疑似签名头", "equivalent": False},
            {"name": "去掉 Cookie", "equivalent": True},
            {"name": "同时去掉两者", "equivalent": False},
            {"name": "最简合规头", "equivalent": False},
        ]

        self.assertEqual(classify_replay_results(connectable)["status"], "可接入")
        self.assertEqual(
            classify_replay_results(signature_required)["status"],
            "不可接入",
        )
        self.assertIn(
            "签名",
            classify_replay_results(signature_required)["reason"],
        )

    def test_parses_targets_document_without_network_or_browser(self):
        parse_targets_document = self.require_function("parse_targets_document")
        targets = parse_targets_document(
            {
                "targets": [
                    "https://careers.example/a",
                    {
                        "url": "https://careers.example/b",
                        "wait": 12,
                        "scroll": True,
                        "click": ".next",
                    },
                ]
            },
            default_wait=8,
            default_scroll=False,
            default_click=None,
        )

        self.assertEqual(targets[0].url, "https://careers.example/a")
        self.assertEqual(targets[0].wait_seconds, 8)
        self.assertEqual(targets[1].wait_seconds, 12)
        self.assertTrue(targets[1].scroll)
        self.assertEqual(targets[1].click_selector, ".next")
        with self.assertRaisesRegex(ValueError, "finite"):
            parse_targets_document(
                [{"url": "https://careers.example/c", "wait": float("nan")}],
                default_wait=8,
                default_scroll=False,
                default_click=None,
            )

    def test_cli_requires_exactly_one_url_source(self):
        build_parser = self.require_function("build_parser")
        parser = build_parser()

        single = parser.parse_args(["--url", "https://careers.example/jobs"])

        self.assertEqual(single.url, "https://careers.example/jobs")
        self.assertEqual(single.wait, 8)
        with self.assertRaises(SystemExit):
            parser.parse_args([])
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "--url",
                    "https://careers.example/jobs",
                    "--targets",
                    "tools/targets.json",
                ]
            )
        with self.assertRaises(SystemExit):
            parser.parse_args(
                ["--url", "https://careers.example/jobs", "--wait", "nan"]
            )

    def test_markdown_report_preserves_facts_without_claiming_integration(self):
        render_markdown_report = self.require_function("render_markdown_report")
        target_results = [
            {
                "entry_url": "https://careers.ctrip.com/",
                "final_url": "https://careers.ctrip.com/#/campus",
                "page_status": 200,
                "block_reason": None,
                "error": None,
                "candidates": [
                    {
                        "method": "POST",
                        "request_url": "https://careers.ctrip.com/api/hrrecruit/getJobAd",
                        "response_status": 200,
                        "content_type": "application/json",
                        "list_path": "retValue.recruitJobAdList",
                        "total_path": "retValue.total",
                        "confidence": 20,
                        "header_names": ["content-type", "cookie", "x-signature"],
                        "replays": [
                            {
                                "name": "最简合规头",
                                "http_status": 200,
                                "equivalent": True,
                                "note": "候选列表路径仍存在且非空",
                            }
                        ],
                        "verdict": {
                            "status": "可接入",
                            "reason": "最简合规头返回等效非空列表",
                        },
                        "config": {
                            "endpoint": "https://careers.ctrip.com/api/hrrecruit/getJobAd",
                            "method": "POST",
                            "list_path": "retValue.recruitJobAdList",
                        },
                        "samples": [
                            {"jobTitle": "后端研发工程师", "kindName": "校园招聘"}
                        ],
                    }
                ],
            }
        ]

        report = render_markdown_report(
            target_results,
            generated_at="2026-08-21T10:00:00+08:00",
        )

        self.assertIn("https://careers.ctrip.com/", report)
        self.assertIn("retValue.recruitJobAdList", report)
        self.assertIn('"kindName": "校园招聘"', report)
        self.assertIn("最简合规头", report)
        self.assertNotIn("接入成功", report)


    def test_markdown_report_renders_capture_omissions_with_redacted_urls(self):
        render_markdown_report = self.require_function("render_markdown_report")
        secret = "never-render-this-token"
        target_results = [
            {
                "entry_url": "https://careers.example/jobs",
                "final_url": "https://careers.example/jobs",
                "page_status": 200,
                "block_reason": None,
                "error": None,
                "exchanges": [
                    {
                        "method": "GET",
                        "request_url": (
                            "https://careers.example/api/jobs"
                            f"?token={secret}&page=1"
                        ),
                        "response_status": 200,
                        "capture_note": "response body exceeded capture limit",
                    },
                    {
                        "method": "POST",
                        "request_url": "https://careers.example/api/search",
                        "response_status": 200,
                        "capture_note": "response JSON was malformed",
                    },
                    {
                        "method": "GET",
                        "request_url": "https://careers.example/api/blocked",
                        "response_status": 403,
                        "capture_note": "response body was unreadable",
                    },
                ],
                "candidates": [],
            }
        ]

        report = render_markdown_report(
            target_results,
            generated_at="2026-08-21T10:00:00+08:00",
        )

        self.assertIn("### Capture notes", report)
        self.assertIn("response body exceeded capture limit", report)
        self.assertIn("response JSON was malformed", report)
        self.assertIn("response body was unreadable", report)
        self.assertIn("%5BREDACTED%5D", report)
        self.assertNotIn(secret, report)


class OfflineBoundaryTests(unittest.TestCase):
    def require_function(self, name):
        function = load_function(name)
        self.assertTrue(callable(function), f"{name} must be implemented")
        return function

    def test_capture_analysis_deduplicates_paginated_endpoint_responses(self):
        analyze_captured_target = self.require_function("analyze_captured_target")
        capture = {
            "entry_url": "https://careers.tencent.com/search.html",
            "final_url": "https://careers.tencent.com/search.html",
            "page_status": 200,
            "block_reason": None,
            "error": None,
            "exchanges": [
                {
                    "request_url": (
                        "https://careers.tencent.com/tencentcareer/api/post/Query"
                        "?pageIndex=1&pageSize=10"
                    ),
                    "method": "GET",
                    "request_headers": {"Accept": "application/json"},
                    "request_body": None,
                    "request_json": None,
                    "response_status": 200,
                    "content_type": "application/json",
                    "response_json": TENCENT_PAYLOAD,
                },
                {
                    "request_url": (
                        "https://careers.tencent.com/tencentcareer/api/post/Query"
                        "?pageIndex=2&pageSize=10"
                    ),
                    "method": "GET",
                    "request_headers": {"Accept": "application/json"},
                    "request_body": None,
                    "request_json": None,
                    "response_status": 200,
                    "content_type": "application/json",
                    "response_json": TENCENT_PAYLOAD,
                },
            ],
        }

        candidates = analyze_captured_target(capture)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["list_path"], "Data.Posts")
        self.assertEqual(
            candidates[0]["config"]["endpoint"],
            "https://careers.tencent.com/tencentcareer/api/post/Query",
        )

    def test_capture_analysis_preserves_material_filter_variants(self):
        analyze_captured_target = self.require_function("analyze_captured_target")
        endpoint = "https://careers.tencent.com/tencentcareer/api/post/Query"
        capture = {
            "exchanges": [
                {
                    "request_url": f"{endpoint}?pageIndex=1&pageSize=10&attrId=",
                    "method": "GET",
                    "request_headers": {"Accept": "application/json"},
                    "request_body": None,
                    "request_json": None,
                    "response_status": 200,
                    "content_type": "application/json",
                    "response_json": TENCENT_PAYLOAD,
                },
                {
                    "request_url": (
                        f"{endpoint}?pageIndex=1&pageSize=10&attrId=campus"
                    ),
                    "method": "GET",
                    "request_headers": {"Accept": "application/json"},
                    "request_body": None,
                    "request_json": None,
                    "response_status": 200,
                    "content_type": "application/json",
                    "response_json": TENCENT_PAYLOAD,
                },
            ]
        }

        candidates = analyze_captured_target(capture)

        self.assertEqual(len(candidates), 2)
        self.assertEqual(
            {candidate["config"]["params"]["attrId"] for candidate in candidates},
            {"", "campus"},
        )

    def test_endpoint_budget_replays_only_campus_preferred_material_variant(self):
        run_target_sequence = self.require_function("run_target_sequence")
        TargetSpec = load_function("TargetSpec")
        self.assertIsNotNone(TargetSpec)
        endpoint = "https://careers.tencent.com/tencentcareer/api/post/Query"

        def exchange(query):
            return {
                "request_url": f"{endpoint}?{query}",
                "method": "GET",
                "request_headers": {"Accept": "application/json"},
                "request_body": None,
                "request_json": None,
                "response_status": 200,
                "content_type": "application/json",
                "response_json": TENCENT_PAYLOAD,
            }

        capture = {
            "entry_url": "https://careers.tencent.com/search.html",
            "final_url": "https://careers.tencent.com/search.html",
            "page_status": 200,
            "block_reason": None,
            "error": None,
            "exchanges": [
                exchange("pageIndex=1&pageSize=10&attrId="),
                exchange("pageIndex=2&pageSize=10&attrId="),
                exchange("pageIndex=1&pageSize=10&attrId=campus"),
            ],
        }
        replayed_filters = []

        def replay_candidate(candidate):
            replayed_filters.append(candidate["config"]["params"]["attrId"])
            return [
                {"name": "完整头 + Cookie（基线）", "equivalent": True},
                {"name": "去掉疑似签名头", "equivalent": True},
                {"name": "去掉 Cookie", "equivalent": True},
                {"name": "同时去掉两者", "equivalent": True},
                {"name": "最简合规头", "equivalent": True},
            ]

        results = run_target_sequence(
            [TargetSpec("https://careers.tencent.com/search.html")],
            capture_func=lambda target: capture,
            replay_func=replay_candidate,
            sleep_fn=lambda seconds: None,
        )

        candidates = results[0]["candidates"]
        self.assertEqual(len(candidates), 2)
        self.assertEqual(replayed_filters, ["campus"])
        self.assertLessEqual(
            sum(len(candidate["replays"]) for candidate in candidates),
            6,
        )
        self.assertEqual(
            {candidate["verdict"]["status"] for candidate in candidates},
            {"可接入", "未重放"},
        )
        self.assertTrue(
            all(candidate["endpoint_replay_budget_limit"] == 6 for candidate in candidates)
        )
        self.assertTrue(
            all(candidate["endpoint_replay_budget_used"] == 5 for candidate in candidates)
        )
        render_markdown_report = self.require_function("render_markdown_report")
        report = render_markdown_report(
            results,
            generated_at="2026-08-21T10:00:00+08:00",
        )
        self.assertIn('"attrId": ""', report)
        self.assertIn('"attrId": "campus"', report)
        self.assertIn("5 / 6", report)

    def test_replay_ladder_uses_exactly_five_sequential_requests(self):
        execute_replay_ladder = self.require_function("execute_replay_ladder")
        calls = []
        sleeps = []

        def requester(**kwargs):
            calls.append(kwargs)
            return {
                "http_status": 200,
                "payload": TENCENT_PAYLOAD,
                "note": "HTTP 200 JSON",
            }

        candidate = {
            "method": "GET",
            "request_url": (
                "https://careers.tencent.com/tencentcareer/api/post/Query"
                "?pageIndex=1&pageSize=10"
            ),
            "request_headers": {
                "Accept": "application/json",
                "Cookie": "browser=cookie",
                "X-Signature": "generated",
            },
            "request_body": None,
            "request_json": None,
            "list_path": "Data.Posts",
        }

        replays = execute_replay_ladder(
            candidate,
            requester=requester,
            sleep_fn=sleeps.append,
        )

        self.assertEqual(len(calls), 5)
        self.assertEqual(len(replays), 5)
        self.assertEqual(sleeps, [1.0, 1.0, 1.0, 1.0])
        self.assertTrue(all(replay["equivalent"] for replay in replays))
        self.assertEqual(
            calls[-1]["headers"]["user-agent"],
            "OfficialCampusRadar/0.1 (local low-frequency collector)",
        )

    def test_suspicious_request_variant_is_redacted_and_never_replayed(self):
        analyze_captured_target = self.require_function("analyze_captured_target")
        execute_replay_ladder = self.require_function("execute_replay_ladder")
        render_markdown_report = self.require_function("render_markdown_report")
        run_target_sequence = self.require_function("run_target_sequence")
        TargetSpec = load_function("TargetSpec")
        self.assertIsNotNone(TargetSpec)
        secret = "frontend-generated-secret"
        request_url = (
            "https://careers.tencent.com/tencentcareer/api/post/Query"
            f"?pageIndex=1&pageSize=10&attrId=campus&traceId={secret}"
        )
        capture = {
            "entry_url": "https://careers.tencent.com/search.html",
            "final_url": "https://careers.tencent.com/search.html",
            "page_status": 200,
            "block_reason": None,
            "error": None,
            "exchanges": [
                {
                    "request_url": request_url,
                    "method": "GET",
                    "request_headers": {"Accept": "application/json"},
                    "request_body": None,
                    "request_json": None,
                    "response_status": 200,
                    "content_type": "application/json",
                    "response_json": TENCENT_PAYLOAD,
                }
            ],
        }
        analyzed = analyze_captured_target(capture)
        direct_calls = []

        def direct_requester(**kwargs):
            direct_calls.append(kwargs)
            return {
                "http_status": 200,
                "payload": TENCENT_PAYLOAD,
                "note": "HTTP 200 JSON",
            }

        direct_replays = execute_replay_ladder(
            analyzed[0],
            requester=direct_requester,
            sleep_fn=lambda seconds: None,
        )
        replayed = []

        def replay_candidate(candidate):
            replayed.append(candidate)
            return []

        results = run_target_sequence(
            [TargetSpec("https://careers.tencent.com/search.html")],
            capture_func=lambda target: capture,
            replay_func=replay_candidate,
            sleep_fn=lambda seconds: None,
        )
        candidate = results[0]["candidates"][0]
        report = render_markdown_report(
            results,
            generated_at="2026-08-21T10:00:00+08:00",
        )

        self.assertEqual(direct_replays, [])
        self.assertEqual(direct_calls, [])
        self.assertEqual(replayed, [])
        self.assertEqual(candidate["verdict"]["status"], "不可接入")
        self.assertIn("签名", candidate["verdict"]["reason"])
        self.assertEqual(candidate["endpoint_replay_budget_used"], 0)
        self.assertNotIn(secret, candidate["request_url"])
        self.assertNotIn(secret, str(candidate["config"]))
        self.assertNotIn(secret, report)
        self.assertIn("[REDACTED]", report)

    def test_target_sequence_is_serial_and_delays_at_least_three_seconds(self):
        run_target_sequence = self.require_function("run_target_sequence")
        TargetSpec = load_function("TargetSpec")
        self.assertIsNotNone(TargetSpec)
        events = []
        sleeps = []
        targets = [
            TargetSpec("https://careers.example/one"),
            TargetSpec("https://careers.example/two"),
        ]

        def capture_target(target):
            events.append(f"capture:{target.url}")
            return {
                "entry_url": target.url,
                "final_url": target.url,
                "page_status": 200,
                "block_reason": None,
                "error": None,
                "exchanges": [],
            }

        def replay_candidate(candidate):
            events.append("replay")
            return []

        results = run_target_sequence(
            targets,
            capture_func=capture_target,
            replay_func=replay_candidate,
            sleep_fn=sleeps.append,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(
            events,
            [
                "capture:https://careers.example/one",
                "capture:https://careers.example/two",
            ],
        )
        self.assertEqual(sleeps, [3.0])

    def test_main_can_run_end_to_end_with_offline_boundaries(self):
        main = self.require_function("main")
        stdout = io.StringIO()
        stderr = io.StringIO()

        def capture_target(target):
            return {
                "entry_url": target.url,
                "final_url": target.url,
                "page_status": 200,
                "block_reason": None,
                "error": None,
                "exchanges": [
                    {
                        "request_url": (
                            "https://careers.tencent.com/tencentcareer/api/post/Query"
                            "?pageIndex=1&pageSize=10"
                        ),
                        "method": "GET",
                        "request_headers": {"Accept": "application/json"},
                        "request_body": None,
                        "request_json": None,
                        "response_status": 200,
                        "content_type": "application/json",
                        "response_json": TENCENT_PAYLOAD,
                    }
                ],
            }

        def requester(**kwargs):
            return {
                "http_status": 200,
                "payload": TENCENT_PAYLOAD,
                "note": "HTTP 200 JSON",
            }

        exit_code = main(
            ["--url", "https://careers.tencent.com/search.html", "--wait", "0"],
            capture_func=capture_target,
            requester=requester,
            sleep_fn=lambda seconds: None,
            now_fn=lambda: "2026-08-21T10:00:00+08:00",
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Data.Posts", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
