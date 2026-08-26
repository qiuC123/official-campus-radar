import hashlib
import re
import unicodedata
from dataclasses import dataclass

from radar.services.normalization import canonicalize_url
from radar.collectors.base import EXPLICIT_MISSING


URL_FIELDS = {"official_page_url", "application_link"}
NULLABLE_EVIDENCE_FIELDS = {"published_on", "deadline"}


@dataclass(frozen=True)
class TrustedHistoricalProjection:
    publication_event_id: int
    position_ids: tuple[int, ...]
    application_link_ids: tuple[int, ...]


def normalize_evidence_value(field_name: str, value) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat") and field_name in {
        "published_on", "deadline", "source_updated_on"
    }:
        return value.isoformat()
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    if field_name in URL_FIELDS and text:
        return canonicalize_url(text)
    return text


def field_evidence_matches(field_name: str, evidence, actual_value) -> bool:
    expected = normalize_evidence_value(field_name, actual_value)
    parsed = normalize_evidence_value(field_name, evidence.parsed_value)
    raw = str(evidence.raw_value or "").strip()
    locator = str(evidence.locator or "").strip()
    expected_hash = hashlib.sha256(parsed.encode("utf-8")).hexdigest()
    explicit_missing = (
        field_name in NULLABLE_EVIDENCE_FIELDS
        and actual_value is None
        and raw == EXPLICIT_MISSING
        and parsed == ""
    )
    return bool(
        (expected or explicit_missing)
        and raw
        and locator
        and parsed == expected
        and evidence.value_hash == expected_hash
    )


def candidate_evidence_is_valid(candidate, positions, recruitment_type: str) -> bool:
    batch_values = {
        "title": candidate.title,
        "recruitment_type": recruitment_type,
        "target_audience": candidate.target_audience,
        "published_on": candidate.published_on,
        "deadline": candidate.deadline,
        "official_page_url": candidate.official_page_url,
    }
    for field_name, actual_value in batch_values.items():
        evidence = candidate.field_evidence.get(field_name)
        if evidence is None:
            return False
        parsed = normalize_evidence_value(field_name, evidence.parsed_value)
        expected = normalize_evidence_value(field_name, actual_value)
        explicit_missing = (
            field_name in NULLABLE_EVIDENCE_FIELDS
            and actual_value is None
            and str(evidence.raw_value or "").strip() == EXPLICIT_MISSING
            and parsed == ""
        )
        if not (
            (expected or explicit_missing)
            and str(evidence.raw_value or "").strip()
            and str(evidence.locator or "").strip()
            and parsed == expected
        ):
            return False
    for position in positions:
        values = {
            "position_title": position.title,
            "location": position.location_text,
        }
        if position.application_url:
            values["application_link"] = position.application_url
        if position.source_updated_on:
            values["source_updated_on"] = position.source_updated_on
        for field_name, actual_value in values.items():
            evidence = position.field_evidence.get(field_name)
            if evidence is None:
                return False
            if not (
                normalize_evidence_value(field_name, actual_value)
                and str(evidence.raw_value or "").strip()
                and str(evidence.locator or "").strip()
                and normalize_evidence_value(field_name, evidence.parsed_value)
                == normalize_evidence_value(field_name, actual_value)
            ):
                return False
    return True


def batch_projection_has_valid_evidence_for_event(
    batch, event, *, current_only: bool
) -> bool:
    if event is None or event.batch_id != batch.pk:
        return False
    version = event.source_version
    if version.source_id != batch.source_id or not version.is_applied:
        return False
    evidence = list(
        batch.evidence.filter(
            publication_event=event,
            source_version=version,
        ).select_related("position", "application_link")
    )

    def matching(field_name: str, actual_value, *, position_id=None, link_id=None):
        return any(
            item.field_name == field_name
            and item.position_id == position_id
            and item.application_link_id == link_id
            and field_evidence_matches(field_name, item, actual_value)
            for item in evidence
        )

    batch_values = {
        "title": batch.title,
        "recruitment_type": batch.recruitment_type,
        "target_audience": batch.target_audience,
        "published_on": batch.published_on,
        "deadline": batch.deadline,
        "official_page_url": batch.official_page_url,
    }
    if any(not matching(name, value) for name, value in batch_values.items()):
        return False
    if current_only:
        positions = list(batch.positions.filter(is_current=True))
        links = list(batch.application_links.filter(is_current=True))
    else:
        position_ids = {
            item.position_id
            for item in evidence
            if item.position_id
            and item.field_name in {"position_title", "location"}
        }
        link_ids = {
            item.application_link_id
            for item in evidence
            if item.application_link_id and item.field_name == "application_link"
        }
        positions = list(batch.positions.filter(pk__in=position_ids))
        links = list(batch.application_links.filter(pk__in=link_ids))
    if not positions:
        return False
    for position in positions:
        if not matching("position_title", position.title, position_id=position.pk):
            return False
        if not matching("location", position.location_text, position_id=position.pk):
            return False
        if position.raw_text and not matching(
            "raw_text", position.raw_text, position_id=position.pk
        ):
            return False
        if position.source_updated_on and not matching(
            "source_updated_on",
            position.source_updated_on,
            position_id=position.pk,
        ):
            return False
    position_ids = {position.pk for position in positions}
    from radar.services.admission import source_permits_application_url

    for link in links:
        if (
            link.batch_id != batch.pk
            or link.position_id not in position_ids
            or not source_permits_application_url(batch.source, link.url)
        ):
            return False
        if not matching(
            "application_link",
            link.url,
            position_id=link.position_id,
            link_id=link.pk,
        ):
            return False
    return True


def batch_projection_has_valid_evidence(batch) -> bool:
    return batch_projection_has_valid_evidence_for_event(
        batch, batch.latest_publication_event, current_only=True
    )


def batch_has_trusted_history(batch) -> bool:
    return trusted_historical_projection(batch) is not None


def trusted_historical_projection(batch) -> TrustedHistoricalProjection | None:
    events = batch.publication_events.filter(
        event_type__in=("published", "updated"),
        evidence_complete=True,
        source_version__is_applied=True,
        source_version__source_id=batch.source_id,
    ).select_related("source_version").order_by("-pk")
    for event in events:
        if not batch_projection_has_valid_evidence_for_event(
            batch,
            event,
            current_only=False,
        ):
            continue
        evidence = batch.evidence.filter(
            publication_event=event,
            source_version=event.source_version,
        )
        position_ids = tuple(
            sorted(
                {
                    item.position_id
                    for item in evidence
                    if item.position_id
                    and item.field_name in {"position_title", "location"}
                }
            )
        )
        application_link_ids = tuple(
            sorted(
                {
                    item.application_link_id
                    for item in evidence
                    if item.application_link_id
                    and item.field_name == "application_link"
                }
            )
        )
        return TrustedHistoricalProjection(
            publication_event_id=event.pk,
            position_ids=position_ids,
            application_link_ids=application_link_ids,
        )
    return None
