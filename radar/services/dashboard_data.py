from datetime import date, timedelta

from django.core.paginator import Paginator
from django.utils import timezone

from radar.models import ApplicationLink, ApplicationProgress, RecruitmentBatch
from radar.services.announcements import announcement_direction_projection_is_complete
from radar.services.evidence import trusted_historical_projection
from radar.services.locations import (
    matches_selected_cities,
    normalize_locations,
    province_locations,
)
from radar.viewmodels import (
    DashboardSummaryVM,
    MAX_SELECTED_PROVINCES,
    PREVIEW_COMPANY_TYPE_CHOICES,
    PREVIEW_RECRUITMENT_TYPE_CHOICES,
    RecruitmentBatchVM,
    RecruitmentPositionVM,
)


def _effective_date(position) -> date:
    candidates = [
        position.source_updated_on,
        timezone.localdate(position.content_changed_at) if position.content_changed_at else None,
        timezone.localdate(position.first_seen_at) if position.first_seen_at else None,
    ]
    return max(value for value in candidates if value is not None)


def _position_vm(
    position,
    *,
    batch_official_page_url: str,
    include_historical_links: bool = False,
    allowed_link_ids: set[int] | None = None,
) -> RecruitmentPositionVM:
    link = next(
        (
            item.href
            for item in position.application_links.all()
            if item.batch_id == position.batch_id
            and (item.is_current or include_historical_links)
            and item.link_type in {
                ApplicationLink.LinkType.APPLICATION,
                ApplicationLink.LinkType.EMAIL,
                ApplicationLink.LinkType.MINI_PROGRAM,
            }
            and (allowed_link_ids is None or item.pk in allowed_link_ids)
            and item.href
        ),
        None,
    )
    return RecruitmentPositionVM(
        id=position.pk,
        title=position.title,
        locations=tuple(normalize_locations(position.location_text) or ["地点未说明"]),
        details=position.raw_text or "官网未提供岗位详情。",
        application_url=link,
        uses_batch_page=link is None,
        effective_updated_on=_effective_date(position),
        is_current=position.is_current,
        kind=position.kind,
    )


def _position_keywords(params) -> tuple[str, ...]:
    value = params.get("position", "")
    return tuple(item.strip().casefold() for item in value.replace("，", ",").split(",") if item.strip())


GENERIC_GRADUATE_AUDIENCE = "应届毕业生（届次未说明）"
GENERIC_MIXED_AUDIENCE = "应届毕业生/实习生（届次未说明）"
def canonical_audience(
    recruitment_type: str,
    target_audience: str,
) -> str:
    """Display only the audience explicitly stored from the primary announcement."""

    value = str(target_audience or "").strip()
    if value in {"校招", "校园招聘", "应届", "应届毕业生", ""}:
        return GENERIC_GRADUATE_AUDIENCE
    if "应届" in value and "实习" in value:
        return GENERIC_MIXED_AUDIENCE
    return value or "未说明"


def filter_position_vms(positions, params):
    selected_cities = params.getlist("city")[:MAX_SELECTED_PROVINCES]
    keywords = _position_keywords(params)
    return [
        item
        for item in positions
        if (not selected_cities or matches_selected_cities(item.locations, selected_cities))
        and (not keywords or any(keyword in item.title.casefold() for keyword in keywords))
    ]


def _summary(batches: list[RecruitmentBatchVM], today: date) -> DashboardSummaryVM:
    positions = [position for batch in batches for position in batch.positions]
    today_companies = {batch.company for batch in batches if batch.effective_updated_on == today}
    recent_companies = {
        batch.company for batch in batches if batch.effective_updated_on >= today - timedelta(days=2)
    }
    return DashboardSummaryVM(
        active_positions=sum(1 for item in positions if item.is_current),
        changed_in_3_days=sum(item.effective_updated_on >= today - timedelta(days=2) for item in positions),
        deadline_in_7_days=0,
        applications_in_progress=sum(
            batch.progress_value in {"applied", "written_test", "interviewed"} for batch in batches
        ),
        today_updated_companies=len(today_companies),
        updated_companies_in_3_days=len(recent_companies),
        deadline_companies_in_1_day=0,
        deadline_companies_in_3_days=0,
    )


