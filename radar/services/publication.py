import hashlib
from dataclasses import dataclass, replace
from typing import Iterable, Literal

from django.db import transaction
from django.utils import timezone

from radar.collectors.base import FieldEvidenceValue, RecruitmentBatchCandidate
from radar.models import (
    ApplicationLink,
    Evidence,
    RecruitmentPosition,
    OfficialSource,
    PublicationEvent,
    RecruitmentBatch,
    SourceVersion,
)
from radar.services.admission import (
    source_is_admitted,
    source_permits_application_url,
    source_permits_batch_url,
)
from radar.services.evidence import (
    candidate_evidence_is_valid,
    normalize_evidence_value,
)
from radar.services.locations import normalized_target_locations
from radar.services.normalization import canonicalize_url
from radar.services.recruitment import classify_recruitment


@dataclass(frozen=True)
class PublicationResult:
    action: Literal["created", "updated", "rejected", "unchanged"]
    batch_id: int | None
    reasons: tuple[str, ...]


BATCH_EVIDENCE_FIELDS = {
    "title",
    "recruitment_type",
    "target_audience",
    "published_on",
    "deadline",
    "official_page_url",
}
POSITION_EVIDENCE_FIELDS = {"position_title", "location"}
OPTIONAL_POSITION_EVIDENCE_FIELDS = {"raw_text", "source_updated_on"}


def _candidate_conflict_indexes(candidates: list[RecruitmentBatchCandidate]) -> set[int]:
    by_identity: dict[str, list[int]] = {}
    by_url: dict[str, list[int]] = {}
    for index, candidate in enumerate(candidates):
        identity_key = candidate.identity_key.strip()
        if identity_key:
            by_identity.setdefault(identity_key, []).append(index)
        if candidate.official_page_url:
            by_url.setdefault(
                canonicalize_url(candidate.official_page_url), []
            ).append(index)
    conflicts: set[int] = set()
    for indexes in by_identity.values():
        if len(indexes) > 1:
            conflicts.update(indexes)
    for indexes in by_url.values():
        identities = {candidates[index].identity_key for index in indexes}
        if len(identities) > 1:
            conflicts.update(indexes)
    return conflicts


def _drop_unproven_position_details(position):
    if not position.raw_text:
        return position
    evidence = position.field_evidence.get("raw_text")
    if (
        evidence is not None
        and str(evidence.raw_value or "").strip()
        and str(evidence.locator or "").strip()
        and normalize_evidence_value("raw_text", evidence.parsed_value)
        == normalize_evidence_value("raw_text", position.raw_text)
    ):
        return position
    return replace(position, raw_text="")


def _event(
    *,
    version: SourceVersion,
    candidate: RecruitmentBatchCandidate,
    event_type: str,
    batch: RecruitmentBatch | None = None,
    reasons: Iterable[str] = (),
    evidence_complete: bool = False,
) -> PublicationEvent:
    return PublicationEvent.objects.create(
        source_version=version,
        batch=batch,
        event_type=event_type,
        identity_key=candidate.identity_key,
        candidate_title=candidate.title,
        reason_codes=list(reasons),
        evidence_complete=evidence_complete,
    )


def _has_complete_evidence(
    candidate: RecruitmentBatchCandidate, positions, recruitment_type: str
) -> bool:
    return candidate_evidence_is_valid(candidate, positions, recruitment_type)


def _write_evidence(
    *,
    batch: RecruitmentBatch,
    version: SourceVersion,
    event: PublicationEvent,
    field_name: str,
    value: FieldEvidenceValue,
    position: RecruitmentPosition | None = None,
    application_link: ApplicationLink | None = None,
) -> None:
    parsed = normalize_evidence_value(field_name, value.parsed_value)
    excerpt = value.raw_value if value.excerpt is None else value.excerpt
    Evidence.objects.create(
        batch=batch,
        source_version=version,
        publication_event=event,
        position=position,
        application_link=application_link,
        field_name=field_name,
        excerpt=excerpt[:1000],
        locator=value.locator,
        raw_value=value.raw_value,
        parsed_value=parsed,
        value_hash=hashlib.sha256(parsed.encode("utf-8")).hexdigest(),
    )


