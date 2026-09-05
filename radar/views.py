from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from radar.models import ApplicationProgress, Organization, RecruitmentBatch
from radar.services.dashboard_data import (
    _position_vm,
    build_orm_dashboard,
    filter_position_vms,
    mock_dashboard,
)
from radar.services.evidence import trusted_historical_projection
from radar.services.announcements import announcement_direction_projection_is_complete
from radar.services.update_status import latest_source_failures, latest_successful_update, scheduled_run_is_missing
from radar.viewmodels import (
    AUDIENCE_CHOICES,
    MAX_SELECTED_PROVINCES,
    PREVIEW_COMPANY_TYPE_CHOICES,
    PREVIEW_RECRUITMENT_TYPE_CHOICES,
    PROVINCE_CHOICES,
    RECRUITMENT_TYPE_CHOICES,
)


def _filter_context(request: HttpRequest, *, preview: bool) -> dict:
    return {
        "company_value": request.GET.get("company", ""),
        "position_value": request.GET.get("position", ""),
        "company_type_choices": (
            PREVIEW_COMPANY_TYPE_CHOICES if preview else Organization.CompanyType.choices
        ),
        "recruitment_type_choices": (
            PREVIEW_RECRUITMENT_TYPE_CHOICES if preview else RECRUITMENT_TYPE_CHOICES
        ),
        "audience_choices": AUDIENCE_CHOICES,
        "selected_company_types": request.GET.getlist("company_type"),
        "selected_recruitment_types": request.GET.getlist("recruitment_type"),
        "selected_cities": request.GET.getlist("city")[:MAX_SELECTED_PROVINCES],
        "selected_progress": request.GET.getlist("progress"),
        "selected_audience": request.GET.get("audience", request.GET.get("target_audience", "")),
    }

def _render_dashboard(request: HttpRequest, *, history: bool = False) -> HttpResponse:
    show_progress = not settings.RADAR_PUBLIC_READONLY
    params = request.GET.copy()
    if not show_progress:
        params.pop("progress", None)
    request.GET = params
    page, summary, city_choices, available_audiences = build_orm_dashboard(
        params,
        history=history,
        include_progress=show_progress,
    )
    preserved_query = request.GET.copy()
    preserved_query.pop("page", None)
    pagination_query_fields = tuple(
        (key, value)
        for key, values in request.GET.lists()
        if key != "page"
        for value in values
    )
    context = {
        "page": page,
        "batches": page.object_list,
        "summary": summary,
        "history": history,
        "is_preview": False,
        "progress_choices": ApplicationProgress.Status.choices if show_progress else (),
        "show_progress": show_progress,
        "city_choices": tuple(dict.fromkeys((
            *city_choices,
            *request.GET.getlist("city")[:MAX_SELECTED_PROVINCES],
        ))),
        "scheduled_run_missing": scheduled_run_is_missing(timezone.now()) if show_progress else False,
        "last_successful_update": latest_successful_update() if show_progress else None,
        "source_failures": latest_source_failures() if show_progress else (),
        "query_without_page": preserved_query.urlencode(),
        "pagination_items": tuple(
            page.paginator.get_elided_page_range(
                page.number,
                on_each_side=2,
                on_ends=1,
            )
        ),
        "pagination_query_fields": pagination_query_fields,
        "current_query": request.GET.urlencode(),
        "show_operations": show_progress and request.user.is_staff,
    }
    context.update(_filter_context(request, preview=False))
    standard_audiences = [value for value, _label in AUDIENCE_CHOICES]
    selected_audience = context["selected_audience"]
    visible_audiences = set(available_audiences)
    if selected_audience in standard_audiences:
        visible_audiences.add(selected_audience)
    context["audience_choices"] = tuple(
        (value, value) for value in standard_audiences if value in visible_audiences
    )
    return render(request, "radar/phase02_dashboard.html", context)


@ensure_csrf_cookie
def dashboard(request: HttpRequest) -> HttpResponse:
    return _render_dashboard(request)


@ensure_csrf_cookie
def history(request: HttpRequest) -> HttpResponse:
    return _render_dashboard(request, history=True)


@ensure_csrf_cookie
def application_progress_list(request: HttpRequest) -> HttpResponse:
    if settings.RADAR_PUBLIC_READONLY:
        raise Http404
    progress_rows = list(
        ApplicationProgress.objects.select_related("batch__organization").order_by(
            "batch__organization__name", "batch__title"
        )
    )
    return render(request, "radar/application_progress.html", {
        "progress_rows": progress_rows,
        "progress_choices": ApplicationProgress.Status.choices,
    })


def phase02_preview(request: HttpRequest) -> HttpResponse:
    if not settings.DEBUG or settings.RADAR_PUBLIC_READONLY:
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
        "show_progress": True,
    }
    context.update(_filter_context(request, preview=True))
    return render(request, "radar/phase02_dashboard.html", context)


@require_GET
def batch_positions(request: HttpRequest, batch_id: int) -> HttpResponse:
    batch = get_object_or_404(RecruitmentBatch, pk=batch_id)
    projection = None
    if batch.status == RecruitmentBatch.Status.ACTIVE:
        batch = get_object_or_404(
            RecruitmentBatch.objects.filter(pk=batch_id).formal()
        )
        positions = batch.positions.filter(is_current=True)
    else:
        batch = get_object_or_404(RecruitmentBatch.objects.historical(), pk=batch_id)
        projection = trusted_historical_projection(batch)
        if projection is not None:
            positions = batch.positions.filter(pk__in=projection.position_ids)
        elif announcement_direction_projection_is_complete(batch, current_only=False):
            positions = batch.positions.filter(kind="direction")
        else:
            raise Http404
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
    if settings.RADAR_PUBLIC_READONLY:
        raise Http404
    batch = get_object_or_404(RecruitmentBatch, pk=batch_id)
    existing_progress = ApplicationProgress.objects.filter(batch=batch).exists()
    if batch.status == RecruitmentBatch.Status.ACTIVE:
        visible = RecruitmentBatch.objects.filter(pk=batch_id).formal().exists()
    else:
        historical_batch = RecruitmentBatch.objects.historical().filter(pk=batch_id).first()
        visible = historical_batch is not None and trusted_historical_projection(historical_batch) is not None
    if not visible and not existing_progress:
        raise Http404
    status = request.POST.get("status", "")
    valid = dict(ApplicationProgress.Status.choices)
    if status not in valid:
        return JsonResponse({"ok": False, "error": "投递状态无效。"}, status=400)
    progress, _ = ApplicationProgress.objects.update_or_create(
        batch=batch, defaults={"status": status}
    )
    return JsonResponse({"ok": True, "status": progress.status, "label": progress.get_status_display()})