def build_orm_dashboard(params, *, history: bool = False):
    queryset = RecruitmentBatch.objects.historical() if history else RecruitmentBatch.objects.formal()
    queryset = queryset.filter(
        status__in=(RecruitmentBatch.Status.EXPIRED, RecruitmentBatch.Status.WITHDRAWN)
        if history else (RecruitmentBatch.Status.ACTIVE,)
    ).select_related("organization", "application_progress", "primary_announcement").prefetch_related(
        "positions__application_links", "application_links"
    )
    if params.get("company"):
        queryset = queryset.filter(organization__name__icontains=params["company"])
    for key, lookup in (
        ("company_type", "organization__company_type"),
        ("recruitment_type", "recruitment_type"),
    ):
        values = params.getlist(key)
        if values:
            queryset = queryset.filter(**{f"{lookup}__in": values})
    if params.get("industry"):
        queryset = queryset.filter(organization__industry__icontains=params["industry"])
    audience = params.get("audience") or params.get("target_audience")
    today = date.today()
    batches: list[RecruitmentBatchVM] = []
    available_audiences: set[str] = set()
    for batch in queryset:
        try:
            progress = batch.application_progress
        except ApplicationProgress.DoesNotExist:
            progress = None
        progress_value = progress.status if progress else ApplicationProgress.Status.NOT_APPLIED
        selected_progress = set(params.getlist("progress"))
        if selected_progress and progress_value not in selected_progress:
            continue
        projection = trusted_historical_projection(batch) if history else None
        if history:
            if projection:
                trusted_ids = set(projection.position_ids)
                positions = [item for item in batch.positions.all() if item.pk in trusted_ids]
            elif announcement_direction_projection_is_complete(batch, current_only=False):
                positions = [
                    item for item in batch.positions.all()
                    if item.kind == item.Kind.DIRECTION
                ]
            else:
                positions = []
        else:
            positions = [item for item in batch.positions.all() if item.is_current]
        target_audience = canonical_audience(
            batch.recruitment_type,
            batch.target_audience,
        )
        available_audiences.add(target_audience)
        if audience and target_audience != audience:
            continue
        position_vms = [
            _position_vm(
                position,
                batch_official_page_url=batch.official_page_url,
                include_historical_links=history,
                allowed_link_ids=(set(projection.application_link_ids) if projection else None),
            )
            for position in positions
        ]
        position_vms = filter_position_vms(position_vms, params)
        if not position_vms:
            continue
        position_vms.sort(key=lambda item: item.effective_updated_on, reverse=True)
        announcement = batch.primary_announcement
        batch_application_urls = tuple(
            item.href
            for item in batch.application_links.all()
            if item.position_id is None
            and item.is_current
            and item.link_type in {
                ApplicationLink.LinkType.APPLICATION,
                ApplicationLink.LinkType.EMAIL,
                ApplicationLink.LinkType.MINI_PROGRAM,
            }
            and item.href
        )
        batch_application_notes = tuple(
            " ".join(
                value
                for value in (
                    f"微信小程序：{item.miniprogram_name}",
                    item.miniprogram_path,
                    item.instructions,
                )
                if value
            )
            for item in batch.application_links.all()
            if item.position_id is None
            and item.is_current
            and item.link_type == ApplicationLink.LinkType.MINI_PROGRAM
            and item.miniprogram_name
            and not item.href
        )
        batches.append(RecruitmentBatchVM(
            id=batch.pk,
            company=batch.organization.name,
            company_type=batch.organization.get_company_type_display(),
            industry=batch.organization.industry,
            title=batch.title,
            recruitment_type=batch.get_recruitment_type_display(),
            target_audience=target_audience,
            deadline=batch.deadline,
            status=batch.get_status_display(),
            official_page_url=batch.official_page_url,
            progress_value=progress_value,
            progress_label=progress.get_status_display() if progress else "未投递",
            positions=tuple(position_vms),
            announcement_url=(announcement.url if announcement else batch.official_page_url),
            announcement_label=(announcement.get_source_kind_display() if announcement else "旧批次页"),
            announcement_instructions=(
                f"微信小程序：{announcement.miniprogram_name} {announcement.miniprogram_path}".strip()
                if announcement and not announcement.url else ""
            ),
            batch_application_urls=batch_application_urls,
            batch_application_notes=batch_application_notes,
        ))
    batches.sort(key=lambda item: item.effective_updated_on, reverse=True)
    page = Paginator(batches, 20).get_page(params.get("page", 1))
    return (
        page,
        _summary(batches, today),
        available_city_choices(batches),
        tuple(sorted(available_audiences)),
    )