def _reject(
    source: OfficialSource,
    candidate: RecruitmentBatchCandidate,
    version: SourceVersion,
    reasons: list[str],
    *,
    ambiguous: bool = False,
    batch: RecruitmentBatch | None = None,
) -> PublicationResult:
    _event(
        version=version,
        candidate=candidate,
        event_type=(
            PublicationEvent.EventType.AMBIGUOUS
            if ambiguous
            else PublicationEvent.EventType.REJECTED
        ),
        batch=batch,
        reasons=reasons,
    )
    return PublicationResult("rejected", None, tuple(reasons))


def _publish_candidate(
    source: OfficialSource,
    candidate: RecruitmentBatchCandidate,
    version: SourceVersion,
) -> PublicationResult:
    identity_key = candidate.identity_key.strip()
    official_page_url = (
        canonicalize_url(candidate.official_page_url)
        if candidate.official_page_url
        else ""
    )
    existing_by_identity = (
        RecruitmentBatch.objects.filter(
            source=source, identity_key=identity_key
        ).first()
        if identity_key
        else None
    )
    existing_by_url = (
        RecruitmentBatch.objects.filter(
            source=source, official_page_url=official_page_url
        ).first()
        if official_page_url
        else None
    )
    if existing_by_url is not None and (
        existing_by_identity is None
        or existing_by_url.pk != existing_by_identity.pk
    ):
        return _reject(
            source,
            candidate,
            version,
            ["ambiguous_identity"],
            ambiguous=True,
            batch=existing_by_identity or existing_by_url,
        )
    existing_batch = existing_by_identity
    target_positions = [
        _drop_unproven_position_details(position)
        for position in candidate.positions
    ]
    lifecycle_identity_is_trusted = (
        existing_batch is not None
        and source_is_admitted(source)
        and bool(candidate.official_page_url)
        and source_permits_batch_url(source, candidate.official_page_url)
    )
    if lifecycle_identity_is_trusted and candidate.withdrawn:
        withdrawn_at = timezone.now()
        event = _event(
            version=version,
            candidate=candidate,
            event_type=PublicationEvent.EventType.WITHDRAWN,
            batch=existing_batch,
            reasons=("explicit_source_withdrawal",),
        )
        existing_batch.status = RecruitmentBatch.Status.WITHDRAWN
        existing_batch.latest_publication_event = event
        existing_batch.last_verified_at = withdrawn_at
        existing_batch.save(
            update_fields=["status", "latest_publication_event", "last_verified_at"]
        )
        RecruitmentPosition.objects.filter(
            batch=existing_batch, is_current=True
        ).update(
            is_current=False,
            removed_at=withdrawn_at,
            content_changed_at=withdrawn_at,
        )
        ApplicationLink.objects.filter(
            batch=existing_batch, is_current=True
        ).update(is_current=False, removed_at=withdrawn_at)
        return PublicationResult("updated", existing_batch.pk, ())
    if lifecycle_identity_is_trusted and not candidate.positions_complete:
        return _reject(
            source,
            candidate,
            version,
            ["incomplete_position_coverage"],
            batch=existing_batch,
        )
    if source.adapter_name == "json_api" and not candidate.positions_complete:
        return _reject(
            source,
            candidate,
            version,
            ["incomplete_position_coverage"],
        )
    reasons: list[str] = []
    if not candidate.identity_key.strip():
        reasons.append("missing_stable_identity")
    if not source_is_admitted(source):
        reasons.append("source_not_admitted")
    if not candidate.official_page_url or not source_permits_batch_url(
        source, candidate.official_page_url
    ):
        reasons.append("missing_official_page_url")
    declared_recruitment_type = classify_recruitment(candidate.recruitment_type)
    declared_type_is_authoritative = source.adapter_name in {
        "json_api",
        "ats_json_api",
        "moka_public_api",
    }
    if declared_type_is_authoritative and declared_recruitment_type in {
        RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT,
        RecruitmentBatch.RecruitmentType.INTERNSHIP,
    }:
        recruitment_type = declared_recruitment_type
    else:
        classification_text = " ".join(
            [candidate.recruitment_type, candidate.title]
            + [position.title for position in target_positions]
            + [position.raw_text for position in target_positions]
        )
        recruitment_type = classify_recruitment(classification_text)
    if recruitment_type not in {
        RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT,
        RecruitmentBatch.RecruitmentType.INTERNSHIP,
    }:
        reasons.append("not_eligible_recruitment_type")
    if not target_positions:
        reasons.append("missing_positions")
    if any(not position.position_key.strip() for position in target_positions):
        reasons.append("missing_stable_position_identity")
    if len({position.position_key for position in target_positions}) != len(
        target_positions
    ):
        reasons.append("conflicting_position_identity")
    if any(
        position.application_url
        and not source_permits_application_url(source, position.application_url)
        for position in target_positions
    ):
        reasons.append("untrusted_application_url")
    if not _has_complete_evidence(candidate, target_positions, recruitment_type):
        reasons.append("incomplete_field_evidence")
    if reasons:
        return _reject(source, candidate, version, reasons)

    batch = existing_batch
    created = batch is None
    batch_content_changed = False
    content_change_time = timezone.now()
    if batch is None:
        batch = RecruitmentBatch.objects.create(
            organization=source.organization,
            source=source,
            identity_key=identity_key,
            title=candidate.title,
            official_page_url=official_page_url,
            recruitment_type=recruitment_type,
            target_audience=candidate.target_audience,
            published_on=candidate.published_on,
            deadline=candidate.deadline,
        )
    else:
        batch_content_changed = any((
            batch.title != candidate.title,
            batch.official_page_url != official_page_url,
            batch.recruitment_type != recruitment_type,
            batch.target_audience != candidate.target_audience,
            batch.published_on != candidate.published_on,
            batch.deadline != candidate.deadline,
            batch.status != RecruitmentBatch.Status.ACTIVE,
        ))
        batch.title = candidate.title
        batch.official_page_url = official_page_url
        batch.recruitment_type = recruitment_type
        batch.target_audience = candidate.target_audience
        batch.published_on = candidate.published_on
        batch.deadline = candidate.deadline
        batch.status = RecruitmentBatch.Status.ACTIVE
        batch.last_verified_at = timezone.now()
        batch.save()
    event = _event(
        version=version,
        candidate=candidate,
        event_type=(
            PublicationEvent.EventType.PUBLISHED
            if created
            else PublicationEvent.EventType.UPDATED
        ),
        batch=batch,
        evidence_complete=True,
    )
    for field_name in BATCH_EVIDENCE_FIELDS:
        _write_evidence(
            batch=batch,
            version=version,
            event=event,
            field_name=field_name,
            value=candidate.field_evidence[field_name],
        )
    current_position_keys: set[str] = set()
    current_link_ids: set[int] = set()
    for position_candidate in target_positions:
        current_position_keys.add(position_candidate.position_key)
        previous_application_url = (
            ApplicationLink.objects.filter(
                batch=batch,
                position__position_key=position_candidate.position_key,
                link_type=ApplicationLink.LinkType.APPLICATION,
                is_current=True,
            )
            .values_list("url", flat=True)
            .first()
        )
        position, position_created = RecruitmentPosition.objects.get_or_create(
            batch=batch,
            position_key=position_candidate.position_key,
            defaults={
                "title": position_candidate.title,
                "location_text": position_candidate.location_text,
                "normalized_locations": normalized_target_locations(
                    position_candidate.location_text
                ),
                "raw_text": position_candidate.raw_text,
                "source_updated_on": position_candidate.source_updated_on,
                "is_current": True,
                "removed_at": None,
            },
        )
        if not position_created:
            new_values = {
                "title": position_candidate.title,
                "location_text": position_candidate.location_text,
                "normalized_locations": normalized_target_locations(
                    position_candidate.location_text
                ),
                "raw_text": position_candidate.raw_text,
                "source_updated_on": position_candidate.source_updated_on,
                "is_current": True,
                "removed_at": None,
            }
            changed = batch_content_changed or (
                any(getattr(position, key) != value for key, value in new_values.items())
                or previous_application_url != position_candidate.application_url
            )
            for key, value in new_values.items():
                setattr(position, key, value)
            update_fields = list(new_values)
            if changed:
                position.content_changed_at = content_change_time
                update_fields.append("content_changed_at")
            position.save(update_fields=update_fields)
        for field_name in POSITION_EVIDENCE_FIELDS:
            _write_evidence(
                batch=batch,
                version=version,
                event=event,
                field_name=field_name,
                value=position_candidate.field_evidence[field_name],
                position=position,
            )
        for field_name in OPTIONAL_POSITION_EVIDENCE_FIELDS:
            value = position_candidate.field_evidence.get(field_name)
            if value is not None:
                _write_evidence(
                    batch=batch,
                    version=version,
                    event=event,
                    field_name=field_name,
                    value=value,
                    position=position,
                )
        if position_candidate.application_url:
            if not candidate.positions_complete:
                ApplicationLink.objects.filter(
                    batch=batch, position=position, is_current=True
                ).update(is_current=False, removed_at=timezone.now())
            link, _ = ApplicationLink.objects.update_or_create(
                batch=batch,
                position=position,
                url=position_candidate.application_url,
                link_type=ApplicationLink.LinkType.APPLICATION,
                defaults={"is_current": True, "removed_at": None},
            )
            current_link_ids.add(link.pk)
            _write_evidence(
                batch=batch,
                version=version,
                event=event,
                field_name="application_link",
                value=position_candidate.field_evidence["application_link"],
                position=position,
                application_link=link,
            )
    if candidate.positions_complete:
        retired_at = timezone.now()
        RecruitmentPosition.objects.filter(
            batch=batch, is_current=True
        ).exclude(position_key__in=current_position_keys).update(
            is_current=False,
            removed_at=retired_at,
            content_changed_at=retired_at,
        )
        ApplicationLink.objects.filter(
            batch=batch,
            is_current=True,
            link_type=ApplicationLink.LinkType.APPLICATION,
        ).exclude(pk__in=current_link_ids).update(
            is_current=False,
            removed_at=retired_at,
        )
    if batch_content_changed:
        RecruitmentPosition.objects.filter(
            batch=batch, is_current=True
        ).exclude(position_key__in=current_position_keys).update(
            content_changed_at=content_change_time
        )
    batch.latest_publication_event = event
    batch.save(update_fields=["latest_publication_event"])
    return PublicationResult("created" if created else "updated", batch.pk, ())


@transaction.atomic
def publish_candidates(
    source: OfficialSource,
    candidates: Iterable[RecruitmentBatchCandidate],
    version: SourceVersion,
) -> list[PublicationResult]:
    candidate_list = [
        replace(
            candidate,
            identity_key=candidate.identity_key.strip(),
            official_page_url=(
                canonicalize_url(candidate.official_page_url)
                if candidate.official_page_url
                else ""
            ),
        )
        for candidate in candidates
    ]
    conflicts = _candidate_conflict_indexes(candidate_list)
    results: list[PublicationResult] = []
    for index, candidate in enumerate(candidate_list):
        if index in conflicts:
            results.append(
                _reject(
                    source,
                    candidate,
                    version,
                    ["ambiguous_identity"],
                    ambiguous=True,
                )
            )
        else:
            results.append(_publish_candidate(source, candidate, version))
    return results


def publish_candidate(
    source: OfficialSource,
    candidate: RecruitmentBatchCandidate,
    version: SourceVersion,
) -> PublicationResult:
    return publish_candidates(source, [candidate], version)[0]
