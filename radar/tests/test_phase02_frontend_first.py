from dataclasses import replace
from datetime import date, datetime, timezone as datetime_timezone
from types import SimpleNamespace

from django.test import Client, TestCase, override_settings

from radar.collectors.base import EXPLICIT_MISSING, PositionCandidate
from radar.models import (
    ApplicationProgress,
    ApprovedApplicationHost,
    OfficialSource,
    Organization,
    RecruitmentBatch,
    RecruitmentPosition,
    SourceVersion,
)
from radar.services.admission import approve_application_host, transition_source
from radar.services.publication import publish_candidates
from radar.services.dashboard_data import (
    _effective_date,
    canonical_audience,
    canonical_recruitment_type,
)
from radar.tests.helpers import (
    complete_candidate,
    create_enabled_source,
    field_evidence,
    publish_formal_notice,
    valid_html_parser_config,
)
from radar.viewmodels import RecruitmentBatchVM


class Phase02FrontendFirstTests(TestCase):
    def setUp(self):
        self.source = create_enabled_source(name="Phase 02 Org", host="phase02.test")
        self.version_number = 0

    def version(self):
        self.version_number += 1
        return SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash=f"{self.version_number:064d}",
            is_applied=True,
        )

    def test_effective_date_uses_shanghai_calendar_day(self):
        position = SimpleNamespace(
            source_updated_on=None,
            content_changed_at=datetime(
                2026, 8, 26, 16, 30, tzinfo=datetime_timezone.utc
            ),
            first_seen_at=None,
        )
        self.assertEqual(_effective_date(position), date(2026, 8, 27))

    def test_effective_date_uses_latest_of_all_three_sources(self):
        position = SimpleNamespace(
            source_updated_on=date(2026, 8, 28),
            content_changed_at=datetime(
                2026, 8, 27, 8, 0, tzinfo=datetime_timezone.utc
            ),
            first_seen_at=datetime(
                2026, 8, 29, 8, 0, tzinfo=datetime_timezone.utc
            ),
        )
        self.assertEqual(_effective_date(position), date(2026, 8, 29))

    def test_batch_location_summary_caps_large_real_location_sets(self):
        positions = tuple(
            SimpleNamespace(locations=(f"地点{index}",))
            for index in range(1, 9)
        )
        batch = RecruitmentBatchVM(
            id=1,
            company="示例公司",
            company_type="民企",
            industry="测试",
            title="示例批次",
            recruitment_type="校园招聘",
            target_audience="2027届",
            deadline=None,
            status="招聘中",
            official_page_url="https://example.test/",
            progress_value="not_applied",
            progress_label="未投递",
            positions=positions,
        )

        self.assertEqual(
            batch.location_summary,
            "地点1、地点2、地点3、地点4、地点5、地点6，另有 2 个地点",
        )

    def test_real_dashboard_uses_chinese_company_type_without_inferred_graduate_year(self):
        self.source.organization.company_type = Organization.CompanyType.PRIVATE
        self.source.organization.save(update_fields=["company_type"])
        candidate = complete_candidate(self.source, identity_key="generic-audience")
        candidate = replace(
            candidate,
            target_audience="应届毕业生",
            field_evidence={
                **candidate.field_evidence,
                "target_audience": field_evidence(
                    "应届毕业生", "#generic-audience .audience"
                ),
            },
        )
        publish_candidates(self.source, [candidate], self.version())

        response = self.client.get("/?audience=届次未说明")

        self.assertContains(response, self.source.organization.name)
        self.assertContains(response, "民企")
        self.assertContains(response, "届次未说明")
        self.assertNotContains(response, ">2027届</span>")
        self.assertNotContains(response, ">private<")

    def test_audience_categories_compact_official_date_ranges_and_internships(self):
        self.assertEqual(
            canonical_audience(
                RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT,
                "2026年9月至2027年8月毕业的在校生",
            ),
            "2027届",
        )
        self.assertEqual(
            canonical_audience(
                RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT,
                "毕业时间为2026年1月至2027年12月",
            ),
            "2026届、2027届",
        )
        self.assertEqual(
            canonical_audience(
                RecruitmentBatch.RecruitmentType.INTERNSHIP,
                "LongCat 实习生招聘对象",
            ),
            "在校生",
        )

    def test_recruitment_type_displays_season_instead_of_generic_campus(self):
        self.assertEqual(
            canonical_recruitment_type(RecruitmentBatch.RecruitmentType.SPECIAL_PROGRAM),
            "待确认",
        )
        self.assertEqual(
            canonical_recruitment_type(RecruitmentBatch.RecruitmentType.AUTUMN),
            "秋招",
        )
        self.assertEqual(
            canonical_recruitment_type(RecruitmentBatch.RecruitmentType.AUTUMN_EARLY),
            "秋招提前批",
        )
        self.assertEqual(
            canonical_recruitment_type(RecruitmentBatch.RecruitmentType.SUMMER),
            "夏招",
        )
        self.assertEqual(
            canonical_recruitment_type(RecruitmentBatch.RecruitmentType.INTERNSHIP),
            "实习",
        )

    def test_province_filter_matches_cities_and_summary_uses_provinces(self):
        candidate = complete_candidate(
            self.source,
            identity_key="province-filter",
            location="深圳市、杭州市",
        )
        publish_candidates(self.source, [candidate], self.version())

        guangdong = self.client.get("/?city=广东")
        zhejiang = self.client.get("/?city=浙江")
        beijing = self.client.get("/?city=北京")

        self.assertContains(guangdong, self.source.organization.name)
        self.assertContains(guangdong, "广东、浙江")
        self.assertContains(zhejiang, self.source.organization.name)
        self.assertNotContains(beijing, self.source.organization.name)

    @override_settings(DEBUG=True)
    def test_preview_is_clearly_mocked_and_does_not_write_business_tables(self):
        response = self.client.get("/preview/phase-02/")
        self.assertContains(response, "模拟数据，不是线上岗位")
        self.assertContains(response, "不会访问企业网站")
        self.assertEqual(RecruitmentBatch.objects.count(), 0)
        self.assertNotContains(response, 'action="/update-now/"')

    @override_settings(DEBUG=True)
    def test_preview_supports_filters_history_and_three_health_states(self):
        self.assertContains(self.client.get("/preview/phase-02/?company=星河"), "星河科技")
        self.assertNotContains(self.client.get("/preview/phase-02/?company=星河"), "云帆智能")
        self.assertContains(self.client.get("/preview/phase-02/?view=history"), "海岳通信")
        self.assertContains(self.client.get("/preview/phase-02/?health=missing"), "模拟：计划更新漏跑")
        self.assertContains(self.client.get("/preview/phase-02/?health=failure"), "模拟：1 个来源失败")
        self.assertContains(self.client.get("/preview/phase-02/?health=normal"), "模拟运行状态")

    def test_two_positions_in_one_batch_share_one_manual_progress(self):
        batch = publish_formal_notice(self.source, identity_key="two-progress")
        RecruitmentPosition.objects.create(
            batch=batch,
            position_key="two",
            title="产品经理",
            location_text="杭州市",
            normalized_locations=["杭州"],
        )
        ApplicationProgress.objects.create(batch=batch, status="interviewed")
        self.assertEqual(batch.application_progress.status, "interviewed")
        self.assertEqual(batch.positions.count(), 2)

    def test_progress_endpoint_returns_json_and_rejects_unknown_status(self):
        batch = publish_formal_notice(self.source, identity_key="json-progress")
        response = self.client.post(
            f"/batches/{batch.pk}/progress/", {"status": "written_test"}
        )
        self.assertEqual(response.json(), {"ok": True, "status": "written_test", "label": "已笔试"})
        self.assertEqual(
            self.client.post(f"/batches/{batch.pk}/progress/", {"status": "invalid"}).status_code,
            400,
        )

    def test_progress_endpoint_enforces_csrf(self):
        batch = publish_formal_notice(self.source, identity_key="csrf-progress")
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(
            client.post(f"/batches/{batch.pk}/progress/", {"status": "applied"}).status_code,
            403,
        )

    def test_identical_daily_verification_does_not_refresh_content_changed_time(self):
        candidate = complete_candidate(self.source, identity_key="stable-time", location="杭州市")
        result = publish_candidates(self.source, [candidate], self.version())[0]
        position = RecruitmentBatch.objects.get(pk=result.batch_id).positions.get()
        original = position.content_changed_at
        publish_candidates(self.source, [candidate], self.version())
        position.refresh_from_db()
        self.assertEqual(position.content_changed_at, original)

    def test_application_link_change_refreshes_content_changed_time_without_progress_loss(self):
        candidate = complete_candidate(self.source, identity_key="link-change")
        result = publish_candidates(self.source, [candidate], self.version())[0]
        position = RecruitmentBatch.objects.get(pk=result.batch_id).positions.get()
        batch = RecruitmentBatch.objects.get(pk=result.batch_id)
        ApplicationProgress.objects.create(batch=batch, status="applied")
        original = position.content_changed_at
        new_url = "https://phase02.test/apply/new"
        changed_position = replace(
            candidate.positions[0],
            application_url=new_url,
            field_evidence={
                **candidate.positions[0].field_evidence,
                "application_link": field_evidence(new_url, "#position-1 a@href"),
            },
        )
        publish_candidates(
            self.source,
            [replace(candidate, positions=(changed_position,))],
            self.version(),
        )
        position.refresh_from_db()
        self.assertGreater(position.content_changed_at, original)
        self.assertEqual(batch.application_progress.status, "applied")

    def test_all_locations_and_location_arrays_are_retained(self):
        candidate = complete_candidate(self.source, identity_key="all-city", location="火星基地")
        second = PositionCandidate(
            title="远程岗位",
            location_text="全国、远程",
            raw_text="地点可协商",
            application_url=None,
            position_key="remote",
            field_evidence={
                "position_title": field_evidence("远程岗位", "#remote .title"),
                "location": field_evidence("全国、远程", "#remote .location"),
            },
        )
        result = publish_candidates(
            self.source, [replace(candidate, positions=candidate.positions + (second,))], self.version()
        )[0]
        locations = list(
            RecruitmentBatch.objects.get(pk=result.batch_id).positions.order_by("pk").values_list("normalized_locations", flat=True)
        )
        self.assertEqual(locations, [["火星基地"], ["全国", "远程"]])
        self.assertContains(self.client.get("/", {"city": ["北京", "上海"]}), "远程岗位")

    def test_missing_application_link_reuses_verified_official_page(self):
        batch = publish_formal_notice(self.source, identity_key="no-link")
        response = self.client.get("/")
        self.assertNotContains(response, "投递待确认")
        self.assertContains(response, f'href="{batch.official_page_url}"', count=2)

    def test_project_specific_application_pages_cover_all_partitioned_companies(self):
        cases = (
            (
                "京东",
                "campus.jd.com",
                "official-project:jd:plan:57",
                "https://campus.jd.com/#/jobs?selProjects=57",
            ),
            (
                "腾讯",
                "join.qq.com",
                "official-project:tencent:project:14",
                "https://join.qq.com/post.html?query=p_14",
            ),
            (
                "美团",
                "zhaopin.meituan.com",
                "official-project:meituan:special:8",
                "https://zhaopin.meituan.com/web/longcat",
            ),
            (
                "大疆创新",
                "apply.careers.dji.com",
                "official-project:dji:digital-management:2027",
                "https://apply.careers.dji.com/campus-recruitment/dji/143359"
                "?locale=zh-CN#/jobs?keyword="
                "%E6%95%B0%E5%AD%97%E7%AE%A1%E7%90%86"
                "&page=1&anchorName=jobsList",
            ),
        )
        expected = {}
        for index, (name, host, identity_key, project_url) in enumerate(cases):
            source = create_enabled_source(name=name, host=host)
            batch = publish_formal_notice(
                source,
                identity_key=identity_key,
                hash_character=str(index + 1),
            )
            expected[batch.pk] = project_url

        response = self.client.get("/")

        for batch_vm in response.context["batches"]:
            if batch_vm.id in expected:
                self.assertEqual(
                    batch_vm.primary_application_url,
                    expected[batch_vm.id],
                )
                escaped_url = expected[batch_vm.id].replace("&", "&amp;")
                self.assertContains(
                    response,
                    f'href="{escaped_url}"',
                    count=1,
                )

    def test_exact_job_pages_cover_all_non_partitioned_formal_companies(self):
        cases = (
            (
                "OPPO",
                "careers.oppo.com",
                "phase-02:p12",
                "https://careers.oppo.com/university/oppo/campus/post"
                "?recruitType=Graduate",
            ),
            (
                "vivo",
                "hr-campus.vivo.com",
                "phase-02:p13",
                "https://hr-campus.vivo.com/jobs?1=%5B%7B%22id%22%3A%222%22%2C"
                "%22label%22%3A%22%E7%A7%8B%E5%AD%A3%E6%A0%A1%E5%9B%AD"
                "%E6%8B%9B%E8%81%98%22%7D%5D",
            ),
            (
                "中国电信集团有限公司",
                "job.chinatelecom.com.cn",
                "phase-02:s03",
                "https://job.chinatelecom.com.cn/wt/TELE/web/index"
                "?brandCode=1#/postinquiry",
            ),
            (
                "中国联合网络通信集团有限公司",
                "zglt.zhaopin.com",
                "phase-02:s04",
                "https://zglt.zhaopin.com/scjobs/index.html",
            ),
            (
                "宁德时代",
                "app.mokahr.com",
                "phase-02:p15",
                "https://app.mokahr.com/campus-recruitment/catlhr/148948#/jobs",
            ),
            (
                "拼多多",
                "careers.pddglobalhr.com",
                "phase-02:p11",
                "https://careers.pddglobalhr.com/campus/grad",
            ),
            (
                "比亚迪",
                "job.byd.com",
                "phase-02:p19",
                "https://job.byd.com/portal/pc/#/school/schoolPositionList",
            ),
            (
                "百度",
                "talent.baidu.com",
                "phase-02:p06",
                "https://talent.baidu.com/jobs/list?recruitType=GRADUATE",
            ),
            (
                "顺丰",
                "campus.sf-express.com",
                "phase-02:p18",
                "https://campus.sf-express.com/#/positionList",
            ),
        )
        expected = {}
        for index, (name, host, identity_key, application_url) in enumerate(cases):
            source = create_enabled_source(name=name, host=host)
            batch = publish_formal_notice(
                source,
                identity_key=identity_key,
                hash_character=f"{index + 1:x}",
            )
            expected[batch.pk] = application_url

        response = self.client.get("/")

        for batch_vm in response.context["batches"]:
            if batch_vm.id in expected:
                self.assertEqual(
                    batch_vm.primary_application_url,
                    expected[batch_vm.id],
                )
                escaped_url = expected[batch_vm.id].replace("&", "&amp;")
                self.assertContains(
                    response,
                    f'href="{escaped_url}"',
                    count=1,
                )

    def test_project_page_precedes_a_single_position_application_link(self):
        source = create_enabled_source(name="腾讯", host="join.qq.com")
        candidate = complete_candidate(
            source,
            identity_key="official-project:tencent:project:9",
            application_url="https://join.qq.com/post_detail.html?postid=1",
        )
        version = SourceVersion.objects.create(
            source=source,
            canonical_url=source.source_url,
            content_hash="9" * 64,
            is_applied=True,
        )
        result = publish_candidates(source, [candidate], version)[0]

        response = self.client.get("/")
        batch_vm = next(
            item for item in response.context["batches"]
            if item.id == result.batch_id
        )

        self.assertEqual(
            batch_vm.primary_application_url,
            "https://join.qq.com/post.html?query=p_9",
        )

    def test_unknown_deadline_is_formal_and_not_counted_as_due_soon(self):
        candidate = complete_candidate(self.source, identity_key="unknown-deadline")
        candidate = replace(candidate, deadline=None, field_evidence={
            **candidate.field_evidence,
            "deadline": field_evidence(EXPLICIT_MISSING, "#batch .deadline [not found]", ""),
        })
        result = publish_candidates(self.source, [candidate], self.version())[0]
        self.assertEqual(result.action, "created")
        response = self.client.get("/")
        self.assertNotContains(response, "投递截止")
        self.assertNotContains(response, 'class="deadline-cell"')
        self.assertEqual(response.context["summary"].deadline_in_7_days, 0)

    def test_tampered_details_fail_closed_and_derived_locations_ignore_cache(self):
        batch = publish_formal_notice(self.source, identity_key="tamper-derived", location="北京市")
        position = batch.positions.get()
        RecruitmentPosition.objects.filter(pk=position.pk).update(
            normalized_locations=["火星"],
            raw_text="篡改详情",
        )
        response = self.client.get("/")
        self.assertNotContains(response, batch.official_page_url)

        RecruitmentPosition.objects.filter(pk=position.pk).update(raw_text="Engineer 北京市")
        response = self.client.get("/")
        self.assertContains(response, "北京")
        self.assertNotContains(response, "火星")

    def test_batch_with_wrong_organization_is_hidden(self):
        batch = publish_formal_notice(self.source, identity_key="wrong-owner")
        other = Organization.objects.create(
            name="错误归属公司", company_type="other", industry="unknown"
        )
        RecruitmentBatch.objects.filter(pk=batch.pk).update(organization=other)
        self.assertNotContains(self.client.get("/"), batch.official_page_url)

    def test_application_link_with_wrong_batch_does_not_reuse_batch_page(self):
        application_url = "https://phase02.test/apply/linked"
        candidate = complete_candidate(
            self.source,
            identity_key="link-owner",
            application_url=application_url,
        )
        result = publish_candidates(self.source, [candidate], self.version())[0]
        batch = RecruitmentBatch.objects.get(pk=result.batch_id)
        other = publish_formal_notice(
            self.source, identity_key="other-link-owner", hash_character="f"
        )
        link = batch.positions.get().application_links.get()
        link.batch = other
        link.save(update_fields=["batch"])
        response = self.client.get("/")
        self.assertContains(response, batch.official_page_url)
        self.assertNotContains(response, application_url)
        self.assertNotContains(response, "投递待确认")

    def test_tampered_external_host_approval_hides_formal_link_and_batch(self):
        organization = Organization.objects.create(
            name="外部投递主体",
            company_type="internet",
            industry="tech",
            official_domain="external-owner.test",
        )
        source = OfficialSource.objects.create(
            organization=organization,
            source_type="website",
            source_url="https://external-owner.test/careers",
            official_entrypoint_url="https://external-owner.test/careers",
            admission_evidence="official page",
            parser_config=valid_html_parser_config(),
        )
        transition_source(
            source,
            to_state="verified",
            actor_label="owner",
            reason="verified",
            evidence="official page reviewed",
        )
        approve_application_host(
            source,
            host="apply.partner.test",
            actor_label="owner",
            evidence="official page links to partner",
        )
        transition_source(
            source,
            to_state="enabled",
            actor_label="owner",
            reason="enabled",
            evidence="offline fixture passed",
        )
        source.refresh_from_db()
        candidate = complete_candidate(
            source,
            identity_key="external-apply",
            application_url="https://apply.partner.test/jobs/1",
        )
        version = SourceVersion.objects.create(
            source=source,
            canonical_url=source.source_url,
            content_hash="e" * 64,
            is_applied=True,
        )
        result = publish_candidates(source, [candidate], version)[0]
        batch = RecruitmentBatch.objects.get(pk=result.batch_id)
        self.assertContains(self.client.get("/"), batch.official_page_url)
        ApprovedApplicationHost.objects.filter(source=source).update(
            approval_digest="0" * 64
        )
        self.assertNotContains(self.client.get("/"), batch.official_page_url)

    def test_history_positions_remain_editable(self):
        batch = publish_formal_notice(
            self.source,
            identity_key="history-progress",
            status=RecruitmentBatch.Status.EXPIRED,
        )
        self.assertContains(self.client.get("/history/"), batch.official_page_url)
        self.client.post(f"/batches/{batch.pk}/progress/", {"status": "interviewed"})
        self.assertEqual(batch.application_progress.status, "interviewed")

    def test_removed_position_progress_route_is_not_retained(self):
        batch = publish_formal_notice(
            self.source, identity_key="hidden-progress", status=RecruitmentBatch.Status.EXPIRED
        )
        hidden = RecruitmentPosition.objects.create(
            batch=batch,
            position_key="hidden",
            title="非可信投影岗位",
            location_text="北京",
            normalized_locations=["北京"],
        )
        response = self.client.post(
            f"/positions/{hidden.pk}/progress/", {"status": "applied"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ApplicationProgress.objects.filter(batch=batch).exists())

    def test_formal_home_never_contains_preview_companies(self):
        response = self.client.get("/")
        self.assertNotContains(response, "星河科技")
        self.assertNotContains(response, "模拟数据，不是线上岗位")

    def test_dashboard_paginates_twenty_batches_and_preserves_query(self):
        for index in range(21):
            publish_formal_notice(
                self.source,
                identity_key=f"page-{index}",
                title=f"分页批次 {index}",
                hash_character=hex(index % 16)[2:],
            )
        first_page = self.client.get("/", {"company": "Phase", "city": ["北京", "上海"]})
        self.assertEqual(len(first_page.context["batches"]), 20)
        self.assertContains(first_page, "company=Phase")
        self.assertContains(first_page, "city=%E5%8C%97%E4%BA%AC")
        second_page = self.client.get("/?company=Phase&city=北京&city=上海&page=2")
        self.assertEqual(len(second_page.context["batches"]), 1)

    def test_batch_position_fragment_loads_all_positions(self):
        candidate = complete_candidate(self.source, identity_key="expand-four")
        positions = list(candidate.positions)
        for index in range(2, 7):
            positions.append(PositionCandidate(
                position_key=f"extra-{index}",
                title=f"额外岗位 {index}",
                location_text="北京",
                raw_text=f"额外岗位 {index} 北京",
                application_url=None,
                field_evidence={
                    "position_title": field_evidence(f"额外岗位 {index}", f"#extra-{index} .title"),
                    "location": field_evidence("北京", f"#extra-{index} .location"),
                },
            ))
        result = publish_candidates(
            self.source, [replace(candidate, positions=tuple(positions))], self.version()
        )[0]
        batch = RecruitmentBatch.objects.get(pk=result.batch_id)
        home = self.client.get("/")
        self.assertContains(home, "另有 4 个岗位")
        batch_vm = next(item for item in home.context["batches"] if item.id == batch.pk)
        self.assertEqual(len(batch_vm.preview_positions), 2)
        fragment = self.client.get(f"/batches/{batch.pk}/positions/")
        self.assertEqual(fragment.content.count(b'class="position-item"'), 6)

    def test_batches_and_positions_sort_by_effective_change_date(self):
        candidate = complete_candidate(self.source, identity_key="sort-first")
        second = PositionCandidate(
            position_key="newer-position",
            title="更新岗位",
            location_text="上海",
            raw_text="更新岗位 上海",
            application_url=None,
            field_evidence={
                "position_title": field_evidence("更新岗位", "#newer .title"),
                "location": field_evidence("上海", "#newer .location"),
                "raw_text": field_evidence("更新岗位 上海", "#newer .details"),
            },
        )
        first_result = publish_candidates(
            self.source,
            [replace(candidate, positions=candidate.positions + (second,))],
            self.version(),
        )[0]
        other = publish_formal_notice(
            self.source, identity_key="sort-second", hash_character="8"
        )
        first_batch = RecruitmentBatch.objects.get(pk=first_result.batch_id)
        first_position = first_batch.positions.get(position_key="position-1")
        newer_position = first_batch.positions.get(position_key="newer-position")
        RecruitmentPosition.objects.filter(pk=first_position.pk).update(
            content_changed_at=datetime(2026, 8, 24, 8, tzinfo=datetime_timezone.utc),
            first_seen_at=datetime(2026, 8, 24, 8, tzinfo=datetime_timezone.utc),
        )
        RecruitmentPosition.objects.filter(pk=newer_position.pk).update(
            content_changed_at=datetime(2026, 8, 28, 8, tzinfo=datetime_timezone.utc),
            first_seen_at=datetime(2026, 8, 28, 8, tzinfo=datetime_timezone.utc),
        )
        RecruitmentPosition.objects.filter(batch=other).update(
            content_changed_at=datetime(2026, 8, 26, 8, tzinfo=datetime_timezone.utc),
            first_seen_at=datetime(2026, 8, 26, 8, tzinfo=datetime_timezone.utc),
        )

        response = self.client.get("/")
        batches = list(response.context["batches"])
        self.assertEqual(batches[0].id, first_batch.pk)
        self.assertEqual(batches[0].positions[0].id, newer_position.pk)

    def test_position_fragment_preserves_position_and_city_filters(self):
        candidate = complete_candidate(self.source, identity_key="expand-filter")
        extra = PositionCandidate(
            position_key="shanghai-product",
            title="产品经理",
            location_text="上海",
            raw_text="上海产品岗位",
            application_url=None,
            field_evidence={
                "position_title": field_evidence("产品经理", "#product .title"),
                "location": field_evidence("上海", "#product .location"),
            },
        )
        result = publish_candidates(
            self.source, [replace(candidate, positions=candidate.positions + (extra,))], self.version()
        )[0]
        fragment = self.client.get(
            f"/batches/{result.batch_id}/positions/?position=产品&city=上海"
        )
        self.assertContains(fragment, "产品经理")
        self.assertNotContains(fragment, candidate.positions[0].title)

    def test_company_and_recruitment_type_use_stable_codes_in_formal_and_preview(self):
        publish_formal_notice(self.source, identity_key="typed-filter")
        company_type = self.source.organization.company_type
        formal = self.client.get(
            f"/?company_type={company_type}&recruitment_type=unknown"
        )
        self.assertContains(formal, self.source.organization.name)
        self.assertNotContains(self.client.get("/?company_type=state_owned"), self.source.organization.name)
        with self.settings(DEBUG=True):
            preview = self.client.get(
                "/preview/phase-02/?company_type=private&recruitment_type=autumn"
            )
        self.assertContains(preview, "星河科技")

    def test_batch_field_change_refreshes_position_but_identical_check_does_not(self):
        candidate = complete_candidate(self.source, identity_key="batch-change")
        result = publish_candidates(self.source, [candidate], self.version())[0]
        position = RecruitmentBatch.objects.get(pk=result.batch_id).positions.get()
        original = position.content_changed_at
        changed = replace(candidate, deadline=date(2027, 1, 31), field_evidence={
            **candidate.field_evidence,
            "deadline": field_evidence("2027-01-31", "#batch .deadline"),
        })
        publish_candidates(self.source, [changed], self.version())
        position.refresh_from_db()
        self.assertGreater(position.content_changed_at, original)
        changed_at = position.content_changed_at
        publish_candidates(self.source, [changed], self.version())
        position.refresh_from_db()
        self.assertEqual(position.content_changed_at, changed_at)

    def test_explicit_withdrawal_refreshes_position_change_time(self):
        candidate = complete_candidate(self.source, identity_key="withdraw-time")
        result = publish_candidates(self.source, [candidate], self.version())[0]
        position = RecruitmentBatch.objects.get(pk=result.batch_id).positions.get()
        original = position.content_changed_at
        publish_candidates(self.source, [replace(candidate, withdrawn=True)], self.version())
        position.refresh_from_db()
        self.assertFalse(position.is_current)
        self.assertEqual(position.content_changed_at, position.removed_at)
        self.assertGreater(position.content_changed_at, original)

    def test_first_truncated_json_page_is_rejected_fail_closed(self):
        self.source.adapter_name = "json_api"
        self.source.save(update_fields=["adapter_name"])
        candidate = replace(
            complete_candidate(self.source, identity_key="truncated-first"),
            positions_complete=False,
        )
        result = publish_candidates(self.source, [candidate], self.version())[0]
        self.assertEqual(result.action, "rejected")
        self.assertIn("incomplete_position_coverage", result.reasons)
        self.assertFalse(
            RecruitmentBatch.objects.filter(identity_key="truncated-first").exists()
        )

    def test_unproven_details_cannot_change_recruitment_classification(self):
        candidate = complete_candidate(self.source, identity_key="unproven-classification")
        unproven_position = replace(
            candidate.positions[0],
            raw_text="只有这段未举证详情写了校园招聘",
            field_evidence={
                key: value
                for key, value in candidate.positions[0].field_evidence.items()
                if key != "raw_text"
            },
        )
        candidate = replace(
            candidate,
            title="普通人才项目",
            recruitment_type="未知",
            positions=(unproven_position,),
            field_evidence={
                **candidate.field_evidence,
                "title": field_evidence("普通人才项目", "#batch h2"),
                "recruitment_type": field_evidence(
                    "未知", "#batch .type", "unknown"
                ),
            },
        )
        result = publish_candidates(self.source, [candidate], self.version())[0]
        self.assertEqual(result.action, "rejected")
        self.assertIn("not_eligible_recruitment_type", result.reasons)
        self.assertFalse(
            RecruitmentBatch.objects.filter(identity_key="unproven-classification").exists()
        )
