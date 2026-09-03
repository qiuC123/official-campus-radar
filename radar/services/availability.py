from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
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


class AvailabilityProbeError(ValueError):
    pass


@dataclass(frozen=True)
class AvailabilityObservation:
    state: Literal["open", "closed"]
    url: str
    content_hash: str
    evidence_excerpt: str


def _text_list(config: dict, name: str, *, required: bool = False) -> tuple[str, ...]:
    raw_values = config.get(name, [])
    if not isinstance(raw_values, list):
        raise ValueError(f"availability_probe.{name} must be a list")
    values = tuple(str(value).strip() for value in raw_values)
    if required and not values:
        raise ValueError(f"availability_probe.{name} must not be empty")
    if len(values) > MAX_SIGNAL_COUNT or any(
        not value or len(value) > MAX_SIGNAL_LENGTH for value in values
    ):
        raise ValueError(
            f"availability_probe.{name} must contain 1..{MAX_SIGNAL_COUNT} "
            f"non-empty values up to {MAX_SIGNAL_LENGTH} characters"
        )
    return values


def validate_availability_probe_config(source: OfficialSource) -> None:
    source_config = source.parser_config
    if not isinstance(source_config, dict):
        return
    config = source_config.get("availability_probe")
    if config is None:
        return
    if not isinstance(config, dict):
        raise ValueError("availability_probe must be an object")
    unexpected = set(config) - ALLOWED_PROBE_KEYS
    if unexpected:
        raise ValueError(
            "availability_probe contains unsupported settings: "
            + ", ".join(sorted(unexpected))
        )
    if config.get("mode") != "browser_text":
        raise ValueError("availability_probe.mode must be browser_text")

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
            "availability_probe.url must use HTTPS on the exact source host"
        )

    timeout = config.get("timeout_seconds", 30)
    if (
        not isinstance(timeout, int)
        or isinstance(timeout, bool)
        or timeout < 5
        or timeout > 60
    ):
        raise ValueError("availability_probe.timeout_seconds must be 5..60")
    _text_list(config, "ready_text_any", required=True)
    closed_text = _text_list(config, "closed_text_any")
    open_text = _text_list(config, "open_text_any")
    pattern_text = str(config.get("position_count_pattern", "")).strip()
    if not closed_text and not open_text and not pattern_text:
        raise ValueError("availability_probe requires an open or closed signal")
    if pattern_text:
        if len(pattern_text) > MAX_SIGNAL_LENGTH:
            raise ValueError("availability_probe.position_count_pattern is too long")
        try:
            pattern = re.compile(pattern_text)
        except re.error as error:
            raise ValueError(
                "availability_probe.position_count_pattern is invalid"
            ) from error
        if pattern.groups != 1:
            raise ValueError(
                "availability_probe.position_count_pattern requires one capture group"
            )
    if source_config.get("batch_partitions"):
        raise ValueError(
            "source-level availability_probe cannot be used with batch_partitions"
        )


def _matched_values(body_text: str, values: tuple[str, ...]) -> tuple[str, ...]:
    folded = body_text.casefold()
    return tuple(value for value in values if value.casefold() in folded)


def probe_source_availability(
    source: OfficialSource,
    *,
    renderer: Callable[..., RenderedOfficialPage] = playwright_render_official_page,
) -> AvailabilityObservation | None:
    source_config = source.parser_config
    if not isinstance(source_config, dict) or "availability_probe" not in source_config:
        return None
    validate_availability_probe_config(source)
    config = source_config["availability_probe"]
    ready_text = _text_list(config, "ready_text_any", required=True)
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
        _text_list(config, "closed_text_any"),
    )
    open_matches = _matched_values(
        rendered.body_text,
        _text_list(config, "open_text_any"),
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


def source_availability_gate_passes(source: OfficialSource) -> bool:
    config = source.parser_config
    if not isinstance(config, dict) or "availability_probe" not in config:
        return True
    return not bool(source.last_error.strip())
