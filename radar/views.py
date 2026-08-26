from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from radar.models import ApplicationProgress, Organization, RecruitmentBatch, RecruitmentPosition
from radar.services.dashboard_data import (
    _position_vm,
    available_city_choices,
    build_orm_dashboard,
    filter_position_vms,
    mock_dashboard,
)
from radar.services.evidence import trusted_historical_projection
from radar.services.update_runner import run_update
from radar.services.update_status import latest_source_failures, latest_successful_update, scheduled_run_is_missing
from radar.viewmodels import FILTER_FIELD_SPECS, MULTI_FILTER_LABELS, OPTIONAL_COLUMN_CHOICES


def _filter_fields(request: HttpRequest):
    choice_map = {
        "company_type": Organization.CompanyType.choices,
        "recruitment_type": RecruitmentBatch.RecruitmentType.choices,
    }
    return tuple(
        {
            "name": name,
            "label": label,
            "kind": kind,
            "placeholder": placeholder,
            "value": request.GET.get(name, ""),
            "choices": choice_map.get(name, ()),
        }
        for name, label, kind, placeholder in FILTER_FIELD_SPECS
    )

def _render_dashboard(request: HttpRequest, *, history: bool = False) -> HttpResponse:
    page, summary, city_choices = build_orm_dashboard(request.GET, history=history)
    preserved_query = request.GET.copy()
    preserved_query.pop("page", None)
    return render(request, "radar/phase02_dashboard.html", {
        "page": page,
        "batches": page.object_list,
        "summary": summary,
        "history": history,
        "is_preview": False,
        "progress_choices": ApplicationProgress.Status.choices,
        "company_type_choices": Organization.CompanyType.choices,
        "recruitment_type_choices": RecruitmentBatch.RecruitmentType.choices,
        "city_choices": tuple(dict.fromkeys((*city_choices, *request.GET.getlist("city")))),
        "selected_cities": request.GET.getlist("city"),
        "selected_progress": request.GET.getlist("progress"),
        "scheduled_run_missing": scheduled_run_is_missing(timezone.now()),
        "last_successful_update": latest_successful_update(),
        "source_failures": latest_source_failures(),
        "query_without_page": preserved_query.urlencode(),
        "current_query": request.GET.urlencode(),
        "optional_columns": OPTIONAL_COLUMN_CHOICES,
        "filter_fields": _filter_fields(request),
        "multi_filter_labels": dict(MULTI_FILTER_LABELS),
    })


def dashboard(request: HttpRequest) -> HttpResponse:
    return _render_dashboard(request)


def history(request: HttpRequest) -> HttpResponse:
    return _render_dashboard(request, history=True)


def phase02_preview(request: HttpRequest) -> HttpResponse:
    if not settings.DEBUG:
        raise Http404
    history = request.GET.get("view") == "history"
    batches, summary = mock_dashboard(request.GET, history=history)
    return render(request, "radar/phase02_dashboard.html", {
        "batches": batches,
        "summary": summary,
        "history": history,
        "is_preview": True,
        "progress_choices": ApplicationProgress.Status.choices,
        "company_type_choices": Organization.CompanyType.choices,
        "recruitment_type_choices": RecruitmentBatch.RecruitmentType.choices,
        "city_choices": tuple(dict.fromkeys((*available_city_choices(batches), *request.GET.getlist("city")))),
        "selected_cities": request.GET.getlist("city"),
        "selected_progress": request.GET.getlist("progress"),
        "preview_health": request.GET.get("health", "normal"),
        "scheduled_run_missing": False,
        "source_failures": (),
        "optional_columns": OPTIONAL_COLUMN_CHOICES,
        "filter_fields": _filter_fields(request),
        "multi_filter_labels": dict(MULTI_FILTER_LABELS),
    })


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
    positions = positions.prefetch_related("application_progress", "application_links")
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
        "progress_choices": ApplicationProgress.Status.choices,
        "is_preview": False,
    })


@require_POST
def update_progress(request: HttpRequest, position_id: int) -> JsonResponse:
    position = get_object_or_404(RecruitmentPosition, pk=position_id)
    if position.batch.status == RecruitmentBatch.Status.ACTIVE:
        visible = position.is_current and RecruitmentBatch.objects.formal().filter(pk=position.batch_id).exists()
    else:
        batch = RecruitmentBatch.objects.historical().filter(pk=position.batch_id).first()
        projection = trusted_historical_projection(batch) if batch else None
        visible = projection is not None and position.pk in projection.position_ids
    if not visible:
        raise Http404
    status = request.POST.get("status", "")
    valid = dict(ApplicationProgress.Status.choices)
    if status not in valid:
        return JsonResponse({"ok": False, "error": "投递状态无效。"}, status=400)
    progress, _ = ApplicationProgress.objects.update_or_create(
        position=position, defaults={"status": status}
    )
    return JsonResponse({"ok": True, "status": progress.status, "label": progress.get_status_display()})


@require_POST
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
