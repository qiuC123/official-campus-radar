import hashlib
from dataclasses import dataclass, replace
from typing import Iterable, Literal

from django.db import transaction
from django.utils import timezone

from radar.collectors.base import FieldEvidenceValue, NoticeCandidate
from radar.models import (
    ApplicationLink,
    Evidence,
    NoticePosition,
    OfficialSource,
    PublicationEvent,
    RecruitmentNotice,
    SourceVersion,
)
from radar.services.admission import (
    source_is_admitted,
    source_permits_application_url,
    source_permits_notice_url,
)
from radar.services.evidence import (
    candidate_evidence_is_valid,
    normalize_evidence_value,
)
from radar.services.locations import normalized_target_locations
from radar.services.normalization import canonicalize_url


@dataclass(frozen=True)
class PublicationResult:
    action: Literal["created", "updated", "rejected", "unchanged"]
    notice_id: int | None
    reasons: tuple[str, ...]


NOTICE_EVIDENCE_FIELDS = {
    "title",
    "recruitment_type",
    "target_audience",
    "published_on",
    "deadline",
    "notice_url",
}
POSITION_EVIDENCE_FIELDS = {"position_title", "location"}
OPTIONAL_POSITION_EVIDENCE_FIELDS = {"raw_text"}


def classify_recruitment(value: str) -> str:
    normalized = (value or "").strip().casefold()
    if any(term in normalized for term in ("招商", "招标", "招聘会", "采购")):
        return RecruitmentNotice.RecruitmentType.OTHER
    if normalized in {
        RecruitmentNotice.RecruitmentType.CAMPUS_RECRUITMENT,
        RecruitmentNotice.RecruitmentType.INTERNSHIP,
    }:
        return normalized
    if any(term in normalized for term in ("实习", "intern")):
        return RecruitmentNotice.RecruitmentType.INTERNSHIP
    if any(
        term in normalized
        for term in ("校园招聘", "校招", "应届生", "graduate program")
    ):
        return RecruitmentNotice.RecruitmentType.CAMPUS_RECRUITMENT
    if any(term in normalized for term in ("社会招聘", "社招", "招聘")):
        return RecruitmentNotice.RecruitmentType.OTHER
    return RecruitmentNotice.RecruitmentType.UNKNOWN


