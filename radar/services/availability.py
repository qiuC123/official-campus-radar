from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from typing import Callable, Literal
from urllib.parse import urlsplit

from radar.collectors.base import (
    FieldEvidenceValue,
    FetchedPage,
    RecruitmentBatchCandidate,
)
from radar.models import OfficialSource, RecruitmentBatch
from radar.services.announcement_discovery import (
    RenderedOfficialPage,
    playwright_render_official_page,
)
from radar.services.normalization import canonicalize_url


MAX_RENDERED_DOCUMENT_BYTES = 2 * 1024 * 1024
MAX_SIGNAL_COUNT = 10
MAX_SIGNAL_LENGTH = 200
ALLOWED_PROBE_KEYS = {
    "mode",
    "url",
    "timeout_seconds",
    "ready_text_any",
    "closed_text_any",
    "open_text_any",
    "position_count_pattern",
}
ALLOWED_PARTITION_PROBE_KEYS = ALLOWED_PROBE_KEYS | {"identity_key"}
MAX_PARTITION_PROBE_COUNT = 20


class AvailabilityProbeError(ValueError):
    pass


@dataclass(frozen=True)
class AvailabilityObservation:
    state: Literal["open", "closed"]
    url: str
    content_hash: str
    evidence_excerpt: str


def _text_list(
    config: dict,
    name: str,
    *,
    required: bool = False,
    config_path: str = "availability_probe",
) -> tuple[str, ...]:
    raw_values = config.get(name, [])
    if not isinstance(raw_values, list):
        raise ValueError(f"{config_path}.{name} must be a list")
    values = tuple(str(value).strip() for value in raw_values)
    if required and not values:
        raise ValueError(f"{config_path}.{name} must not be empty")
    if len(values) > MAX_SIGNAL_COUNT or any(
        not value or len(value) > MAX_SIGNAL_LENGTH for value in values
    ):
        raise ValueError(
            f"{config_path}.{name} must contain 1..{MAX_SIGNAL_COUNT} "
            f"non-empty values up to {MAX_SIGNAL_LENGTH} characters"
        )
    return values


def _validate_probe_config(
    source: OfficialSource,
    config: dict,
    *,
    config_path: str,
    allowed_keys: set[str],
) -> None:
    if not isinstance(config, dict):
        raise ValueError(f"{config_path} must be an object")
    unexpected = set(config) - allowed_keys
    if unexpected:
        raise ValueError(
            f"{config_path} contains unsupported settings: "
            + ", ".join(sorted(unexpected))
        )
    if config.get("mode") != "browser_text":
        raise ValueError(f"{config_path}.mode must be browser_text")

    probe_url = urlsplit(str(config.get("url", "")).strip())
    source_url = urlsplit(source.source_url)
    if (
        probe_url.scheme != "https"
        or not probe_url.hostname
        or probe_url.username is not None
        or probe_url.password is not None
        or probe_url.hostname.casefold()
        != (source_url.hostname or "").casefold()
    ):
        raise ValueError(
            f"{config_path}.url must use HTTPS on the exact source host"
        )

    timeout = config.get("timeout_seconds", 30)
    if (
        not isinstance(timeout, int)
        or isinstance(timeout, bool)
        or timeout < 5
        or timeout > 60
    ):
        raise ValueError(f"{config_path}.timeout_seconds must be 5..60")
    _text_list(
        config,
        "ready_text_any",
        required=True,
        config_path=config_path,
    )
    closed_text = _text_list(
        config,
        "closed_text_any",
        config_path=config_path,
    )
    open_text = _text_list(
        config,
        "open_text_any",
        config_path=config_path,
    )
    pattern_text = str(config.get("position_count_pattern", "")).strip()
    if not closed_text and not open_text and not pattern_text:
        raise ValueError(f"{config_path} requires an open or closed signal")
    if pattern_text:
        if len(pattern_text) > MAX_SIGNAL_LENGTH:
            raise ValueError(f"{config_path}.position_count_pattern is too long")
        try:
            pattern = re.compile(pattern_text)
        except re.error as error:
            raise ValueError(
                f"{config_path}.position_count_pattern is invalid"
            ) from error
        if pattern.groups != 1:
            raise ValueError(
                f"{config_path}.position_count_pattern requires one capture group"
            )


