from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import transaction

from radar.models import ApprovedApplicationHost, OfficialSource, SourceAdmissionEvent


ALLOWED_ADMISSION_TRANSITIONS = {
    OfficialSource.AdmissionState.CANDIDATE: {
        OfficialSource.AdmissionState.VERIFIED
    },
    OfficialSource.AdmissionState.VERIFIED: {
        OfficialSource.AdmissionState.ENABLED
    },
    OfficialSource.AdmissionState.ENABLED: {
        OfficialSource.AdmissionState.SUSPENDED,
        OfficialSource.AdmissionState.REVOKED,
    },
    OfficialSource.AdmissionState.SUSPENDED: {
        OfficialSource.AdmissionState.VERIFIED,
        OfficialSource.AdmissionState.REVOKED,
    },
    OfficialSource.AdmissionState.REVOKED: set(),
}


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _belongs_to_official_domain(host: str, official_domain: str) -> bool:
    domain = official_domain.lower().strip()
    return bool(domain) and (host == domain or host.endswith(f".{domain}"))


def _api_endpoint_is_official(source: OfficialSource) -> bool:
    config = source.parser_config
    if not isinstance(config, dict):
        return False
    endpoint = str(config.get("endpoint", "")).strip()
    return (
        urlparse(endpoint).scheme == "https"
        and _belongs_to_official_domain(
            _host(endpoint), source.organization.official_domain
        )
    )


def _validated_admission_chain(source: OfficialSource) -> list[SourceAdmissionEvent] | None:
    prefetched = getattr(source, "_prefetched_objects_cache", {}).get("admission_events")
    events = (
        sorted(prefetched, key=lambda item: (item.created_at, item.pk))
        if prefetched is not None
        else list(source.admission_events.order_by("created_at", "pk"))
    )
    if not events:
        return None
    current_state = OfficialSource.AdmissionState.CANDIDATE
    previous_hash = "0" * 64
    for index, event in enumerate(events):
        if not all(
            str(value or "").strip()
            for value in (event.actor_label, event.reason, event.evidence)
        ):
            return None
        if event.previous_event_hash != previous_hash:
            return None
        expected_hash = SourceAdmissionEvent.calculate_hash(
            source_id=event.source_id,
            from_state=event.from_state,
            to_state=event.to_state,
            actor_label=event.actor_label,
            reason=event.reason,
            evidence=event.evidence,
            previous_event_hash=event.previous_event_hash,
        )
        if event.event_hash != expected_hash:
            return None
        if (
            index == 0
            and event.from_state == ""
            and event.to_state == OfficialSource.AdmissionState.CANDIDATE
        ):
            previous_hash = event.event_hash
            continue
        if event.from_state != current_state:
            return None
        if event.to_state not in ALLOWED_ADMISSION_TRANSITIONS[current_state]:
            return None
        current_state = event.to_state
        previous_hash = event.event_hash
    if current_state != source.admission_state:
        return None
    return events


def _has_valid_application_host_approval(
    source: OfficialSource,
    host: str,
    chain: list[SourceAdmissionEvent] | None = None,
) -> bool:
    """Recheck an approved host's facts, digest, and admission-chain ownership."""
    chain = chain if chain is not None else _validated_admission_chain(source)
    if not chain:
        return False
    chain_event_ids = {event.pk for event in chain}
    prefetched = getattr(source, "_prefetched_objects_cache", {}).get(
        "approved_application_hosts"
    )
    approvals = (
        [item for item in prefetched if item.host == host]
        if prefetched is not None
        else source.approved_application_hosts.filter(host=host).select_related(
            "admission_event"
        )
    )
    return any(
        approval.source_id == source.pk
        and approval.admission_event_id in chain_event_ids
        and approval.admission_event.source_id == source.pk
        and approval.admission_event.to_state
        == OfficialSource.AdmissionState.VERIFIED
        and all(
            str(value or "").strip()
            for value in (approval.host, approval.actor_label, approval.evidence)
        )
        and approval.approval_digest == approval.calculate_digest()
        for approval in approvals
    )