def _candidate_conflict_indexes(candidates: list[NoticeCandidate]) -> set[int]:
    by_identity: dict[str, list[int]] = {}
    by_url: dict[str, list[int]] = {}
    for index, candidate in enumerate(candidates):
        identity_key = candidate.identity_key.strip()
        if identity_key:
            by_identity.setdefault(identity_key, []).append(index)
        if candidate.official_notice_url:
            by_url.setdefault(
                canonicalize_url(candidate.official_notice_url), []
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


def _event(
    *,
    version: SourceVersion,
    candidate: NoticeCandidate,
    event_type: str,
    notice: RecruitmentNotice | None = None,
    reasons: Iterable[str] = (),
    evidence_complete: bool = False,
) -> PublicationEvent:
    return PublicationEvent.objects.create(
        source_version=version,
        notice=notice,
        event_type=event_type,
        identity_key=candidate.identity_key,
        candidate_title=candidate.title,
        reason_codes=list(reasons),
        evidence_complete=evidence_complete,
    )


def _has_complete_evidence(
    candidate: NoticeCandidate, positions, recruitment_type: str
) -> bool:
    return candidate_evidence_is_valid(candidate, positions, recruitment_type)


def _write_evidence(
    *,
    notice: RecruitmentNotice,
    version: SourceVersion,
    event: PublicationEvent,
    field_name: str,
    value: FieldEvidenceValue,
    position: NoticePosition | None = None,
    application_link: ApplicationLink | None = None,
) -> None:
    parsed = normalize_evidence_value(field_name, value.parsed_value)
    excerpt = value.raw_value if value.excerpt is None else value.excerpt
    Evidence.objects.create(
        notice=notice,
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
    candidate: NoticeCandidate,
    version: SourceVersion,
    reasons: list[str],
    *,
    ambiguous: bool = False,
    notice: RecruitmentNotice | None = None,
) -> PublicationResult:
    _event(
        version=version,
        candidate=candidate,
        event_type=(
            PublicationEvent.EventType.AMBIGUOUS
            if ambiguous
            else PublicationEvent.EventType.REJECTED
        ),
        notice=notice,
        reasons=reasons,
    )
    return PublicationResult("rejected", None, tuple(reasons))


def _publish_candidate(
    source: OfficialSource,
    candidate: NoticeCandidate,
    version: SourceVersion,
) -> PublicationResult:
    identity_key = candidate.identity_key.strip()
    notice_url = (
        canonicalize_url(candidate.official_notice_url)
        if candidate.official_notice_url
        else ""
    )
    existing_by_identity = (
        RecruitmentNotice.objects.filter(
            source=source, identity_key=identity_key
        ).first()
        if identity_key
        else None
    )
    existing_by_url = (
        RecruitmentNotice.objects.filter(
            source=source, official_notice_url=notice_url
        ).first()
        if notice_url
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
            notice=existing_by_identity or existing_by_url,
        )
    existing_notice = existing_by_identity
    target_positions = [
        position
        for position in candidate.positions
        if normalized_target_locations(position.location_text)
    ]
    lifecycle_identity_is_trusted = (
        existing_notice is not None
        and source_is_admitted(source)
        and bool(candidate.official_notice_url)
        and source_permits_notice_url(source, candidate.official_notice_url)
    )
    if lifecycle_identity_is_trusted and candidate.withdrawn:
        event = _event(
            version=version,
            candidate=candidate,
            event_type=PublicationEvent.EventType.WITHDRAWN,
            notice=existing_notice,
            reasons=("explicit_source_withdrawal",),
        )
        existing_notice.status = RecruitmentNotice.Status.WITHDRAWN
        existing_notice.latest_publication_event = event
        existing_notice.last_verified_at = timezone.now()
        existing_notice.save(
            update_fields=["status", "latest_publication_event", "last_verified_at"]
        )
        NoticePosition.objects.filter(
            notice=existing_notice, is_current=True
        ).update(is_current=False, removed_at=timezone.now())
        ApplicationLink.objects.filter(
            notice=existing_notice, is_current=True
        ).update(is_current=False, removed_at=timezone.now())
        return PublicationResult("updated", existing_notice.pk, ())
    if lifecycle_identity_is_trusted and not candidate.positions_complete:
        return _reject(
            source,
            candidate,
            version,
            ["incomplete_position_coverage"],
            notice=existing_notice,
        )
    if (
        lifecycle_identity_is_trusted
        and candidate.positions_complete
        and not target_positions
    ):
        event = _event(
            version=version,
            candidate=candidate,
            event_type=PublicationEvent.EventType.OUT_OF_SCOPE,
            notice=existing_notice,
            reasons=("complete_position_coverage_has_no_target_position",),
        )
        NoticePosition.objects.filter(
            notice=existing_notice, is_current=True
        ).update(is_current=False, removed_at=timezone.now())
        ApplicationLink.objects.filter(
            notice=existing_notice, is_current=True
        ).update(is_current=False, removed_at=timezone.now())
        existing_notice.latest_publication_event = event
        existing_notice.last_verified_at = timezone.now()
        existing_notice.save(
            update_fields=["latest_publication_event", "last_verified_at"]
        )
        return PublicationResult("updated", existing_notice.pk, ())

    reasons: list[str] = []
    if not candidate.identity_key.strip():
        reasons.append("missing_stable_identity")
    if not source_is_admitted(source):
        reasons.append("source_not_admitted")
    if not candidate.official_notice_url or not source_permits_notice_url(
        source, candidate.official_notice_url
    ):
        reasons.append("missing_official_notice_url")
    classification_text = " ".join(
        [candidate.recruitment_type, candidate.title]
        + [position.title for position in candidate.positions]
        + [position.raw_text for position in candidate.positions]
    )
    recruitment_type = classify_recruitment(classification_text)
    if recruitment_type not in {
        RecruitmentNotice.RecruitmentType.CAMPUS_RECRUITMENT,
        RecruitmentNotice.RecruitmentType.INTERNSHIP,
    }:
        reasons.append("not_eligible_recruitment_type")
    if not target_positions:
        reasons.append("missing_target_location")
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

    notice = existing_notice
    created = notice is None
    if notice is None:
        notice = RecruitmentNotice.objects.create(
            organization=source.organization,
            source=source,
            identity_key=identity_key,
            title=candidate.title,
            official_notice_url=notice_url,
            recruitment_type=recruitment_type,
            target_audience=candidate.target_audience,
            published_on=candidate.published_on,
            deadline=candidate.deadline,
        )
    else:
        notice.title = candidate.title
        notice.official_notice_url = notice_url
        notice.recruitment_type = recruitment_type
        notice.target_audience = candidate.target_audience
        notice.published_on = candidate.published_on
        notice.deadline = candidate.deadline
        notice.status = RecruitmentNotice.Status.ACTIVE
        notice.last_verified_at = timezone.now()
        notice.save()
    event = _event(
        version=version,
        candidate=candidate,
        event_type=(
            PublicationEvent.EventType.PUBLISHED
            if created
            else PublicationEvent.EventType.UPDATED
        ),
        notice=notice,
        evidence_complete=True,
    )
    if candidate.positions_complete:
        NoticePosition.objects.filter(notice=notice, is_current=True).update(
            is_current=False, removed_at=timezone.now()
        )
        ApplicationLink.objects.filter(notice=notice, is_current=True).update(
            is_current=False, removed_at=timezone.now()
        )
    for field_name in NOTICE_EVIDENCE_FIELDS:
        _write_evidence(
            notice=notice,
            version=version,
            event=event,
            field_name=field_name,
            value=candidate.field_evidence[field_name],
        )
    for position_candidate in target_positions:
        position, _ = NoticePosition.objects.update_or_create(
            notice=notice,
            position_key=position_candidate.position_key,
            defaults={
                "title": position_candidate.title,
                "location_text": position_candidate.location_text,
                "normalized_locations": normalized_target_locations(
                    position_candidate.location_text
                ),
                "raw_text": position_candidate.raw_text,
                "is_current": True,
                "removed_at": None,
            },
        )
        for field_name in POSITION_EVIDENCE_FIELDS:
            _write_evidence(
                notice=notice,
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
                    notice=notice,
                    version=version,
                    event=event,
                    field_name=field_name,
                    value=value,
                    position=position,
                )
        if position_candidate.application_url:
            if not candidate.positions_complete:
                ApplicationLink.objects.filter(
                    notice=notice, position=position, is_current=True
                ).update(is_current=False, removed_at=timezone.now())
            link, _ = ApplicationLink.objects.update_or_create(
                notice=notice,
                position=position,
                url=position_candidate.application_url,
                link_type=ApplicationLink.LinkType.APPLICATION,
                defaults={"is_current": True, "removed_at": None},
            )
            _write_evidence(
                notice=notice,
                version=version,
                event=event,
                field_name="application_link",
                value=position_candidate.field_evidence["application_link"],
                position=position,
                application_link=link,
            )
    notice.latest_publication_event = event
    notice.save(update_fields=["latest_publication_event"])
    return PublicationResult("created" if created else "updated", notice.pk, ())


@transaction.atomic
def publish_candidates(
    source: OfficialSource,
    candidates: Iterable[NoticeCandidate],
    version: SourceVersion,
) -> list[PublicationResult]:
    candidate_list = [
        replace(
            candidate,
            identity_key=candidate.identity_key.strip(),
            official_notice_url=(
                canonicalize_url(candidate.official_notice_url)
                if candidate.official_notice_url
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
    candidate: NoticeCandidate,
    version: SourceVersion,
) -> PublicationResult:
    return publish_candidates(source, [candidate], version)[0]
