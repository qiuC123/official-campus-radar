from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from radar.models import ApplicationProgress, Organization, RecruitmentBatch
from radar.services.dashboard_data import (
    _position_vm,
    build_orm_dashboard,
    filter_position_vms,
    mock_dashboard,
)
from radar.services.evidence import trusted_historical_projection
from radar.services.update_runner import run_update
from radar.services.update_status import latest_source_failures, latest_successful_update, scheduled_run_is_missing
from radar.viewmodels import (
    AUDIENCE_CHOICES,
    PREVIEW_COMPANY_TYPE_CHOICES,
    PREVIEW_RECRUITMENT_TYPE_CHOICES,
    PROVINCE_CHOICES,
)


def _filter_context(request: HttpRequest, *, preview: bool) -> dict:
    return {
        "company_value": request.GET.get("company", ""),
        "position_value": request.GET.get("position", ""),
        "company_type_choices": (
            PREVIEW_COMPANY_TYPE_CHOICES if preview else Organization.CompanyType.choices
        ),
        "recruitment_type_choices": (
            PREVIEW_RECRUITMENT_TYPE_CHOICES if preview else RecruitmentBatch.RecruitmentType.choices
        ),
        "audience_choices": AUDIENCE_CHOICES,
        "selected_company_types": request.GET.getlist("company_type"),
        "selected_recruitment_types": request.GET.getlist("recruitment_type"),
        "selected_cities": request.GET.getlist("city"),
        "selected_progress": request.GET.getlist("progress"),
        "selected_audience": request.GET.get("audience", request.GET.get("target_audience", "")),
    }

def _render_dashboard(request: HttpRequest, *, history: bool = False) -> HttpResponse:
    page, summary, city_choices = build_orm_dashboard(request.GET, history=history)
    preserved_query = request.GET.copy()
    preserved_query.pop("page", None)
    context = {
        "page": page,
        "batches": page.object_list,
        "summary": summary,
        "history": history,
        "is_preview": False,
        "progress_choices": ApplicationProgress.Status.choices,
        "city_choices": tuple(dict.fromkeys((*city_choices, *request.GET.getlist("city")))),
        "scheduled_run_missing": scheduled_run_is_missing(timezone.now()),
        "last_successful_update": latest_successful_update(),
        "source_failures": latest_source_failures(),
        "query_without_page": preserved_query.urlencode(),
        "current_query": request.GET.urlencode(),
        "show_operations": request.user.is_staff,
    }
    context.update(_filter_context(request, preview=False))
    return render(request, "radar/phase02_dashboard.html", context)


def dashboard(request: HttpRequest) -> HttpResponse:
    return _render_dashboard(request)


def history(request: HttpRequest) -> HttpResponse:
    return _render_dashboard(request, history=True)


def phase02_preview(request: HttpRequest) -> HttpResponse:
    if not settings.DEBUG:
        raise Http404
    history = request.GET.get("view") == "history"
    batches, summary = mock_dashboard(request.GET, history=history)
    context = {
        "batches": batches,
        "summary": summary,
        "history": history,
        "is_preview": True,
        "progress_choices": ApplicationProgress.Status.choices,
        "city_choices": PROVINCE_CHOICES,
        "preview_health": request.GET.get("health", "normal"),
        "scheduled_run_missing": False,
        "source_failures": (),
        "show_operations": True,
    }
    context.update(_filter_context(request, preview=True))
    return render(request, "radar/phase02_dashboard.html", context)


@require_GET
def batch_positions(request: HttpRequest, batch_id: int) -> HttpResponse:
    batch = get_object_or_404(RecruitmentBatch, pk=batch_id)
    projection = None
    if batch.status == RecruitmentBatch.Status.ACTIVE:
        batch = get_object_or_404(RecruitmentBatch.objects.formal(), pk=batch_id)
        positions = batch.positions.filter(is_current=True)
    else:
        batch = get_object_or_404(RecruitmentBatch.objects.historical(), pk=batch_id)
        projection = trusted_historical_projection(batch)
        if projection is None:
            raise Http404
        positions = batch.positions.filter(pk__in=projection.position_ids)
    positions = positions.prefetch_related("application_links")
    position_vms = [
            _position_vm(
                position,
                batch_official_page_url=batch.official_page_url,
                include_historical_links=batch.status != RecruitmentBatch.Status.ACTIVE,
                allowed_link_ids=(set(projection.application_link_ids) if projection else None),
            )
            for position in positions
        ]
    position_vms = filter_position_vms(position_vms, request.GET)
    position_vms.sort(key=lambda item: item.effective_updated_on, reverse=True)
    return render(request, "radar/position_rows.html", {
        "positions": position_vms,
        "is_preview": False,
    })


@require_POST
def update_progress(request: HttpRequest, batch_id: int) -> JsonResponse:
    batch = get_object_or_404(RecruitmentBatch, pk=batch_id)
    if batch.status == RecruitmentBatch.Status.ACTIVE:
        visible = RecruitmentBatch.objects.formal().filter(pk=batch_id).exists()
    else:
        historical_batch = RecruitmentBatch.objects.historical().filter(pk=batch_id).first()
        visible = historical_batch is not None and trusted_historical_projection(historical_batch) is not None
    if not visible:
        raise Http404
    status = request.POST.get("status", "")
    valid = dict(ApplicationProgress.Status.choices)
    if status not in valid:
        return JsonResponse({"ok": False, "error": "投递状态无效。"}, status=400)
    progress, _ = ApplicationProgress.objects.update_or_create(
        batch=batch, defaults={"status": status}
    )
    return JsonResponse({"ok": True, "status": progress.status, "label": progress.get_status_display()})


@require_POST
@staff_member_required
def update_now(request: HttpRequest) -> HttpResponse:
    try:
        summary = run_update(trigger="manual")
    except Exception:
        messages.error(request, "手动更新异常，未能确认更新结果。")
        return redirect("dashboard")
    if summary.status == "failed":
        messages.error(request, "手动更新未执行：没有可成功完成的已启用核验来源。")
    else:
        messages.info(request, f"更新完成：检查 {summary.sources_checked} 个来源，新增 {summary.batches_created} 条。")
    return redirect("dashboard")