def mock_dashboard(params, *, history: bool = False):
    today = date.today()
    rows = (
        ("星河科技", "民企", "互联网/科技", "星河科技 2027 届校园招聘", "秋招", "2027届", 7,
         (("上海", "浙江"), ("北京",), ("广东",), ("上海",), ("全国",), ("广东",), ("远程",)), 6),
        ("远航能源", "央国企", "能源/电力", "远航能源集团秋季校园招聘", "秋招", "2026届", 2,
         (("湖北", "全国"), ("北京",)), None),
        ("云帆智能", "外资", "互联网/科技", "云帆智能长期实习生招聘", "实习", "实习生", 2,
         (("远程", "浙江"), ("远程",)), 66),
        ("青峦银行", "银行", "金融", "青峦银行管理培训生项目", "秋招", "2025届", 2,
         (("北京", "上海", "广东"), ("北京",)), 25),
        ("矩阵机器人", "中外合资", "制造业", "矩阵机器人全球校园招聘", "秋招提前批", "2028届", 2,
         (("广东",), ("上海",)), 96),
        ("海岳通信", "民企", "通信", "海岳通信春季补录", "春招补录", "2024届", 2,
         (("四川",), ("湖北",)), -57),
    )
    titles = (
        "后端开发工程师", "算法工程师", "产品经理", "数据分析师", "测试开发工程师",
        "客户端开发工程师", "交互设计师",
    )
    batches: list[RecruitmentBatchVM] = []
    for index, (company, company_type, industry, title, recruitment_type, audience, count, locations, days) in enumerate(rows, 1):
        batch_url = f"https://example.invalid/batches/{index}"
        positions = tuple(RecruitmentPositionVM(
            id=f"mock-{index}-{number}",
            title=(titles[number - 1] if index == 1 else (
                ("电气工程师", "财务管理岗") if index == 2 else
                ("前端开发实习生", "交互设计实习生") if index == 3 else
                ("金融科技管培生", "风险管理岗") if index == 4 else
                ("机器人控制算法", "机械设计") if index == 5 else
                ("网络研发工程师", "无线通信工程师")
            )[number - 1]),
            locations=locations[number - 1],
            details="此处仅展示模拟岗位名称与地点，不连接企业网站。",
            application_url=(batch_url if index == 2 and number == 2 else "https://example.invalid/apply"),
            uses_batch_page=index == 2 and number == 2,
            effective_updated_on=(today - timedelta(days=index + number - 2) if index != 6 else today - timedelta(days=106 + number)),
            is_current=index != 6,
        ) for number in range(1, count + 1))
        batches.append(RecruitmentBatchVM(
            id=f"mock-{index}", company=company, company_type=company_type, industry=industry,
            title=title, recruitment_type=recruitment_type, target_audience=audience,
            deadline=(today + timedelta(days=days) if days is not None else None),
            status="已截止" if index == 6 else "招聘中", official_page_url=batch_url,
            progress_value="applied" if index == 2 else "not_applied",
            progress_label="已投递" if index == 2 else "未投递", positions=positions,
            announcement_url=batch_url,
            announcement_label="企业官网公告",
        ))

    visible = [item for item in batches if (item.status != "招聘中") == history]
    company = params.get("company", "").casefold()
    selected_company_types = {
        dict(PREVIEW_COMPANY_TYPE_CHOICES).get(value, value) for value in params.getlist("company_type")
    }
    selected_recruitment_types = {
        dict(PREVIEW_RECRUITMENT_TYPE_CHOICES).get(value, value) for value in params.getlist("recruitment_type")
    }
    audience = params.get("audience") or params.get("target_audience")
    selected_progress = set(params.getlist("progress"))
    filtered: list[RecruitmentBatchVM] = []
    for batch in visible:
        if company and company not in batch.company.casefold():
            continue
        if selected_company_types and batch.company_type not in selected_company_types:
            continue
        if params.get("industry") and params["industry"] not in batch.industry:
            continue
        if selected_recruitment_types and batch.recruitment_type not in selected_recruitment_types:
            continue
        if audience and audience != batch.target_audience:
            continue
        positions = filter_position_vms(batch.positions, params)
        if positions and (not selected_progress or batch.progress_value in selected_progress):
            filtered.append(RecruitmentBatchVM(**{**batch.__dict__, "positions": tuple(positions)}))
    filtered.sort(key=lambda item: item.effective_updated_on, reverse=True)
    return filtered, _summary(filtered, today)


def available_city_choices(batches) -> tuple[str, ...]:
    locations = {
        city for batch in batches for position in batch.positions for city in position.locations
        if city and city != "地点未说明"
    }
    provinces = set(province_locations(locations))
    ordered = sorted(provinces - {"全国", "远程", "海外"})
    return tuple(
        ordered
        + [item for item in ("全国", "远程", "海外") if item in provinces]
    )