def source_is_admitted(source: OfficialSource) -> bool:
    if (
        source.admission_state != OfficialSource.AdmissionState.ENABLED
        or not source.is_verified
        or not source.is_active
    ):
        return False
    if urlparse(source.source_url).scheme != "https":
        return False
    chain = _validated_admission_chain(source)
    if not chain or chain[-1].to_state != OfficialSource.AdmissionState.ENABLED:
        return False
    source_host = _host(source.source_url)
    official_domain = source.organization.official_domain
    if source.source_type in {
        OfficialSource.SourceType.WEBSITE,
        OfficialSource.SourceType.ANNOUNCEMENT,
    }:
        return _belongs_to_official_domain(source_host, official_domain)
    if source.source_type == OfficialSource.SourceType.API:
        return (
            _belongs_to_official_domain(source_host, official_domain)
            and _api_endpoint_is_official(source)
        )
    if source.source_type == OfficialSource.SourceType.ATS:
        return (
            bool(source.official_entrypoint_url)
            and urlparse(source.official_entrypoint_url).scheme == "https"
            and _belongs_to_official_domain(
                _host(source.official_entrypoint_url), official_domain
            )
            and _has_valid_application_host_approval(source, source_host, chain)
        )
    return source.source_type == OfficialSource.SourceType.WECHAT


def valid_admitted_source_ids() -> list[int]:
    sources = OfficialSource.objects.filter(
        admission_state=OfficialSource.AdmissionState.ENABLED,
        is_verified=True,
        is_active=True,
    ).select_related("organization").prefetch_related(
        "admission_events", "approved_application_hosts__admission_event"
    )
    return [source.pk for source in sources if source_is_admitted(source)]


def valid_historical_source_ids() -> list[int]:
    sources = OfficialSource.objects.select_related("organization").prefetch_related(
        "admission_events"
    )
    valid_ids = []
    for source in sources:
        chain = _validated_admission_chain(source)
        if chain and any(
            event.to_state == OfficialSource.AdmissionState.ENABLED
            for event in chain
        ):
            valid_ids.append(source.pk)
    return valid_ids


def source_permits_batch_url(source: OfficialSource, url: str) -> bool:
    return urlparse(url).scheme == "https" and _host(url) == _host(source.source_url)


def source_permits_application_url(source: OfficialSource, url: str) -> bool:
    if urlparse(url).scheme != "https":
        return False
    host = _host(url)
    cache = getattr(source, "_prefetched_objects_cache", {})
    if "admission_events" not in cache or "organization" not in source._state.fields_cache:
        source = OfficialSource.objects.select_related("organization").prefetch_related(
            "admission_events", "approved_application_hosts__admission_event"
        ).get(pk=source.pk)
    chain = _validated_admission_chain(source)
    if not chain:
        return False
    if (
        host == _host(source.source_url)
        and source.source_type != OfficialSource.SourceType.ATS
    ):
        return True
    return _has_valid_application_host_approval(source, host, chain)


def source_permits_url(
    source: OfficialSource, url: str, *, application: bool = False
) -> bool:
    if application:
        return source_permits_application_url(source, url)
    return source_permits_batch_url(source, url)


def _validate_verification_candidate(source: OfficialSource) -> None:
    source_host = _host(source.source_url)
    official_domain = source.organization.official_domain
    if urlparse(source.source_url).scheme != "https":
        raise ValidationError("source URL must use HTTPS")
    if source.source_type in {
        OfficialSource.SourceType.WEBSITE,
        OfficialSource.SourceType.ANNOUNCEMENT,
        OfficialSource.SourceType.API,
    }:
        if not _belongs_to_official_domain(source_host, official_domain):
            raise ValidationError(
                "website source host must belong to the official domain"
            )
        if (
            source.source_type == OfficialSource.SourceType.API
            and not _api_endpoint_is_official(source)
        ):
            raise ValidationError(
                "API endpoint must use HTTPS and belong to the official domain"
            )
    elif source.source_type in {
        OfficialSource.SourceType.ATS,
        OfficialSource.SourceType.WECHAT,
    }:
        if not source.official_entrypoint_url or not _belongs_to_official_domain(
            _host(source.official_entrypoint_url), official_domain
        ):
            raise ValidationError(
                "external source requires an official-domain entrypoint"
            )


