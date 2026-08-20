from django.contrib import messages
from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from radar.forms import ApplicationProgressForm, NoticeFilterForm
from radar.models import (ApplicationLink, ApplicationProgress, NoticePosition,
                          RecruitmentNotice)
from radar.services.evidence import trusted_historical_projection
from radar.services.update_runner import run_update
from radar.services.update_status import (expected_scheduled_date,
                                          latest_source_failures,
                                          latest_successful_update,
                                          scheduled_run_is_missing)


def dashboard(request: HttpRequest) -> HttpResponse:
    form = NoticeFilterForm(request.GET)
    form.is_valid()
    values = form.cleaned_data if form.is_valid() else {}
    status = values.get("status") or RecruitmentNotice.Status.ACTIVE
    history_requested = status in {
        RecruitmentNotice.Status.EXPIRED,
        RecruitmentNotice.Status.WITHDRAWN,
    }
    base_notices = (
        RecruitmentNotice.objects.historical()
        if history_requested
        else RecruitmentNotice.objects.formal()
    )
    notices = base_notices.filter(status=status).select_related(
        "organization"
    ).order_by("organization__name", "title")
    if values.get("company"):
        notices = notices.filter(organization__name__icontains=values["company"])
    for field, lookup in (("company_type", "organization__company_type"), ("industry", "organization__industry"), ("recruitment_type", "recruitment_type"), ("target_audience", "target_audience")):
        if values.get(field):
            notices = notices.filter(**{f"{lookup}__icontains": values[field]})
    if values.get("deadline_before"):
        notices = notices.filter(deadline__lte=values["deadline_before"])
    if history_requested:
        historical_notices = list(notices.prefetch_related("application_progress"))
        projections = {
            notice.pk: trusted_historical_projection(notice)
            for notice in historical_notices
        }
        position_ids = {
            position_id
            for projection in projections.values()
            if projection is not None
            for position_id in projection.position_ids
        }
        link_ids = {
            link_id
            for projection in projections.values()
            if projection is not None
            for link_id in projection.application_link_ids
        }
        positions_by_notice: dict[int, list[NoticePosition]] = {}
        for position in NoticePosition.objects.filter(pk__in=position_ids).order_by("pk"):
            positions_by_notice.setdefault(position.notice_id, []).append(position)
        links_by_notice: dict[int, list[ApplicationLink]] = {}
        for link in ApplicationLink.objects.filter(pk__in=link_ids).order_by("pk"):
            links_by_notice.setdefault(link.notice_id, []).append(link)
        projected_notices = []
        city = values.get("city")
        position_keyword = values.get("position", "").casefold()
        for notice in historical_notices:
            projection = projections[notice.pk]
            if projection is None:
                continue
            notice.visible_positions = positions_by_notice.get(notice.pk, [])
            notice.visible_application_links = links_by_notice.get(notice.pk, [])
            if city and not any(
                city in position.normalized_locations
                for position in notice.visible_positions
            ):
                continue
            if position_keyword and not any(
                position_keyword in position.title.casefold()
                for position in notice.visible_positions
            ):
                continue
            projected_notices.append(notice)
        notices = projected_notices
    else:
        if values.get("city"):
            notice_ids = [
                position.notice_id
                for position in NoticePosition.objects.filter(is_current=True)
                if values["city"] in position.normalized_locations
            ]
            notices = notices.filter(pk__in=notice_ids)
        if values.get("position"):
            matching_notice_ids = NoticePosition.objects.filter(
                is_current=True,
                title__icontains=values["position"],
            ).values_list("notice_id", flat=True)
            notices = notices.filter(pk__in=matching_notice_ids)
        notices = notices.distinct().prefetch_related(
            Prefetch(
                "positions",
                queryset=NoticePosition.objects.filter(is_current=True),
                to_attr="visible_positions",
            ),
            Prefetch(
                "application_links",
                queryset=ApplicationLink.objects.filter(is_current=True),
                to_attr="visible_application_links",
            ),
            "application_progress",
        )
    for notice in notices:
        try:
            notice.current_progress = notice.application_progress
        except ApplicationProgress.DoesNotExist:
            notice.current_progress = None
    now = timezone.now()
    return render(request, "radar/dashboard.html", {
        "filter_form": form,
        "notices": notices,
        "progress_choices": ApplicationProgress.Status.choices,
        "scheduled_run_missing": scheduled_run_is_missing(now),
        "expected_scheduled_date": expected_scheduled_date(now),
        "last_successful_update": latest_successful_update(),
        "source_failures": latest_source_failures(),
    })


@require_POST
def update_progress(request: HttpRequest, notice_id: int) -> HttpResponse:
    notice = get_object_or_404(RecruitmentNotice, pk=notice_id)
    progress, _ = ApplicationProgress.objects.get_or_create(notice=notice)
    form = ApplicationProgressForm(request.POST, instance=progress)
    if form.is_valid():
        form.save()
        messages.success(request, "投递进度已更新。")
    else:
        messages.error(request, "投递进度无效，未保存。")
    return redirect("dashboard")


@require_POST
def update_now(request: HttpRequest) -> HttpResponse:
    try:
        summary = run_update(trigger="manual")
    except Exception:
        messages.error(request, "手动更新异常，未能确认更新结果。")
        return redirect("dashboard")
    if summary.status == "failed":
        messages.error(request, "手动更新未执行：没有可成功完成的已启用核验来源。")
    elif summary.status == "partial_failure":
        messages.warning(request, f"手动更新部分失败：检查 {summary.sources_checked} 个来源，失败 {summary.sources_failed} 个，新增 {summary.notices_created} 条。")
    else:
        messages.info(request, f"手动更新完成：检查 {summary.sources_checked} 个来源，失败 {summary.sources_failed} 个，新增 {summary.notices_created} 条，更新 {summary.notices_updated} 条，未发布 {summary.notices_rejected} 条。")
    return redirect("dashboard")
