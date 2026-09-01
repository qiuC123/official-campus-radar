from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from radar.models import (
    AnnouncementDiscoveryCandidate,
    AnnouncementFieldEvidence,
    OfficialSource,
    Organization,
    ApplicationLink,
    RecruitmentAnnouncement,
    RecruitmentBatch,
    RecruitmentPolicy,
    RecruitmentPolicyEvent,
    RecruitmentPosition,
    WeChatAccountIdentity,
)
from radar.services.admission import source_is_admitted, source_permits_application_url
from radar.services.admission import transition_source
from radar.services.announcement_discovery import RefetchedOfficialCandidate
from radar.services.normalization import canonicalize_url


REQUIRED_ANNOUNCEMENT_FIELDS = {
    "title",
    "recruitment_type",
    "target_audience",
    "availability",
}
CURRENT_AUDIENCE_MARKERS = ("2027", "实习")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EXTERNAL_LINK_KINDS = {"wechat", "external_http", "email", "phone"}


def _normalized_name(value: str) -> str:
    return re.sub(r"\s+", "", value or "").casefold()


def _parse_datetime(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return parse_datetime(str(value))


def _normalized_wxcli_links(value) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 200:
        raise ValidationError("wxcli external links are invalid")
    normalized = []
    for item in value:
        if not isinstance(item, dict):
            raise ValidationError("wxcli external link must be an object")
        kind = str(item.get("kind") or "").strip()
        target = str(item.get("normalized_value") or "").strip()
        if kind not in _EXTERNAL_LINK_KINDS or not target:
            raise ValidationError("wxcli external link has invalid kind or target")
        try:
            index = int(item.get("index"))
        except (TypeError, ValueError) as error:
            raise ValidationError("wxcli external link index is invalid") from error
        if index < 0:
            raise ValidationError("wxcli external link index is invalid")
        normalized.append({
            "index": index,
            "source_location": str(item.get("source_location") or "").strip()[:500],
            "normalized_value": target[:2000],
            "kind": kind,
            "text": str(item.get("text") or "").strip()[:500],
        })
    return normalized


def _normalized_wxcli_media(value) -> list[dict]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 100:
        raise ValidationError("wxcli image evidence is invalid")
    normalized = []
    for item in value:
        if not isinstance(item, dict):
            raise ValidationError("wxcli image evidence must be an object")
        try:
            index = int(item.get("index"))
        except (TypeError, ValueError) as error:
            raise ValidationError("wxcli image index is invalid") from error
        url = str(item.get("url") or "").strip()
        if index < 0 or urlsplit(url).scheme != "https":
            raise ValidationError("wxcli image evidence requires an indexed HTTPS URL")
        media = {"index": index, "url": url[:2000]}
        # wxcli 0.4 only has index/url. These optional fields let Radar consume
        # a future media-evidence minor extension without treating it as Article text.
        for key, limit in (
            ("ocr_text", 20000),
            ("ocr_engine", 200),
            ("analysis_status", 64),
        ):
            if item.get(key) is not None:
                media[key] = str(item[key]).strip()[:limit]
        if isinstance(item.get("qr_payloads"), list):
            media["qr_payloads"] = [
                str(payload).strip()[:2000]
                for payload in item["qr_payloads"][:20]
                if str(payload).strip()
            ]
        normalized.append(media)
    return normalized


def _media_ocr_is_human_confirmed(media: dict) -> bool:
    return (
        str(media.get("analysis_status") or "").casefold() == "human_confirmed"
        and bool(str(media.get("ocr_text") or "").strip())
    )


def _image_locator_has_confirmed_excerpt(
    announcement: RecruitmentAnnouncement,
    excerpt: str,
    locator: str,
) -> bool:
    match = re.match(r"^image\[(\d+)\](?:/ocr)?$", locator.strip())
    if match is None:
        return True
    index = int(match.group(1))
    normalized_excerpt = re.sub(r"\s+", "", excerpt)
    return any(
        int(media.get("index", -1)) == index
        and _media_ocr_is_human_confirmed(media)
        and normalized_excerpt in re.sub(r"\s+", "", str(media.get("ocr_text") or ""))
        for media in announcement.observed_media or []
    )


def _source_for_url(organization: Organization, url: str) -> OfficialSource | None:
    host = (urlsplit(url).hostname or "").casefold()
    matches = []
    for source in organization.official_sources.all():
        source_host = (urlsplit(source.source_url).hostname or "").casefold()
        if (
            source_host
            and (host == source_host or host.endswith(f".{source_host}"))
            and source_is_admitted(source)
        ):
            matches.append((len(source_host), source))
    return max(matches, key=lambda item: item[0])[1] if matches else None


@transaction.atomic
def admit_official_domain_announcement_source(
    organization: Organization,
    url: str,
    *,
    actor_label: str,
    identity_evidence: str,
) -> OfficialSource:
    """Admit a read-only identity source for an announcement on the official domain."""

    parts = urlsplit(url)
    host = (parts.hostname or "").casefold()
    official_domain = organization.official_domain.casefold().strip()
    if (
        parts.scheme != "https"
        or not official_domain
        or parts.username
        or parts.password
        or not (host == official_domain or host.endswith(f".{official_domain}"))
    ):
        raise ValidationError("announcement source must belong to the configured official domain")
    actor = actor_label.strip()
    evidence = identity_evidence.strip()
    if not actor or not evidence:
        raise ValidationError("source admission requires actor and identity evidence")
    origin = urlunsplit(("https", parts.netloc, "", "", ""))
    source, _ = OfficialSource.objects.get_or_create(
        organization=organization,
        source_type=OfficialSource.SourceType.ANNOUNCEMENT,
        source_url=origin,
        defaults={
            "official_entrypoint_url": origin,
            "admission_evidence": evidence,
            "access_policy": "低频、公开、只用于核验招聘公告",
            "adapter_name": "announcement_only",
            "parser_config": {},
        },
    )
    if source.admission_state == OfficialSource.AdmissionState.CANDIDATE:
        transition_source(
            source,
            to_state=OfficialSource.AdmissionState.VERIFIED,
            actor_label=actor,
            reason="企业官方域名公告身份核验",
            evidence=evidence,
        )
        source.refresh_from_db()
    if source.admission_state == OfficialSource.AdmissionState.VERIFIED:
        transition_source(
            source,
            to_state=OfficialSource.AdmissionState.ENABLED,
            actor_label=actor,
            reason="启用只读公告身份源",
            evidence=evidence,
        )
        source.refresh_from_db()
    if not source_is_admitted(source):
        raise ValidationError("announcement source did not complete the admission chain")
    return source


@transaction.atomic
def verify_official_announcement(
    candidate: AnnouncementDiscoveryCandidate,
    refetched: RefetchedOfficialCandidate,
    *,
    identity_evidence: str,
) -> RecruitmentAnnouncement:
    if candidate.source_kind not in {
        RecruitmentAnnouncement.SourceKind.WEBSITE,
        RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM,
    }:
        raise ValidationError("candidate is not an official-site announcement")
    if not refetched.recruitment_signal_found:
        raise ValidationError("official page does not contain a recruitment-project signal")
    source = _source_for_url(candidate.organization, refetched.url)
    if source is None:
        raise ValidationError("official page is not covered by an admitted organization source")
    evidence = identity_evidence.strip()
    if not evidence:
        raise ValidationError("official identity evidence is required")
    announcement, _ = RecruitmentAnnouncement.objects.update_or_create(
        organization=candidate.organization,
        source_kind=candidate.source_kind,
        identity_key=hashlib.sha256(refetched.url.encode("utf-8")).hexdigest(),
        defaults={
            "source": source,
            "title": refetched.title or candidate.title_hint,
            "url": refetched.url,
            "last_verified_at": refetched.fetched_at,
            "identity_evidence": evidence,
            "content_sha256": refetched.content_sha256,
            "verification_status": RecruitmentAnnouncement.VerificationStatus.VERIFIED,
            "verification_method": refetched.verification_method,
        },
    )
    announcement.full_clean()
    announcement.save()
    candidate.state = AnnouncementDiscoveryCandidate.State.VERIFIED
    candidate.error_code = ""
    candidate.final_url = refetched.url
    candidate.content_sha256 = refetched.content_sha256
    candidate.recruitment_signal_found = refetched.recruitment_signal_found
    candidate.technical_verified_at = refetched.fetched_at
    candidate.announcement = announcement
    candidate.save(update_fields=[
        "state",
        "error_code",
        "final_url",
        "content_sha256",
        "recruitment_signal_found",
        "technical_verified_at",
        "announcement",
    ])
    return announcement


def _matched_wechat_identity(
    organization: Organization,
    observed_name: str,
    observed_biz_id: str,
) -> WeChatAccountIdentity | None:
    identities = organization.wechat_account_identities.filter(
        is_verified=True,
        verified_at__isnull=False,
    ).exclude(identity_evidence="")
    if observed_biz_id:
        matched = identities.filter(biz_id=observed_biz_id).first()
        if matched:
            return matched
    normalized = _normalized_name(observed_name)
    name_match = next(
        (item for item in identities if _normalized_name(item.display_name) == normalized),
        None,
    )
    if observed_biz_id and name_match and name_match.biz_id:
        return None
    return name_match


def announcement_identity_is_trusted(announcement: RecruitmentAnnouncement) -> bool:
    if announcement.verification_status != RecruitmentAnnouncement.VerificationStatus.VERIFIED:
        return False
    if not _SHA256.fullmatch(str(announcement.content_sha256 or "").casefold()):
        return False
    if announcement.source_kind in {
        RecruitmentAnnouncement.SourceKind.WEBSITE,
        RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM,
    }:
        if announcement.verification_method not in {
            RecruitmentAnnouncement.VerificationMethod.HTTP,
            RecruitmentAnnouncement.VerificationMethod.BROWSER,
            RecruitmentAnnouncement.VerificationMethod.HUMAN_SNAPSHOT,
        }:
            return False
        source = (
            announcement.source
            if announcement.source_id
            else None
        )
        if source is not None and "admission_events" not in getattr(
            source, "_prefetched_objects_cache", {}
        ):
            source = OfficialSource.objects.select_related("organization").prefetch_related(
                "admission_events", "approved_application_hosts__admission_event"
            ).get(pk=source.pk)
        announcement_host = (urlsplit(announcement.url).hostname or "").casefold()
        source_host = (
            (urlsplit(source.source_url).hostname or "").casefold()
            if source
            else ""
        )
        return bool(
            source
            and source_is_admitted(source)
            and source_host
            and (
                announcement_host == source_host
                or announcement_host.endswith(f".{source_host}")
            )
        )
    if announcement.source_kind == RecruitmentAnnouncement.SourceKind.WECHAT_ARTICLE:
        if announcement.verification_method != RecruitmentAnnouncement.VerificationMethod.WXCLI:
            return False
        if (urlsplit(announcement.url).hostname or "").casefold() != "mp.weixin.qq.com":
            return False
        return _matched_wechat_identity(
            announcement.organization,
            announcement.account_display_name,
            announcement.account_biz_id,
        ) is not None
    if announcement.source_kind == RecruitmentAnnouncement.SourceKind.WECHAT_MINIPROGRAM:
        if announcement.verification_method not in {
            RecruitmentAnnouncement.VerificationMethod.WXCLI,
            RecruitmentAnnouncement.VerificationMethod.HUMAN_SNAPSHOT,
        }:
            return False
        if not announcement.miniprogram_name.strip():
            return False
        return _matched_wechat_identity(
            announcement.organization,
            announcement.account_display_name,
            announcement.account_biz_id,
        ) is not None
    return False


@transaction.atomic
def import_wxcli_announcement(
    organization: Organization,
    verified_candidate: dict,
) -> RecruitmentAnnouncement:
    evidence = verified_candidate.get("evidence")
    if not isinstance(evidence, dict) or evidence.get("schema_version") != "1":
        raise ValidationError("wxcli candidate has no schema-v1 Article Evidence")
    article = evidence.get("article")
    account = evidence.get("account_identity")
    if not isinstance(article, dict) or not isinstance(account, dict):
        raise ValidationError("wxcli evidence is incomplete")
    observed_name = str(account.get("observed_display_name") or "").strip()
    observed_biz_id = str(account.get("observed_biz_id") or "").strip()
    identity = _matched_wechat_identity(organization, observed_name, observed_biz_id)
    if identity is None:
        raise ValidationError("WeChat account is not on the organization's verified allowlist")
    url = str(article.get("source_url") or verified_candidate.get("fetch_url") or "").strip()
    if (urlsplit(url).hostname or "").casefold() != "mp.weixin.qq.com":
        raise ValidationError("wxcli evidence does not point to a WeChat public article")
    title = str(article.get("title") or "").strip()
    if not title:
        raise ValidationError("wxcli evidence has no article title")
    markdown = str(article.get("content_markdown") or "").strip()
    links = _normalized_wxcli_links(evidence.get("external_links"))
    images = _normalized_wxcli_media(evidence.get("images"))
    if not markdown and not images:
        raise ValidationError("wxcli evidence has neither article text nor image evidence")
    content_sha256 = str(evidence.get("content_sha256") or "").strip().casefold()
    evidence_sha256 = str(evidence.get("evidence_sha256") or "").strip().casefold()
    if not _SHA256.fullmatch(content_sha256) or not _SHA256.fullmatch(evidence_sha256):
        raise ValidationError("wxcli evidence hashes are invalid")
    status = (
        RecruitmentAnnouncement.VerificationStatus.VERIFIED
        if markdown or any(_media_ocr_is_human_confirmed(media) for media in images)
        else RecruitmentAnnouncement.VerificationStatus.PENDING_IMAGE
    )
    identity_key = str(verified_candidate.get("article_identity") or "").strip()
    if not identity_key:
        raise ValidationError("wxcli candidate has no article identity")
    source = organization.official_sources.filter(
        source_type=OfficialSource.SourceType.WECHAT
    ).first()
    announcement, _ = RecruitmentAnnouncement.objects.update_or_create(
        organization=organization,
        source_kind=RecruitmentAnnouncement.SourceKind.WECHAT_ARTICLE,
        identity_key=identity_key,
        defaults={
            "source": source,
            "title": title,
            "url": canonicalize_url(url),
            "published_at": _parse_datetime(article.get("published_at")),
            "last_verified_at": _parse_datetime(evidence.get("last_verified_at")) or timezone.now(),
            "identity_evidence": identity.identity_evidence,
            "account_display_name": observed_name,
            "account_biz_id": observed_biz_id,
            "content_sha256": content_sha256,
            "evidence_sha256": evidence_sha256,
            "observed_external_links": links,
            "observed_media": images,
            "verification_status": status,
            "verification_method": RecruitmentAnnouncement.VerificationMethod.WXCLI,
        },
    )
    announcement.full_clean()
    announcement.save()
    return announcement


def observed_application_channel_candidates(
    announcement: RecruitmentAnnouncement,
) -> tuple[dict, ...]:
    """Return inert candidates; never visits or promotes a wxcli-observed target."""

    candidates = []
    for item in announcement.observed_external_links or []:
        if item.get("kind") not in {"external_http", "email"}:
            continue
        candidates.append({
            "kind": item["kind"],
            "target": item["normalized_value"],
            "text": item.get("text", ""),
            "source_location": item.get("source_location", ""),
            "verification_required": True,
        })
    for item in announcement.observed_media or []:
        for payload in item.get("qr_payloads", []):
            candidates.append({
                "kind": "qr_payload",
                "target": payload,
                "text": "",
                "source_location": f"image[{item.get('index')}]",
                "verification_required": True,
            })
    return tuple(candidates)


@transaction.atomic
def split_verified_announcement_project(
    announcement: RecruitmentAnnouncement,
    *,
    project_key: str,
    project_title: str,
    project_evidence: str,
) -> RecruitmentAnnouncement:
    """Create one project-scoped announcement identity from a multi-project page."""

    if not announcement_identity_is_trusted(announcement):
        raise ValidationError("only an identity-trusted announcement can be split")
    key = project_key.strip()
    title = project_title.strip()
    evidence = project_evidence.strip()
    if not key or len(key) > 200 or not title or not evidence:
        raise ValidationError("project split requires key, title, and explicit section evidence")
    identity_key = hashlib.sha256(
        f"{announcement.pk}:{announcement.identity_key}:{key}".encode("utf-8")
    ).hexdigest()
    project, _ = RecruitmentAnnouncement.objects.get_or_create(
        organization=announcement.organization,
        source_kind=announcement.source_kind,
        identity_key=identity_key,
        defaults={
            "source": announcement.source,
            "title": title,
            "url": announcement.url,
            "miniprogram_name": announcement.miniprogram_name,
            "miniprogram_path": announcement.miniprogram_path,
            "published_at": announcement.published_at,
            "last_verified_at": announcement.last_verified_at,
            "identity_evidence": f"{announcement.identity_evidence}\n项目范围：{evidence}",
            "account_display_name": announcement.account_display_name,
            "account_biz_id": announcement.account_biz_id,
            "content_sha256": announcement.content_sha256,
            "evidence_sha256": announcement.evidence_sha256,
            "observed_external_links": announcement.observed_external_links,
            "observed_media": announcement.observed_media,
            "verification_status": announcement.verification_status,
            "verification_method": announcement.verification_method,
        },
    )
    project.full_clean()
    project.save()
    return project


def announcement_evidence_is_complete(batch: RecruitmentBatch) -> bool:
    announcement = batch.primary_announcement
    if (
        announcement is None
        or announcement.organization_id != batch.organization_id
        or not announcement_identity_is_trusted(announcement)
    ):
        return False
    latest_by_field = {}
    prefetched = getattr(batch, "_prefetched_objects_cache", {}).get(
        "announcement_evidence"
    )
    evidence = (
        sorted(
            (item for item in prefetched if item.announcement_id == announcement.pk),
            key=lambda item: item.pk,
        )
        if prefetched is not None
        else batch.announcement_evidence.filter(announcement=announcement).order_by("pk")
    )
    for item in evidence:
        expected_hash = hashlib.sha256(item.parsed_value.encode("utf-8")).hexdigest()
        locator = item.locator.strip()
        snapshot_binding_is_valid = (
            announcement.verification_method
            != RecruitmentAnnouncement.VerificationMethod.HUMAN_SNAPSHOT
            or locator.startswith(f"snapshot[{announcement.content_sha256}]")
        )
        if (
            item.excerpt.strip()
            and locator
            and item.value_hash == expected_hash
            and snapshot_binding_is_valid
        ):
            latest_by_field[item.field_name] = item
    if not REQUIRED_ANNOUNCEMENT_FIELDS <= set(latest_by_field):
        return False
    expected = {
        "title": batch.title,
        "recruitment_type": batch.recruitment_type,
        "target_audience": batch.target_audience,
        "availability": RecruitmentBatch.Status.ACTIVE,
    }
    return all(latest_by_field[field].parsed_value == value for field, value in expected.items())


def announcement_direction_projection_is_complete(
    batch: RecruitmentBatch,
    *,
    current_only: bool = True,
) -> bool:
    announcement = batch.primary_announcement
    if announcement is None:
        return False
    direction_query = batch.positions.filter(kind=RecruitmentPosition.Kind.DIRECTION)
    if current_only:
        direction_query = direction_query.filter(is_current=True)
    directions = list(direction_query)
    if not directions:
        return False
    evidence = list(batch.announcement_evidence.filter(
        announcement=announcement,
        position__in=directions,
    ))
    by_position_and_field = {
        (item.position_id, item.field_name): item for item in evidence
    }
    for direction in directions:
        values = {
            "direction_title": direction.title,
            "direction_location": direction.location_text,
        }
        for field_name, expected in values.items():
            item = by_position_and_field.get((direction.pk, field_name))
            if (
                item is None
                or not item.excerpt.strip()
                or not item.locator.strip()
                or item.parsed_value != expected
                or item.value_hash
                != hashlib.sha256(expected.encode("utf-8")).hexdigest()
            ):
                return False
    channels = batch.application_links.filter(position__isnull=True)
    if current_only:
        channels = channels.filter(is_current=True)
    return any(
        (
            item.href
            or (
                item.link_type == ApplicationLink.LinkType.MINI_PROGRAM
                and item.miniprogram_name.strip()
            )
        )
        and item.verification_evidence.strip()
        for item in channels
    )


@transaction.atomic
def mark_batch_pending_with_announcement(
    batch: RecruitmentBatch,
    announcement: RecruitmentAnnouncement,
) -> RecruitmentBatch:
    """Link trusted evidence while keeping an unresolved batch out of the formal page."""

    if announcement.organization_id != batch.organization_id:
        raise ValidationError("announcement and batch organizations differ")
    if not announcement_identity_is_trusted(announcement):
        raise ValidationError("only identity-trusted announcements can mark a batch pending")
    if announcement.recruitment_batches.exclude(pk=batch.pk).exists():
        raise ValidationError("one primary announcement can belong to only one recruitment batch")
    if batch.primary_announcement_id and batch.primary_announcement_id != announcement.pk:
        raise ValidationError("an existing primary announcement cannot be replaced implicitly")
    batch.primary_announcement = announcement
    batch.announcement_admission = RecruitmentBatch.AnnouncementAdmission.PENDING
    batch.full_clean()
    batch.save(update_fields=["primary_announcement", "announcement_admission"])
    return batch


@transaction.atomic
def admit_batch_with_announcement(
    batch: RecruitmentBatch,
    announcement: RecruitmentAnnouncement,
    *,
    field_evidence: dict[str, tuple[str, str, str]],
    confirm_field_conflicts: bool = False,
) -> RecruitmentBatch:
    """Attach one verified notice; every interpreted batch field needs explicit proof."""

    if announcement.organization_id != batch.organization_id:
        raise ValidationError("announcement and batch organizations differ")
    if not announcement_identity_is_trusted(announcement):
        raise ValidationError("only identity-trusted announcements can admit a batch")
    if announcement.recruitment_batches.exclude(pk=batch.pk).exists():
        raise ValidationError("one primary announcement can admit only one recruitment batch")
    if set(field_evidence) != REQUIRED_ANNOUNCEMENT_FIELDS:
        raise ValidationError("announcement evidence must prove all required batch fields")
    interpreted = {field: values[0] for field, values in field_evidence.items()}
    if interpreted["recruitment_type"] not in RecruitmentBatch.RecruitmentType.values:
        raise ValidationError("announcement recruitment type is invalid")
    if interpreted["recruitment_type"] == RecruitmentBatch.RecruitmentType.UNKNOWN:
        raise ValidationError("announcement recruitment type must be explicit")
    if not interpreted["title"].strip() or not interpreted["target_audience"].strip():
        raise ValidationError("announcement title and target audience must be explicit")
    if (
        interpreted["recruitment_type"] != RecruitmentBatch.RecruitmentType.INTERNSHIP
        and not any(
            marker in interpreted["target_audience"]
            for marker in CURRENT_AUDIENCE_MARKERS
        )
    ):
        raise ValidationError("announcement is outside the current 2027/internship scope")
    if interpreted["availability"] != RecruitmentBatch.Status.ACTIVE:
        raise ValidationError("only currently available batches can be admitted")
    for field_name, (parsed_value, excerpt, locator) in field_evidence.items():
        if not excerpt.strip() or not locator.strip():
            raise ValidationError(f"announcement evidence for {field_name} is incomplete")
        if not _image_locator_has_confirmed_excerpt(announcement, excerpt, locator):
            raise ValidationError(
                f"announcement image evidence for {field_name} is not human-confirmed"
            )
        if (
            announcement.verification_method
            == RecruitmentAnnouncement.VerificationMethod.HUMAN_SNAPSHOT
            and not locator.strip().startswith(
                f"snapshot[{announcement.content_sha256}]"
            )
        ):
            raise ValidationError(
                f"snapshot announcement evidence for {field_name} has the wrong locator"
            )
    existing = batch.primary_announcement
    if existing is not None and existing.pk != announcement.pk:
        if existing.verification_status == RecruitmentAnnouncement.VerificationStatus.VERIFIED:
            if existing.priority < announcement.priority:
                raise ValidationError("a lower-priority announcement cannot replace the primary notice")
            if existing.priority == announcement.priority:
                old_time = existing.published_at or existing.created_at
                new_time = announcement.published_at or announcement.created_at
                if old_time >= new_time:
                    raise ValidationError("an older equal-priority announcement cannot replace the primary notice")
    for field_name, (parsed_value, excerpt, locator) in field_evidence.items():
        AnnouncementFieldEvidence.objects.create(
            batch=batch,
            announcement=announcement,
            field_name=field_name,
            excerpt=excerpt,
            locator=locator,
            parsed_value=parsed_value,
        )
    material_conflicts = {
        field_name
        for field_name, current_value in {
            "recruitment_type": batch.recruitment_type,
            "target_audience": batch.target_audience,
            "availability": batch.status,
        }.items()
        if existing is not None
        and existing.pk != announcement.pk
        and current_value != interpreted[field_name]
    }
    if material_conflicts and not confirm_field_conflicts:
        batch.announcement_admission = RecruitmentBatch.AnnouncementAdmission.PENDING
        batch.full_clean()
        batch.save(update_fields=["announcement_admission"])
        return batch
    batch.primary_announcement = announcement
    batch.announcement_admission = RecruitmentBatch.AnnouncementAdmission.ADMITTED
    batch.title = interpreted["title"]
    batch.recruitment_type = interpreted["recruitment_type"]
    batch.target_audience = interpreted["target_audience"]
    batch.status = interpreted["availability"]
    batch.full_clean()
    batch.save(update_fields=[
        "primary_announcement",
        "announcement_admission",
        "title",
        "recruitment_type",
        "target_audience",
        "status",
    ])
    if not announcement_evidence_is_complete(batch):
        raise ValidationError("saved announcement evidence did not pass integrity verification")
    return batch


@transaction.atomic
def create_announcement_only_batch(
    announcement: RecruitmentAnnouncement,
    *,
    identity_key: str,
    field_evidence: dict[str, tuple[str, str, str]],
    directions: list[dict[str, str]],
    application_evidence: str,
    application_url: str = "",
    application_email: str = "",
    application_miniprogram_name: str = "",
    application_miniprogram_path: str = "",
    application_instructions: str = "",
) -> RecruitmentBatch:
    """Create a formal-capable batch when the announcement is the only job source."""

    if announcement.source is None or not source_is_admitted(announcement.source):
        raise ValidationError("announcement-only batches require an admitted official source")
    if not directions:
        raise ValidationError("announcement-only batches require at least one explicit job direction")
    if application_miniprogram_name:
        invalid_channel = bool(application_email)
    else:
        invalid_channel = bool(application_url) == bool(application_email)
    if invalid_channel:
        raise ValidationError("provide exactly one application URL, email, or mini-program")
    if application_url and not source_permits_application_url(announcement.source, application_url):
        raise ValidationError("application URL is not permitted by the announcement source")
    batch = RecruitmentBatch.objects.create(
        organization=announcement.organization,
        source=announcement.source,
        identity_key=identity_key.strip(),
        title=field_evidence["title"][0],
        official_page_url=announcement.url or announcement.source.source_url,
        recruitment_type=field_evidence["recruitment_type"][0],
        target_audience=field_evidence["target_audience"][0],
        status=RecruitmentBatch.Status.ACTIVE,
        primary_announcement=announcement,
        announcement_admission=RecruitmentBatch.AnnouncementAdmission.PENDING,
    )
    admit_batch_with_announcement(batch, announcement, field_evidence=field_evidence)
    for index, direction in enumerate(directions, 1):
        title = str(direction.get("title") or "").strip()
        location = str(direction.get("location") or "").strip()
        excerpt = str(direction.get("excerpt") or "").strip()
        locator = str(direction.get("locator") or "").strip()
        if not all((title, location, excerpt, locator)):
            raise ValidationError("every job direction requires title, location, excerpt, and locator")
        position = RecruitmentPosition.objects.create(
            batch=batch,
            position_key=f"direction-{index}-{hashlib.sha256(title.encode('utf-8')).hexdigest()[:16]}",
            title=title,
            location_text=location,
            raw_text=excerpt,
            kind=RecruitmentPosition.Kind.DIRECTION,
        )
        for field_name, parsed_value in (
            ("direction_title", title),
            ("direction_location", location),
        ):
            AnnouncementFieldEvidence.objects.create(
                batch=batch,
                announcement=announcement,
                position=position,
                field_name=field_name,
                excerpt=excerpt,
                locator=locator,
                parsed_value=parsed_value,
            )
    link_type = (
        ApplicationLink.LinkType.EMAIL
        if application_email
        else ApplicationLink.LinkType.MINI_PROGRAM
        if application_miniprogram_name
        else ApplicationLink.LinkType.APPLICATION
    )
    channel = ApplicationLink(
        batch=batch,
        link_type=link_type,
        url=application_url,
        email=application_email,
        miniprogram_name=application_miniprogram_name,
        miniprogram_path=application_miniprogram_path,
        instructions=application_instructions,
        verification_evidence=application_evidence,
    )
    channel.full_clean()
    channel.save()
    if not announcement_direction_projection_is_complete(batch):
        raise ValidationError("announcement-only direction projection is incomplete")
    return batch


@dataclass(frozen=True)
class BatchSignature:
    organization_id: int
    target_audience: str
    recruitment_type: str
    named_program: str
    job_pool_key: str


def _normalize_signature_part(value: str) -> str:
    return re.sub(r"[\W_]+", "", value or "", flags=re.UNICODE).casefold()


def build_batch_signature(
    *,
    organization_id: int,
    target_audience: str,
    recruitment_type: str,
    named_program: str = "",
    job_pool_key: str = "",
) -> BatchSignature:
    return BatchSignature(
        organization_id,
        _normalize_signature_part(target_audience),
        recruitment_type,
        _normalize_signature_part(named_program),
        _normalize_signature_part(job_pool_key),
    )


def compare_batch_signatures(
    left: BatchSignature,
    right: BatchSignature,
) -> Literal["merge", "separate", "manual_review"]:
    if left.organization_id != right.organization_id:
        return "separate"
    if left.recruitment_type != right.recruitment_type:
        return "separate"
    if left == right and left.target_audience and left.job_pool_key:
        return "merge"
    return "manual_review"


def migration_preview_payload() -> dict:
    from radar.services.admission import source_is_admitted
    from radar.services.evidence import batch_projection_has_valid_evidence

    rows = []
    kept_companies: set[int] = set()
    pending_companies: set[int] = set()
    excluded_companies: set[int] = set()
    reused_positions = 0
    unmatched_positions = 0
    batches = RecruitmentBatch.objects.select_related(
        "organization", "primary_announcement"
    ).prefetch_related("positions").order_by("organization__name", "pk")
    for batch in batches:
        evidence_complete = announcement_evidence_is_complete(batch)
        projection_complete = (
            batch_projection_has_valid_evidence(
                batch,
                announcement_fields=True,
            )
            or announcement_direction_projection_is_complete(batch)
        )
        if batch.announcement_admission == RecruitmentBatch.AnnouncementAdmission.SUPERSEDED:
            outcome = "superseded"
            reusable = 0
            unmatched = batch.positions.count()
            unmatched_positions += unmatched
        elif (
            batch.announcement_admission == RecruitmentBatch.AnnouncementAdmission.ADMITTED
            and evidence_complete
            and projection_complete
            and batch.status == RecruitmentBatch.Status.ACTIVE
            and source_is_admitted(batch.source)
        ):
            outcome = "keep"
            kept_companies.add(batch.organization_id)
            reusable = batch.positions.filter(is_current=True).count()
            reused_positions += reusable
            unmatched = batch.positions.count() - reusable
            unmatched_positions += unmatched
        elif batch.primary_announcement_id:
            outcome = "pending"
            pending_companies.add(batch.organization_id)
            reusable = 0
            unmatched = batch.positions.count()
            unmatched_positions += unmatched
        else:
            outcome = "exclude"
            excluded_companies.add(batch.organization_id)
            reusable = 0
            unmatched = batch.positions.count()
            unmatched_positions += unmatched
        rows.append({
            "batch_id": batch.pk,
            "company": batch.organization.name,
            "title": batch.title,
            "outcome": outcome,
            "primary_announcement_id": batch.primary_announcement_id,
            "positions_reused": reusable,
            "positions_unmatched": unmatched,
        })
    return {
        "schema_version": "1",
        "summary": {
            "companies_kept": len(kept_companies),
            "companies_pending": len(pending_companies - kept_companies),
            "companies_excluded": len(excluded_companies - kept_companies - pending_companies),
            "batches_reviewed": len(rows),
            "positions_reused": reused_positions,
            "positions_unmatched": unmatched_positions,
        },
        "batches": rows,
    }


def migration_preview_digest(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@transaction.atomic
def record_migration_preview() -> tuple[dict, str]:
    payload = migration_preview_payload()
    digest = migration_preview_digest(payload)
    policy, _ = RecruitmentPolicy.objects.get_or_create(key="default")
    policy.preview_digest = digest
    policy.preview_generated_at = timezone.now()
    policy.save(update_fields=["preview_digest", "preview_generated_at"])
    return payload, digest


@transaction.atomic
def activate_announcement_gate(
    confirm_digest: str,
    *,
    actor_label: str = "local-owner",
) -> RecruitmentPolicy:
    payload = migration_preview_payload()
    current_digest = migration_preview_digest(payload)
    policy, _ = RecruitmentPolicy.objects.select_for_update().get_or_create(key="default")
    if policy.announcement_gate_enforced:
        raise ValidationError("announcement gate is already activated")
    if not policy.preview_digest or policy.preview_digest != current_digest:
        raise ValidationError("migration preview is missing or stale")
    if confirm_digest != current_digest:
        raise ValidationError("confirmation digest does not match the current preview")
    actor = actor_label.strip()
    if not actor:
        raise ValidationError("announcement gate activation requires an actor")
    ready_batch_ids = {
        row["batch_id"] for row in payload["batches"] if row["outcome"] == "keep"
    }
    pending_batch_ids = {
        row["batch_id"] for row in payload["batches"] if row["outcome"] == "pending"
    }
    excluded_batch_ids = {
        row["batch_id"] for row in payload["batches"] if row["outcome"] == "exclude"
    }
    RecruitmentBatch.objects.filter(pk__in=ready_batch_ids).update(
        announcement_admission=RecruitmentBatch.AnnouncementAdmission.ADMITTED
    )
    RecruitmentBatch.objects.filter(pk__in=pending_batch_ids).update(
        announcement_admission=RecruitmentBatch.AnnouncementAdmission.PENDING
    )
    RecruitmentBatch.objects.filter(pk__in=excluded_batch_ids).update(
        announcement_admission=RecruitmentBatch.AnnouncementAdmission.EXCLUDED
    )
    policy.announcement_gate_enforced = True
    policy.activated_at = timezone.now()
    policy.save(update_fields=["announcement_gate_enforced", "activated_at"])
    RecruitmentPolicyEvent.objects.create(
        policy=policy,
        event_type=RecruitmentPolicyEvent.EventType.ACTIVATED,
        actor_label=actor,
        preview_digest=current_digest,
    )
    return policy
