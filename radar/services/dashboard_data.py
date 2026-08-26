from datetime import date, timedelta

from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.dateparse import parse_date

from radar.models import ApplicationLink, ApplicationProgress, Organization, RecruitmentBatch
from radar.services.locations import matches_selected_cities, normalize_locations
from radar.services.evidence import trusted_historical_projection
from radar.viewmodels import DashboardSummaryVM, RecruitmentBatchVM, RecruitmentPositionVM


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
    try:
        progress = position.application_progress
    except ApplicationProgress.DoesNotExist:
        progress = None
    link = next(
        (
            item.url
            for item in position.application_links.all()
            if item.batch_id == position.batch_id
            and (item.is_current or include_historical_links)
            and item.link_type == ApplicationLink.LinkType.APPLICATION
            and (allowed_link_ids is None or item.pk in allowed_link_ids)
        ),
        None,
    )
    return RecruitmentPositionVM(
        id=position.pk,
        title=position.title,
        locations=tuple(normalize_locations(position.location_text) or ["地点未说明"]),
        details=position.raw_text or "官网未提供岗位详情。",
        application_url=link or batch_official_page_url,
        uses_batch_page=link is None,
        effective_updated_on=_effective_date(position),
        progress_value=progress.status if progress else ApplicationProgress.Status.NOT_APPLIED,
        progress_label=progress.get_status_display() if progress else "未投递",
        is_current=position.is_current,
    )


def filter_position_vms(positions, params):
    selected_cities = params.getlist("city")
    selected_progress = set(params.getlist("progress"))
    position_keyword = params.get("position", "").casefold()
    return [
        item
        for item in positions
        if (not selected_cities or matches_selected_cities(item.locations, selected_cities))
        and (not position_keyword or position_keyword in item.title.casefold())
        and (not selected_progress or item.progress_value in selected_progress)
    ]
def build_orm_dashboard(params, *, history: bool = False):
    queryset = RecruitmentBatch.objects.historical() if history else RecruitmentBatch.objects.formal()
    queryset = queryset.filter(
        status__in=(RecruitmentBatch.Status.EXPIRED, RecruitmentBatch.Status.WITHDRAWN)
        if history
        else (RecruitmentBatch.Status.ACTIVE,)
    ).select_related("organization").prefetch_related(
        "positions__application_progress", "positions__application_links"
    )
    if params.get("company"):
        queryset = queryset.filter(organization__name__icontains=params["company"])
    for key, lookup in (("company_type", "organization__company_type"), ("recruitment_type", "recruitment_type")):
        if params.get(key):
            queryset = queryset.filter(**{lookup: params[key]})
    for key, lookup in (("industry", "organization__industry"), ("target_audience", "target_audience")):
        if params.get(key):
            queryset = queryset.filter(**{f"{lookup}__icontains": params[key]})
    if params.get("deadline_before"):
        deadline_before = parse_date(params["deadline_before"])
        if deadline_before:
            queryset = queryset.filter(deadline__lte=deadline_before)

    batches: list[RecruitmentBatchVM] = []
    for batch in queryset:
        if history:
            projection = trusted_historical_projection(batch)
            trusted_ids = set(projection.position_ids) if projection else set()
            positions = [item for item in batch.positions.all() if item.pk in trusted_ids]
        else:
            positions = [item for item in batch.positions.all() if item.is_current]
        position_vms = [
            _position_vm(
                position,
                batch_official_page_url=batch.official_page_url,
                include_historical_links=history,
                allowed_link_ids=(set(projection.application_link_ids) if history and projection else None),
            )
            for position in positions
        ]
        position_vms = filter_position_vms(position_vms, params)
        if not position_vms:
            continue
        position_vms.sort(key=lambda item: item.effective_updated_on, reverse=True)
        batches.append(
            RecruitmentBatchVM(
                id=batch.pk,
                company=batch.organization.name,
                company_type=batch.organization.get_company_type_display(),
                industry=batch.organization.industry,
                title=batch.title,
                recruitment_type=batch.get_recruitment_type_display(),
                target_audience=batch.target_audience or "未说明",
                deadline=batch.deadline,
                status=batch.get_status_display(),
                official_page_url=batch.official_page_url,
                positions=tuple(position_vms),
            )
        )
    batches.sort(key=lambda item: item.effective_updated_on, reverse=True)
    today = date.today()
    positions = [position for batch in batches for position in batch.positions]
    summary = DashboardSummaryVM(
        active_positions=sum(1 for item in positions if item.is_current),
        changed_in_3_days=sum(item.effective_updated_on >= today - timedelta(days=2) for item in positions),
        deadline_in_7_days=sum(
            len(batch.positions)
            for batch in batches
            if batch.deadline and today <= batch.deadline <= today + timedelta(days=7)
        ),
        applications_in_progress=sum(
            item.progress_value in {"applied", "written_test", "interviewed"}
            for item in positions
        ),
    )
    city_choices = available_city_choices(batches)
    page = Paginator(batches, 20).get_page(params.get("page", 1))
    return page, summary, city_choices