def validate_availability_probe_config(source: OfficialSource) -> None:
    source_config = source.parser_config
    if not isinstance(source_config, dict):
        return
    config = source_config.get("availability_probe")
    partition_configs = source_config.get("partition_availability_probes")
    if config is not None and partition_configs is not None:
        raise ValueError(
            "availability_probe and partition_availability_probes are mutually exclusive"
        )
    if config is not None:
        _validate_probe_config(
            source,
            config,
            config_path="availability_probe",
            allowed_keys=ALLOWED_PROBE_KEYS,
        )
    if config is not None and source_config.get("batch_partitions"):
        raise ValueError(
            "source-level availability_probe cannot be used with batch_partitions"
        )
    if partition_configs is None:
        return
    if not isinstance(partition_configs, list):
        raise ValueError("partition_availability_probes must be a list")
    if not 1 <= len(partition_configs) <= MAX_PARTITION_PROBE_COUNT:
        raise ValueError(
            "partition_availability_probes must contain 1..20 entries"
        )
    partitions = source_config.get("batch_partitions")
    if not isinstance(partitions, list) or not partitions:
        raise ValueError(
            "partition_availability_probes requires batch_partitions"
        )
    partition_identities = {
        str(partition.get("batch", {}).get("identity_key", "")).strip()
        for partition in partitions
        if isinstance(partition, dict)
        and isinstance(partition.get("batch"), dict)
    }
    identities: set[str] = set()
    for index, partition_config in enumerate(partition_configs):
        config_path = f"partition_availability_probes[{index}]"
        _validate_probe_config(
            source,
            partition_config,
            config_path=config_path,
            allowed_keys=ALLOWED_PARTITION_PROBE_KEYS,
        )
        identity_key = str(partition_config.get("identity_key", "")).strip()
        if not identity_key:
            raise ValueError(f"{config_path}.identity_key is required")
        if identity_key in identities:
            raise ValueError(
                "partition_availability_probes identity_key values must be unique"
            )
        if identity_key not in partition_identities:
            raise ValueError(
                f"{config_path}.identity_key must match a configured batch partition"
            )
        identities.add(identity_key)


def _matched_values(body_text: str, values: tuple[str, ...]) -> tuple[str, ...]:
    folded = body_text.casefold()
    return tuple(value for value in values if value.casefold() in folded)


