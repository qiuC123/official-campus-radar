import copy
import hashlib
import json

from django.db import migrations
from django.utils import timezone


ACTOR = "local-owner"


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _event_hash(source_id, from_state, to_state, reason, evidence, previous_hash):
    payload = json.dumps(
        {
            "source_id": source_id,
            "from_state": from_state,
            "to_state": to_state,
            "actor_label": ACTOR,
            "reason": reason,
            "evidence": evidence,
            "previous_event_hash": previous_hash,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _hash(payload)


def _append_source_event(SourceAdmissionEvent, source, from_state, to_state, reason, evidence):
    latest = SourceAdmissionEvent.objects.filter(source_id=source.pk).order_by("-pk").first()
    previous_hash = latest.event_hash if latest else "0" * 64
    SourceAdmissionEvent.objects.create(
        source_id=source.pk,
        from_state=from_state,
        to_state=to_state,
        actor_label=ACTOR,
        reason=reason,
        evidence=evidence,
        previous_event_hash=previous_hash,
        event_hash=_event_hash(
            source.pk,
            from_state,
            to_state,
            reason,
            evidence,
            previous_hash,
        ),
    )


def _reconfigure_source(
    SourceAdmissionEvent,
    source,
    *,
    source_url=None,
    source_type=None,
    official_entrypoint_url=None,
    parser_config,
):
    evidence = (
        "2026-09-01 official-site review confirmed the current recruitment project; "
        f"config_sha256={_hash(json.dumps(parser_config, ensure_ascii=False, sort_keys=True, separators=(',', ':')))}"
    )
    if source.admission_state == "enabled":
        _append_source_event(
            SourceAdmissionEvent,
            source,
            "enabled",
            "suspended",
            "replace mixed or stale recruitment scope",
            evidence,
        )
    source.admission_state = "suspended"
    source.is_active = False
    source.is_verified = True
    if source_url:
        source.source_url = source_url
    if source_type:
        source.source_type = source_type
    if official_entrypoint_url:
        source.official_entrypoint_url = official_entrypoint_url
    source.parser_config = parser_config
    source.save(
        update_fields=[
            "source_url",
            "source_type",
            "official_entrypoint_url",
            "parser_config",
            "admission_state",
            "is_active",
            "is_verified",
        ]
    )
    _append_source_event(
        SourceAdmissionEvent,
        source,
        "suspended",
        "verified",
        "verify exact current recruitment scope",
        evidence,
    )
    source.admission_state = "verified"
    source.save(update_fields=["admission_state"])
    _append_source_event(
        SourceAdmissionEvent,
        source,
        "verified",
        "enabled",
        "enable exact current recruitment scope",
        evidence,
    )
    source.admission_state = "enabled"
    source.is_active = True
    source.save(update_fields=["admission_state", "is_active"])


def _create_api_source(
    OfficialSource,
    SourceAdmissionEvent,
    organization,
    *,
    source_url,
    entrypoint,
    parser_config,
):
    source = OfficialSource.objects.filter(
        organization_id=organization.pk,
        source_url=source_url,
        adapter_name="json_api",
    ).first()
    if source is not None:
        if source.admission_state == "enabled" and source.parser_config == parser_config:
            return source
        _reconfigure_source(
            SourceAdmissionEvent,
            source,
            source_url=source_url,
            source_type="api",
            official_entrypoint_url=entrypoint,
            parser_config=parser_config,
        )
        return source
    evidence = "企业官网招聘入口与同域公开招聘接口已于2026-09-01只读核验"
    source = OfficialSource.objects.create(
        organization_id=organization.pk,
        source_type="api",
        source_url=source_url,
        official_entrypoint_url=entrypoint,
        admission_evidence=evidence,
        access_policy="低频、公开、无需登录访问",
        adapter_name="json_api",
        parser_config=parser_config,
        admission_state="candidate",
        is_verified=False,
        is_active=False,
    )
    _append_source_event(
        SourceAdmissionEvent,
        source,
        "",
        "candidate",
        "candidate imported from verified official project",
        evidence,
    )
    _append_source_event(
        SourceAdmissionEvent,
        source,
        "candidate",
        "verified",
        "verify official project API",
        evidence,
    )
    source.admission_state = "verified"
    source.is_verified = True
    source.save(update_fields=["admission_state", "is_verified"])
    _append_source_event(
        SourceAdmissionEvent,
        source,
        "verified",
        "enabled",
        "enable official project API",
        evidence,
    )
    source.admission_state = "enabled"
    source.is_active = True
    source.save(update_fields=["admission_state", "is_active"])
    return source


def _li_config(project_id, identity_key, title, recruitment_type, audience, page_url):
    return {
        "endpoint": "https://api-web.lixiang.com/osd-hr-recruitment-website/v1/recruit/school/job-page",
        "method": "GET",
        "params": {"project_id": project_id},
        "headers": {},
        "body_encoding": "query",
        "pagination": {
            "mode": "page_index",
            "page_param": "page",
            "size_param": "page_size",
            "page_size": 100,
            "start_page": 1,
            "max_pages": 20,
            "total_kind": "pages",
        },
        "list_path": "data.items",
        "total_path": "data.total_pages",
        "field_map": {
            "position_key": "id",
            "title": "title",
            "location": "location_title",
        },
        "row_filters": [],
        "request_delay_seconds": 1,
        "batch": {
            "identity_key": identity_key,
            "title": title,
            "official_page_url": page_url,
            "recruitment_type": recruitment_type,
            "target_audience": audience,
            "published_on": "",
            "deadline": "",
        },
    }


def _midea_config(project_rule_id, identity_key, title, recruitment_type, audience, page_url):
    return {
        "endpoint": "https://careers.midea.com/backend/school/position/common/position/list",
        "method": "POST",
        "body": {
            "keyword": None,
            "pageIndex": 1,
            "pageSize": 20,
            "projectRuleId": project_rule_id,
            "recruitCategoryIds": [],
            "workPlaceCodes": [],
        },
        "headers": {
            "Accept": "application/json",
            "Referer": "https://careers.midea.com/",
        },
        "body_encoding": "json",
        "pagination": {
            "mode": "page_index",
            "page_param": "pageIndex",
            "size_param": "pageSize",
            "page_size": 20,
            "start_page": 1,
            "max_pages": 20,
            "total_kind": "items",
        },
        "list_path": "data.data",
        "total_path": "data.total",
        "field_map": {
            "position_key": "projectPositionId",
            "title": "projectPositionName",
            "location": "workplaceDtoList[].workPlaceName||workPlaceCode",
        },
        "row_filters": [],
        "request_delay_seconds": 1,
        "batch": {
            "identity_key": identity_key,
            "title": title,
            "official_page_url": page_url,
            "recruitment_type": recruitment_type,
            "target_audience": audience,
            "published_on": "",
            "deadline": "",
        },
    }


def _geely_config():
    portal = "https://campus.geely.com/campus-recruitment/geely/78436?locale=zh-CN#/jobs"
    base_batch = {
        "identity_key": "phase-02:p16",
        "title": "吉利控股 2027 届校园招聘",
        "official_page_url": portal,
        "recruitment_type": "autumn",
        "target_audience": "2027届及在校生",
        "published_on": "",
        "deadline": "",
    }
    partitions = []
    for identity, title, recruitment_type, audience, signal in (
        (
            "official-project:geely:2027-autumn",
            "吉利控股 2027 届秋季校园招聘",
            "autumn",
            "2027届",
            "2027届秋招",
        ),
        (
            "official-project:geely:2027-internship",
            "吉利控股 2027 届实习生招聘",
            "internship",
            "在校生",
            "2027届实习生",
        ),
    ):
        batch = copy.deepcopy(base_batch)
        batch.update(
            {
                "identity_key": identity,
                "title": title,
                "recruitment_type": recruitment_type,
                "target_audience": audience,
            }
        )
        partitions.append(
            {
                "batch": batch,
                "row_filters": [
                    {
                        "path": "customFields[].value",
                        "contains_any": [signal],
                    }
                ],
            }
        )
    return {
        "org_id": "geely",
        "site_id": 78436,
        "mode": "campus",
        "page_size": 100,
        "max_pages": 30,
        "request_delay_seconds": 1,
        "row_filters": [
            {
                "path": "customFields[].value",
                "contains_any": ["2027届秋招", "2027届实习生"],
            }
        ],
        "batch": base_batch,
        "batch_partitions": partitions,
    }


def _bosch_config():
    return {
        "endpoint": "https://api.smartrecruiters.com/v1/companies/BoschGroup/postings",
        "method": "GET",
        "params": {
            "country": "cn",
            "limit": 100,
            "offset": 0,
            "q": "校招",
        },
        "headers": {
            "Accept": "application/json",
            "Referer": "https://www.bosch.com.cn/careers/job-offers/",
        },
        "body_encoding": "query",
        "pagination": {
            "mode": "offset",
            "page_param": "offset",
            "size_param": "limit",
            "page_size": 100,
            "start_offset": 0,
            "max_pages": 5,
            "total_kind": "items",
        },
        "list_path": "content",
        "total_path": "totalFound",
        "field_map": {
            "position_key": "id",
            "title": "name",
            "location": "location.fullLocation||location.city",
        },
        "row_filters": [{"path": "name", "contains_any": ["27届校招"]}],
        "request_delay_seconds": 1,
        "batch": {
            "identity_key": "phase-02:f05",
            "title": "博世中国 2027 届秋季校园招聘",
            "official_page_url": "https://www.bosch.com.cn/careers/job-offers/",
            "recruitment_type": "autumn",
            "target_audience": "2027届",
            "published_on": "",
            "deadline": "",
        },
    }


def _admit_batch(
    RecruitmentAnnouncement,
    RecruitmentBatch,
    AnnouncementFieldEvidence,
    *,
    source,
    identity_key,
    announcement_identity,
    title,
    url,
    recruitment_type,
    target_audience,
    title_excerpt,
    type_excerpt,
    audience_excerpt,
    availability_excerpt,
):
    verified_at = timezone.now()
    fingerprint = _hash(
        "|".join(
            [title, url, recruitment_type, target_audience, availability_excerpt]
        )
    )
    announcement, _ = RecruitmentAnnouncement.objects.update_or_create(
        organization_id=source.organization_id,
        source_kind="recruiting_system",
        identity_key=announcement_identity,
        defaults={
            "source_id": source.pk,
            "title": title,
            "url": url,
            "last_verified_at": verified_at,
            "identity_evidence": "企业官网招聘入口与官方公开招聘项目接口相互印证",
            "content_sha256": fingerprint,
            "evidence_sha256": fingerprint,
            "verification_status": "verified",
            "verification_method": "http",
        },
    )
    batch, _ = RecruitmentBatch.objects.update_or_create(
        source_id=source.pk,
        identity_key=identity_key,
        defaults={
            "organization_id": source.organization_id,
            "title": title,
            "official_page_url": url,
            "primary_announcement_id": announcement.pk,
            "announcement_admission": "admitted",
            "recruitment_type": recruitment_type,
            "target_audience": target_audience,
            "status": "active",
        },
    )
    fields = {
        "title": (title, title_excerpt),
        "recruitment_type": (recruitment_type, type_excerpt),
        "target_audience": (target_audience, audience_excerpt),
        "availability": ("active", availability_excerpt),
    }
    for field_name, (value, excerpt) in fields.items():
        AnnouncementFieldEvidence.objects.get_or_create(
            batch_id=batch.pk,
            announcement_id=announcement.pk,
            field_name=field_name,
            locator=f"official-project[{identity_key}]/{field_name}",
            parsed_value=value,
            defaults={"excerpt": excerpt, "value_hash": _hash(value)},
        )
    return batch


def admit_first_official_site_group(apps, schema_editor):
    Organization = apps.get_model("radar", "Organization")
    OfficialSource = apps.get_model("radar", "OfficialSource")
    SourceAdmissionEvent = apps.get_model("radar", "SourceAdmissionEvent")
    RecruitmentAnnouncement = apps.get_model("radar", "RecruitmentAnnouncement")
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    AnnouncementFieldEvidence = apps.get_model("radar", "AnnouncementFieldEvidence")

    organizations = {
        organization.name: organization
        for organization in Organization.objects.filter(
            name__in=("理想汽车", "吉利控股", "美的集团", "博世中国")
        )
    }
    if len(organizations) != 4:
        return

    li = organizations["理想汽车"]
    li_main_source = OfficialSource.objects.filter(
        organization_id=li.pk, adapter_name="json_api"
    ).order_by("pk").first()
    li_specs = (
        (
            25,
            "official-project:lixiang:25",
            "理想汽车 2027 校园招聘",
            "autumn",
            "2027届",
            "https://www.lixiang.com/employ/campus/list.html?project_id=25",
            "2027校园招聘",
            "当前招聘季于秋季阶段开放",
            "正式批毕业时间为2026年9月至2027年8月",
        ),
        (
            24,
            "official-project:lixiang:24",
            "理想汽车 2027“理想+”招聘",
            "autumn",
            "2027届",
            "https://www.lixiang.com/employ/campus/list.html?project_id=24",
            "2027“理想+”",
            "当前招聘季于秋季阶段开放",
            "理想+毕业时间为2026年1月至2027年8月",
        ),
        (
            23,
            "official-project:lixiang:23",
            "理想汽车日常实习生招聘",
            "internship",
            "在校生",
            "https://www.lixiang.com/employ/campus/list.html?project_id=23",
            "实习生招聘",
            "官方项目类型为实习生招聘",
            "面向可参加实习的在校生",
        ),
    )
    li_sources = []
    for index, spec in enumerate(li_specs):
        project_id, identity, title, recruitment_type, audience, url, _, _, _ = spec
        config = _li_config(
            project_id, identity, title, recruitment_type, audience, url
        )
        if index == 0 and li_main_source is not None:
            _reconfigure_source(
                SourceAdmissionEvent,
                li_main_source,
                source_url="https://www.lixiang.com/employ/campus/list.html",
                source_type="api",
                official_entrypoint_url="https://www.lixiang.com/employ/campus/list.html",
                parser_config=config,
            )
            source = li_main_source
        else:
            source = _create_api_source(
                OfficialSource,
                SourceAdmissionEvent,
                li,
                source_url=url,
                entrypoint="https://www.lixiang.com/employ/campus/list.html",
                parser_config=config,
            )
        li_sources.append(source)
    RecruitmentBatch.objects.filter(
        organization_id=li.pk,
        identity_key="phase-02:p20",
    ).update(announcement_admission="superseded")
    for source, spec in zip(li_sources, li_specs):
        project_id, identity, title, recruitment_type, audience, url, title_excerpt, type_excerpt, audience_excerpt = spec
        _admit_batch(
            RecruitmentAnnouncement,
            RecruitmentBatch,
            AnnouncementFieldEvidence,
            source=source,
            identity_key=identity,
            announcement_identity=f"official-project:lixiang:announcement:{project_id}",
            title=title,
            url=url,
            recruitment_type=recruitment_type,
            target_audience=audience,
            title_excerpt=title_excerpt,
            type_excerpt=type_excerpt,
            audience_excerpt=audience_excerpt,
            availability_excerpt="官方项目列表与岗位接口当前仍返回可投岗位",
        )

    geely = organizations["吉利控股"]
    geely_source = OfficialSource.objects.filter(
        organization_id=geely.pk, adapter_name="moka_public_api"
    ).order_by("pk").first()
    if geely_source is not None:
        geely_url = "https://campus.geely.com/campus-recruitment/geely/78436?locale=zh-CN#/jobs"
        _reconfigure_source(
            SourceAdmissionEvent,
            geely_source,
            source_url=geely_url,
            source_type="ats",
            official_entrypoint_url="https://campus.geely.com/",
            parser_config=_geely_config(),
        )
        RecruitmentBatch.objects.filter(
            organization_id=geely.pk,
            identity_key="phase-02:p16",
        ).update(announcement_admission="superseded")
        for identity, title, recruitment_type, audience, signal in (
            (
                "official-project:geely:2027-autumn",
                "吉利控股 2027 届秋季校园招聘",
                "autumn",
                "2027届",
                "2027届秋招",
            ),
            (
                "official-project:geely:2027-internship",
                "吉利控股 2027 届实习生招聘",
                "internship",
                "在校生",
                "2027届实习生",
            ),
        ):
            _admit_batch(
                RecruitmentAnnouncement,
                RecruitmentBatch,
                AnnouncementFieldEvidence,
                source=geely_source,
                identity_key=identity,
                announcement_identity=f"{identity}:announcement",
                title=title,
                url=geely_url,
                recruitment_type=recruitment_type,
                target_audience=audience,
                title_excerpt=signal,
                type_excerpt=f"官方职位字段招聘年度为{signal}",
                audience_excerpt="2027届" if recruitment_type == "autumn" else "实习生职位面向在校生",
                availability_excerpt="集团官网招聘入口与Moka公开职位接口当前返回开放岗位",
            )

    midea = organizations["美的集团"]
    midea_daily_source = OfficialSource.objects.filter(
        organization_id=midea.pk, adapter_name="json_api"
    ).order_by("pk").first()
    midea_specs = (
        (
            "055bb05d-1957-4ea0-bb21-873ca0164d84",
            "official-project:midea:2027-star",
            "美的集团 2027 届美的星校园招聘",
            "autumn",
            "2027届",
            "https://careers.midea.com/schoolOut/post?type=1",
            "美的集团2027届校园招聘；应届生招聘",
            "2026年9月当前处于2027届秋季招聘阶段",
            "2026年1月至2027年12月毕业的海内外在校本硕学生",
        ),
        (
            "ad1671b7-1d5a-41a5-a38c-fb810e731813",
            "official-project:midea:2027-doctor",
            "美的集团 2027 届博士招聘",
            "autumn",
            "2027届",
            "https://careers.midea.com/schoolOut/post?type=5",
            "美的集团2027届校园招聘；应届博士招聘",
            "2026年9月当前处于2027届秋季招聘阶段",
            "2026年1月至2027年12月毕业的海内外博士毕业生",
        ),
        (
            "4286dfd5-d9e8-4146-8f8c-98093833a81b",
            "phase-02:p17",
            "美的集团日常实习生招聘",
            "internship",
            "在校生",
            "https://careers.midea.com/schoolOut/post?type=2",
            "日常实习生招聘通道；实习生招聘",
            "官方项目类型为实习生招聘",
            "面向全体在校本硕博同学",
        ),
    )
    midea_sources = []
    for index, spec in enumerate(midea_specs):
        project_rule_id, identity, title, recruitment_type, audience, url, _, _, _ = spec
        config = _midea_config(
            project_rule_id, identity, title, recruitment_type, audience, url
        )
        if index == 2 and midea_daily_source is not None:
            _reconfigure_source(
                SourceAdmissionEvent,
                midea_daily_source,
                source_url="https://careers.midea.com/schoolOut/post?type=2",
                source_type="api",
                official_entrypoint_url="https://careers.midea.com/schoolOut",
                parser_config=config,
            )
            source = midea_daily_source
        else:
            source = _create_api_source(
                OfficialSource,
                SourceAdmissionEvent,
                midea,
                source_url=f"{url}&projectRuleId={project_rule_id}",
                entrypoint="https://careers.midea.com/schoolOut",
                parser_config=config,
            )
        midea_sources.append(source)
    for source, spec in zip(midea_sources, midea_specs):
        project_rule_id, identity, title, recruitment_type, audience, url, title_excerpt, type_excerpt, audience_excerpt = spec
        _admit_batch(
            RecruitmentAnnouncement,
            RecruitmentBatch,
            AnnouncementFieldEvidence,
            source=source,
            identity_key=identity,
            announcement_identity=f"official-project:midea:announcement:{project_rule_id}",
            title=title,
            url=url,
            recruitment_type=recruitment_type,
            target_audience=audience,
            title_excerpt=title_excerpt,
            type_excerpt=type_excerpt,
            audience_excerpt=audience_excerpt,
            availability_excerpt="官方项目接口status=1且当前返回开放岗位",
        )

    bosch = organizations["博世中国"]
    bosch_source = OfficialSource.objects.filter(
        organization_id=bosch.pk, adapter_name="ats_json_api"
    ).order_by("pk").first()
    if bosch_source is not None:
        _reconfigure_source(
            SourceAdmissionEvent,
            bosch_source,
            source_url="https://www.bosch.com.cn/careers/job-offers/",
            source_type="ats",
            official_entrypoint_url="https://www.bosch.com.cn/careers/job-offers/",
            parser_config=_bosch_config(),
        )
        _admit_batch(
            RecruitmentAnnouncement,
            RecruitmentBatch,
            AnnouncementFieldEvidence,
            source=bosch_source,
            identity_key="phase-02:f05",
            announcement_identity="official-project:bosch:2027-autumn",
            title="博世中国 2027 届秋季校园招聘",
            url="https://www.bosch.com.cn/careers/job-offers/",
            recruitment_type="autumn",
            target_audience="2027届",
            title_excerpt="27届校招职位",
            type_excerpt="27届校招职位于2026年8月6日至10日发布",
            audience_excerpt="职位名称明确标注27届校招",
            availability_excerpt="SmartRecruiters官方公开职位接口当前返回18个开放职位",
        )


def exclude_first_official_site_group(apps, schema_editor):
    RecruitmentBatch = apps.get_model("radar", "RecruitmentBatch")
    identities = [
        "official-project:lixiang:25",
        "official-project:lixiang:24",
        "official-project:lixiang:23",
        "official-project:geely:2027-autumn",
        "official-project:geely:2027-internship",
        "official-project:midea:2027-star",
        "official-project:midea:2027-doctor",
        "phase-02:p17",
        "phase-02:f05",
    ]
    RecruitmentBatch.objects.filter(identity_key__in=identities).update(
        announcement_admission="excluded"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("radar", "0030_add_tencent_internship_batches"),
    ]

    operations = [
        migrations.RunPython(
            admit_first_official_site_group,
            exclude_first_official_site_group,
        ),
    ]