@transaction.atomic
def transition_source(
    source: OfficialSource,
    *,
    to_state: str,
    actor_label: str,
    reason: str,
    evidence: str,
) -> SourceAdmissionEvent:
    source = OfficialSource.objects.select_for_update().get(pk=source.pk)
    if not all(value.strip() for value in (actor_label, reason, evidence)):
        raise ValidationError("actor, reason, and evidence are required")
    if to_state not in ALLOWED_ADMISSION_TRANSITIONS[source.admission_state]:
        raise ValidationError(
            f"invalid source admission transition: {source.admission_state} -> {to_state}"
        )
    if to_state == OfficialSource.AdmissionState.VERIFIED:
        _validate_verification_candidate(source)
    if (
        to_state == OfficialSource.AdmissionState.ENABLED
        and source.source_type == OfficialSource.SourceType.ATS
        and not _has_valid_application_host_approval(
            source, _host(source.source_url)
        )
    ):
        raise ValidationError("ATS source host requires official-entrypoint approval")
    if (
        to_state == OfficialSource.AdmissionState.ENABLED
        and source.source_type != OfficialSource.SourceType.ANNOUNCEMENT
    ):
        from radar.collectors.registry import AdapterRegistry

        try:
            AdapterRegistry.validate_source_config(source)
        except ValueError as error:
            raise ValidationError(str(error)) from error
    event = SourceAdmissionEvent.objects.create(
        source=source,
        from_state=source.admission_state,
        to_state=to_state,
        actor_label=actor_label.strip(),
        reason=reason.strip(),
        evidence=evidence.strip(),
    )
    source.admission_state = to_state
    source.is_verified = to_state in {
        OfficialSource.AdmissionState.VERIFIED,
        OfficialSource.AdmissionState.ENABLED,
        OfficialSource.AdmissionState.SUSPENDED,
    }
    source.is_active = to_state == OfficialSource.AdmissionState.ENABLED
    source.save(update_fields=["admission_state", "is_verified", "is_active"])
    return event


@transaction.atomic
def approve_application_host(
    source: OfficialSource,
    *,
    host: str,
    actor_label: str,
    evidence: str,
) -> ApprovedApplicationHost:
    source = OfficialSource.objects.select_for_update().get(pk=source.pk)
    normalized_host = _host(f"https://{host.strip().lower()}")
    if not normalized_host or not actor_label.strip() or not evidence.strip():
        raise ValidationError("host, actor, and evidence are required")
    if source.admission_state != OfficialSource.AdmissionState.VERIFIED:
        raise ValidationError(
            "application hosts can only be approved after verification"
        )
    if not source.official_entrypoint_url or not _belongs_to_official_domain(
        _host(source.official_entrypoint_url), source.organization.official_domain
    ):
        raise ValidationError(
            "application host approval requires an official entrypoint"
        )
    chain = _validated_admission_chain(source)
    if not chain or chain[-1].to_state != OfficialSource.AdmissionState.VERIFIED:
        raise ValidationError("application host approval requires a valid verified chain")
    verification_event = source.admission_events.filter(
        to_state=OfficialSource.AdmissionState.VERIFIED
    ).latest("pk")
    return ApprovedApplicationHost.objects.create(
        source=source,
        host=normalized_host,
        evidence=evidence.strip(),
        actor_label=actor_label.strip(),
        admission_event=verification_event,
    )