def _probe_availability(
    source: OfficialSource,
    config: dict,
    *,
    renderer: Callable[..., RenderedOfficialPage] = playwright_render_official_page,
    config_path: str = "availability_probe",
) -> AvailabilityObservation:
    ready_text = _text_list(
        config,
        "ready_text_any",
        required=True,
        config_path=config_path,
    )
    rendered = renderer(
        str(config["url"]).strip(),
        timeout_seconds=int(config.get("timeout_seconds", 30)),
        wait_for_text=ready_text,
    )
    observed_url = urlsplit(canonicalize_url(rendered.url))
    source_host = (urlsplit(source.source_url).hostname or "").casefold()
    if (
        observed_url.scheme != "https"
        or observed_url.username is not None
        or observed_url.password is not None
        or (observed_url.hostname or "").casefold() != source_host
    ):
        raise AvailabilityProbeError(
            "availability probe redirected outside the exact source host"
        )
    encoded_text = rendered.body_text.encode("utf-8")
    if len(encoded_text) > MAX_RENDERED_DOCUMENT_BYTES:
        raise AvailabilityProbeError("availability probe document exceeds 2 MiB")

    closed_matches = _matched_values(
        rendered.body_text,
        _text_list(config, "closed_text_any", config_path=config_path),
    )
    open_matches = _matched_values(
        rendered.body_text,
        _text_list(config, "open_text_any", config_path=config_path),
    )
    counts: set[int] = set()
    pattern_text = str(config.get("position_count_pattern", "")).strip()
    if pattern_text:
        for match in re.finditer(pattern_text, rendered.body_text, flags=re.IGNORECASE):
            try:
                counts.add(int(match.group(1)))
            except (TypeError, ValueError) as error:
                raise AvailabilityProbeError(
                    "availability position count is not an integer"
                ) from error

    closed = bool(closed_matches) or counts == {0}
    open_ = bool(open_matches) or bool(counts and 0 not in counts)
    if closed and open_:
        raise AvailabilityProbeError("availability probe returned conflicting signals")
    if not closed and not open_:
        raise AvailabilityProbeError("availability probe returned no decisive signal")

    state: Literal["open", "closed"] = "closed" if closed else "open"
    evidence_parts = [f"state={state}"]
    if closed_matches:
        evidence_parts.append("closed_text=" + "|".join(closed_matches))
    if open_matches:
        evidence_parts.append("open_text=" + "|".join(open_matches))
    if counts:
        evidence_parts.append("position_counts=" + "|".join(map(str, sorted(counts))))
    evidence_excerpt = "; ".join(evidence_parts)
    content_payload = json.dumps(
        {
            "availability": state,
            "evidence": evidence_excerpt,
            "url": canonicalize_url(rendered.url),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return AvailabilityObservation(
        state=state,
        url=canonicalize_url(rendered.url),
        content_hash=hashlib.sha256(content_payload.encode("utf-8")).hexdigest(),
        evidence_excerpt=evidence_excerpt,
    )


def probe_source_availability(
    source: OfficialSource,
    *,
    renderer: Callable[..., RenderedOfficialPage] = playwright_render_official_page,
) -> AvailabilityObservation | None:
    source_config = source.parser_config
    if not isinstance(source_config, dict) or "availability_probe" not in source_config:
        return None
    validate_availability_probe_config(source)
    return _probe_availability(
        source,
        source_config["availability_probe"],
        renderer=renderer,
    )


def probe_partition_availability(
    source: OfficialSource,
    *,
    renderer: Callable[..., RenderedOfficialPage] = playwright_render_official_page,
) -> dict[str, AvailabilityObservation]:
    source_config = source.parser_config
    if (
        not isinstance(source_config, dict)
        or "partition_availability_probes" not in source_config
    ):
        return {}
    validate_availability_probe_config(source)
    return {
        str(config["identity_key"]).strip(): _probe_availability(
            source,
            config,
            renderer=renderer,
            config_path=f"partition_availability_probes[{index}]",
        )
        for index, config in enumerate(
            source_config["partition_availability_probes"]
        )
    }


def closed_availability_page(observation: AvailabilityObservation) -> FetchedPage:
    body = json.dumps(
        {
            "availability": observation.state,
            "evidence": observation.evidence_excerpt,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return FetchedPage(
        canonical_url=observation.url,
        body=body,
        content_hash=observation.content_hash,
        http_status=200,
        etag=None,
    )


def closed_availability_candidate(
    source: OfficialSource,
    observation: AvailabilityObservation,
) -> RecruitmentBatchCandidate:
    batch = source.parser_config["batch"]
    evidence = FieldEvidenceValue(
        raw_value=observation.evidence_excerpt,
        locator="browser:body-text",
        parsed_value=RecruitmentBatch.Status.WITHDRAWN,
    )
    return RecruitmentBatchCandidate(
        title=str(batch["title"]),
        official_page_url=str(batch["official_page_url"]),
        recruitment_type=str(batch["recruitment_type"]),
        target_audience=str(batch["target_audience"]),
        published_on=None,
        deadline=None,
        withdrawn=True,
        evidence_excerpt=observation.evidence_excerpt,
        positions=(),
        identity_key=str(batch["identity_key"]),
        field_evidence={"availability": evidence},
        positions_complete=True,
    )


def apply_partition_availability(
    source: OfficialSource,
    page: FetchedPage,
    candidates: list[RecruitmentBatchCandidate],
    observations: dict[str, AvailabilityObservation],
) -> tuple[FetchedPage, list[RecruitmentBatchCandidate]]:
    if not observations:
        return page, candidates
    config = source.parser_config
    partitions = config.get("batch_partitions", [])
    batch_by_identity = {
        str(partition["batch"]["identity_key"]): partition["batch"]
        for partition in partitions
    }
    result_candidates = list(candidates)
    candidate_index_by_identity = {
        candidate.identity_key: index
        for index, candidate in enumerate(result_candidates)
    }
    for identity_key, observation in observations.items():
        candidate_index = candidate_index_by_identity.get(identity_key)
        candidate = (
            None if candidate_index is None else result_candidates[candidate_index]
        )
        if observation.state == "open":
            if candidate is None:
                raise AvailabilityProbeError(
                    "open partition is missing from the complete position inventory"
                )
            continue
        batch = batch_by_identity[identity_key]
        evidence = FieldEvidenceValue(
            raw_value=observation.evidence_excerpt,
            locator="browser:body-text",
            parsed_value=RecruitmentBatch.Status.WITHDRAWN,
        )
        if candidate is None:
            candidate = RecruitmentBatchCandidate(
                title=str(batch["title"]),
                official_page_url=str(batch["official_page_url"]),
                recruitment_type=str(batch["recruitment_type"]),
                target_audience=str(batch["target_audience"]),
                published_on=None,
                deadline=None,
                withdrawn=True,
                evidence_excerpt=observation.evidence_excerpt,
                positions=(),
                identity_key=identity_key,
                field_evidence={"availability": evidence},
                positions_complete=True,
            )
            candidate_index_by_identity[identity_key] = len(result_candidates)
            result_candidates.append(candidate)
        else:
            candidate = replace(
                candidate,
                withdrawn=True,
                evidence_excerpt=observation.evidence_excerpt,
                positions=(),
                field_evidence={"availability": evidence},
                positions_complete=True,
            )
            result_candidates[candidate_index] = candidate

    content_payload = json.dumps(
        {
            "inventory_content_hash": page.content_hash,
            "partition_availability": {
                identity_key: observation.content_hash
                for identity_key, observation in sorted(observations.items())
            },
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    combined_page = replace(
        page,
        content_hash=hashlib.sha256(content_payload.encode("utf-8")).hexdigest(),
        not_modified=False,
    )
    return combined_page, result_candidates


def source_availability_gate_passes(source: OfficialSource) -> bool:
    config = source.parser_config
    if not isinstance(config, dict) or not (
        "availability_probe" in config
        or "partition_availability_probes" in config
    ):
        return True
    return not bool(source.last_error.strip())