def mock_dashboard(params, *, history: bool = False):
    today = date.today()
    rows = (
        ("星河科技", "互联网/科技", "互联网", "2027 届校园招聘", 5, ("上海", "杭州")),
        ("远航能源", "央企/国企", "新能源", "秋季校园招聘", 2, ("全国",)),
        ("云帆智能", "互联网/科技", "科技", "长期实习生招聘", 2, ("远程", "杭州")),
        ("青峦银行", "其他", "金融", "2027 管培生项目", 1, ("北京", "上海", "深圳")),
        ("矩阵机器人", "互联网/科技", "科技", "全球校园招聘", 1, ("深圳",)),
        ("海岳通信", "央企/国企", "科技", "2026 春季招聘", 1, ("成都",)),
    )
    batches = []
    for index, (company, company_type, industry, title, count, locations) in enumerate(rows, 1):
        batch_url = f"https://example.invalid/batches/{index}"
        positions = tuple(
            RecruitmentPositionVM(
                id=f"mock-{index}-{number}",
                title=("后端开发工程师" if number == 1 else f"模拟岗位 {number}"),
                locations=locations,
                details="负责真实业务场景中的设计、开发和协作。此处为较长模拟岗位描述。",
                application_url=batch_url if index == 2 and number == 2 else "https://example.invalid/apply",
                uses_batch_page=index == 2 and number == 2,
                effective_updated_on=today - timedelta(days=index + number - 2),
                progress_value="applied" if number == 2 else "not_applied",
                progress_label="已投递" if number == 2 else "未投递",
                is_current=index != 6,
            )
            for number in range(1, count + 1)
        )
        batches.append(
            RecruitmentBatchVM(
                id=f"mock-{index}", company=company, company_type=company_type,
                industry=industry, title=title, recruitment_type="校园招聘" if index != 3 else "实习",
                target_audience="2027届", deadline=None if index == 2 else today + timedelta(days=index),
                status="已截止" if index == 6 else "招聘中",
                official_page_url=batch_url, positions=positions,
            )
        )
    visible = [item for item in batches if (item.status != "招聘中") == history]
    company = params.get("company", "").casefold()
    position_keyword = params.get("position", "").casefold()
    selected_cities = params.getlist("city")
    selected_progress = set(params.getlist("progress"))
    filtered = []
    for batch in visible:
        if company and company not in batch.company.casefold():
            continue
        company_type_label = dict(Organization.CompanyType.choices).get(params.get("company_type"), params.get("company_type"))
        recruitment_type_label = dict(RecruitmentBatch.RecruitmentType.choices).get(params.get("recruitment_type"), params.get("recruitment_type"))
        if params.get("company_type") and company_type_label != batch.company_type:
            continue
        if params.get("industry") and params["industry"] not in batch.industry:
            continue
        if params.get("recruitment_type") and recruitment_type_label != batch.recruitment_type:
            continue
        if params.get("target_audience") and params["target_audience"] not in batch.target_audience:
            continue
        deadline_before = parse_date(params.get("deadline_before", ""))
        if deadline_before and (batch.deadline is None or batch.deadline > deadline_before):
            continue
        positions = [
            item for item in batch.positions
            if (not position_keyword or position_keyword in item.title.casefold())
            and matches_selected_cities(item.locations, selected_cities)
            and (not selected_progress or item.progress_value in selected_progress)
        ]
        if positions:
            filtered.append(RecruitmentBatchVM(**{**batch.__dict__, "positions": tuple(positions)}))
    positions = [item for batch in filtered for item in batch.positions]
    summary = DashboardSummaryVM(
        sum(item.is_current for item in positions),
        sum(item.effective_updated_on >= today - timedelta(days=2) for item in positions),
        sum(len(batch.positions) for batch in filtered if batch.deadline and today <= batch.deadline <= today + timedelta(days=7)),
        sum(item.progress_value in {"applied", "written_test", "interviewed"} for item in positions),
    )
    return filtered, summary


def available_city_choices(batches) -> tuple[str, ...]:
    cities = {
        city
        for batch in batches
        for position in batch.positions
        for city in position.locations
        if city and city != "地点未说明"
    }
    ordered = sorted(cities - {"全国", "远程"})
    return tuple(ordered + [item for item in ("全国", "远程") if item in cities or not cities])
