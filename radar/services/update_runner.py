from dataclasses import dataclass
from datetime import datetime
import re
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from radar.collectors.base import FetchedPage, RecruitmentBatchCandidate
from radar.collectors.registry import AdapterRegistry
from radar.models import (
    FetchRun,
    OfficialSource,
    PublicationEvent,
    RecruitmentBatch,
    RecruitmentPosition,
    SourceVersion,
    UpdateRun,
)
from radar.services.admission import source_is_admitted
from radar.services.publication import PublicationResult, publish_candidates


@dataclass(frozen=True)
class UpdateSummary:
    update_run_id: int
    sources_checked: int
    sources_failed: int
    batches_created: int
    batches_updated: int
    batches_rejected: int
    status: str = "failed"
    error_message: str = ""


def sanitize_error(error: Exception) -> str:
    message = " ".join(str(error).split())

    def safe_url(match):
        parts = urlsplit(match.group(0))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    message = re.sub(r"https?://[^\s]+", safe_url, message)
    message = re.sub(r"\b[A-Za-z]:\\+(?:[^\\\s]+\\+)*[^\\\s]+", "[local-path]", message)
    message = re.sub(
        r"(?i)\b(token|cookie|authorization|password|secret)=\S+",
        r"\1=[redacted]",
        message,
    )
    message = re.sub(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b", "[email]", message)
    message = message[:300]
    return f"{type(error).__name__}: {message}" if message else type(error).__name__


@transaction.atomic
def _apply_source_page(
    *,
    update_run: UpdateRun,
    source: OfficialSource,
    page: FetchedPage,
    candidates: list[RecruitmentBatchCandidate],
    local_date,
    reprocess_rejected: bool = False,
) -> list[PublicationResult]:
    source = OfficialSource.objects.select_for_update().get(pk=source.pk)
    latest_applied = (
        SourceVersion.objects.filter(source=source, is_applied=True)
        .order_by("-applied_at", "-pk")
        .first()
    )
    if page.not_modified:
        FetchRun.objects.create(
            update_run=update_run,
            source=source,
            status=FetchRun.Status.NOT_MODIFIED,
            http_status=page.http_status,
        )
        results: list[PublicationResult] = []
    elif (
        latest_applied is not None
        and latest_applied.content_hash == page.content_hash
        and not (
            reprocess_rejected
            and latest_applied.publication_events.exists()
            and not latest_applied.publication_events.exclude(
                event_type__in={
                    PublicationEvent.EventType.REJECTED,
                    PublicationEvent.EventType.AMBIGUOUS,
                    PublicationEvent.EventType.OUT_OF_SCOPE,
                }
            ).exists()
        )
    ):
        FetchRun.objects.create(
            update_run=update_run,
            source=source,
            status=FetchRun.Status.UNCHANGED,
            http_status=page.http_status,
        )
        results = []
    else:
        fetch_run = FetchRun.objects.create(
            update_run=update_run,
            source=source,
            status=FetchRun.Status.RUNNING,
            http_status=page.http_status,
        )
        version = SourceVersion.objects.create(
            source=source,
            fetch_run=fetch_run,
            canonical_url=page.canonical_url,
            content_hash=page.content_hash,
            etag=page.etag or "",
            is_applied=False,
        )
        results = publish_candidates(source, candidates, version)
        applied_at = timezone.now()
        version.is_applied = True
        version.applied_at = applied_at
        version.save(update_fields=["is_applied", "applied_at"])
        fetch_run.status = FetchRun.Status.SUCCESS
        fetch_run.save(update_fields=["status"])
    expiring = RecruitmentBatch.objects.filter(
        source=source,
        status=RecruitmentBatch.Status.ACTIVE,
        deadline__lt=local_date,
    )
    expiring_ids = list(expiring.values_list("pk", flat=True))
    if expiring_ids:
        expired_at = timezone.now()
        RecruitmentPosition.objects.filter(
            batch_id__in=expiring_ids, is_current=True
        ).update(content_changed_at=expired_at)
        expiring.update(status=RecruitmentBatch.Status.EXPIRED)
    source.last_checked_at = timezone.now()
    source.last_etag = page.etag or source.last_etag
    source.last_error = ""
    source.save(update_fields=["last_checked_at", "last_etag", "last_error"])
    return results


def _record_source_failure(
    *, update_run: UpdateRun, source: OfficialSource, error: Exception
) -> None:
    safe_error = sanitize_error(error)
    with transaction.atomic():
        locked_source = OfficialSource.objects.select_for_update().get(pk=source.pk)
        FetchRun.objects.create(
            update_run=update_run,
            source=locked_source,
            status=FetchRun.Status.FAILED,
            error_message=safe_error,
        )
        locked_source.last_checked_at = timezone.now()
        locked_source.last_error = safe_error
        locked_source.save(update_fields=["last_checked_at", "last_error"])


def run_update(
    *,
    trigger: str,
    now: datetime | None = None,
    source_ids: Iterable[int] | None = None,
    reprocess_rejected: bool = False,
) -> UpdateSummary:
    requested_source_ids = tuple(source_ids) if source_ids is not None else None
    if reprocess_rejected and trigger != UpdateRun.Trigger.MANUAL:
        raise ValueError("rejected versions can only be reprocessed manually")
    if reprocess_rejected and not requested_source_ids:
        raise ValueError("reprocessing rejected versions requires source IDs")
    current = now or timezone.now()
    local_date = current.astimezone(ZoneInfo("Asia/Shanghai")).date()
    update_run = UpdateRun.objects.create(
        trigger=trigger,
        scheduled_for_date=(
            local_date if trigger == UpdateRun.Trigger.SCHEDULED else None
        ),
    )
    sources = list(
        OfficialSource.objects.filter(
            admission_state=OfficialSource.AdmissionState.ENABLED
        ).select_related("organization")
    )
    sources = [source for source in sources if source_is_admitted(source)]
    if requested_source_ids is not None:
        allowed_ids = set(requested_source_ids)
        sources = [source for source in sources if source.pk in allowed_ids]
    demo_keys = {source.local_demo_key for source in sources}
    if len(demo_keys) == 1 and "" not in demo_keys:
        update_run.local_demo_key = demo_keys.pop()
        update_run.save(update_fields=["local_demo_key"])

    checked = failed = created = updated = rejected = 0
    successful_source_ids: set[int] = set()
    for source in sources:
        checked += 1
        try:
            adapter = AdapterRegistry.get(source)
            page = adapter.fetch(source)
            candidates = [] if page.not_modified else list(adapter.extract(source, page))
            results = _apply_source_page(
                update_run=update_run,
                source=source,
                page=page,
                candidates=candidates,
                local_date=local_date,
                reprocess_rejected=reprocess_rejected,
            )
        except Exception as error:
            failed += 1
            _record_source_failure(update_run=update_run, source=source, error=error)
            continue
        successful_source_ids.add(source.pk)
        created += sum(result.action == "created" for result in results)
        updated += sum(result.action == "updated" for result in results)
        rejected += sum(result.action == "rejected" for result in results)

    update_run.status = (
        UpdateRun.Status.FAILED
        if not successful_source_ids
        else UpdateRun.Status.PARTIAL_FAILURE
        if failed or rejected
        else UpdateRun.Status.SUCCESS
    )
    if not sources:
        update_run.error_message = "no active admitted source"
    elif not successful_source_ids:
        update_run.error_message = "all checked sources failed"
    elif failed or rejected:
        parts = []
        if failed:
            parts.append(f"sources_failed={failed}")
        if rejected:
            parts.append(f"batches_rejected={rejected}")
        update_run.error_message = "partial update: " + " ".join(parts)
    update_run.completed_at = timezone.now()
    update_run.save(update_fields=["status", "completed_at", "error_message"])
    return UpdateSummary(
        update_run.pk,
        checked,
        failed,
        created,
        updated,
        rejected,
        update_run.status,
        update_run.error_message,
    )
