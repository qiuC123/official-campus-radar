from datetime import date

from radar.collectors.base import FieldEvidenceValue, RecruitmentBatchCandidate, PositionCandidate
from radar.models import OfficialSource, Organization, RecruitmentBatch, SourceVersion
from radar.services.admission import transition_source
from radar.services.publication import publish_candidates


def valid_html_parser_config() -> dict[str, str]:
    return {
        "notice_selector": "article.job",
        "notice_id_attribute": "data-notice-id",
        "position_id_attribute": "data-position-id",
        "notice_url_selector": "a.notice",
        "title_selector": "h2",
        "recruitment_type_selector": ".type",
        "target_audience_selector": ".audience",
        "published_on_selector": ".published",
        "deadline_selector": ".deadline",
        "position_title_selector": ".position-title",
        "location_selector": ".location",
        "excerpt_selector": ".description",
    }


def field_evidence(raw: str, locator: str, parsed: str | None = None) -> FieldEvidenceValue:
    return FieldEvidenceValue(raw, locator, raw if parsed is None else parsed)


def create_enabled_source(
    *,
    name: str = "Example Org",
    host: str = "official.test",
    path: str = "/careers",
) -> OfficialSource:
    organization = Organization.objects.create(
        name=name,
        company_type="internet",
        industry="tech",
        official_domain=host,
    )
    source = OfficialSource.objects.create(
        organization=organization,
        source_type="website",
        source_url=f"https://{host}{path}",
        admission_evidence="candidate note",
        parser_config=valid_html_parser_config(),
    )
    transition_source(
        source,
        to_state="verified",
        actor_label="test-owner",
        reason="official domain verified",
        evidence="test fixture review",
    )
    transition_source(
        source,
        to_state="enabled",
        actor_label="test-owner",
        reason="offline parser accepted",
        evidence="test fixture passed",
    )
    source.refresh_from_db()
    return source


def complete_candidate(
    source: OfficialSource,
    *,
    identity_key: str = "batch-2027",
    title: str = "2027 Campus",
    location: str = "北京",
    position_key: str = "position-1",
    application_url: str | None = None,
    official_page_url: str | None = None,
    withdrawn: bool = False,
) -> RecruitmentBatchCandidate:
    base = source.source_url.rstrip("/")
    url = official_page_url or f"{base}/batches/{identity_key}"
    position_evidence = {
        "position_title": field_evidence("Engineer", f"#{position_key} .title"),
        "location": field_evidence(location, f"#{position_key} .location"),
        "raw_text": field_evidence(
            f"Engineer {location}", f"#{position_key} .description"
        ),
    }
    if application_url:
        position_evidence["application_link"] = field_evidence(
            application_url, f"#{position_key} a.apply@href"
        )
    return RecruitmentBatchCandidate(
        title=title,
        official_page_url=url,
        recruitment_type="校园招聘",
        target_audience="2027届",
        published_on=date(2026, 8, 1),
        deadline=date(2026, 12, 31),
        withdrawn=withdrawn,
        evidence_excerpt="fixture context",
        positions=(
            PositionCandidate(
                "Engineer",
                location,
                f"Engineer {location}",
                application_url,
                position_key=position_key,
                field_evidence=position_evidence,
            ),
        ),
        identity_key=identity_key,
        field_evidence={
            "title": field_evidence(title, f"#{identity_key} h2"),
            "recruitment_type": field_evidence(
                "校园招聘", f"#{identity_key} .type", "campus_recruitment"
            ),
            "target_audience": field_evidence("2027届", f"#{identity_key} .audience"),
            "published_on": field_evidence("2026-08-01", f"#{identity_key} .published"),
            "deadline": field_evidence("2026-12-31", f"#{identity_key} .deadline"),
            "official_page_url": field_evidence(url, f"#{identity_key} a.notice@href"),
        },
        positions_complete=True,
    )


def publish_formal_notice(
    source: OfficialSource,
    *,
    identity_key: str = "batch-2027",
    title: str = "2027 Campus",
    location: str = "北京",
    status: str = RecruitmentBatch.Status.ACTIVE,
    hash_character: str = "a",
) -> RecruitmentBatch:
    version = SourceVersion.objects.create(
        source=source,
        canonical_url=source.source_url,
        content_hash=hash_character * 64,
        is_applied=True,
    )
    result = publish_candidates(
        source,
        [
            complete_candidate(
                source,
                identity_key=identity_key,
                title=title,
                location=location,
            )
        ],
        version,
    )[0]
    batch = RecruitmentBatch.objects.get(pk=result.batch_id)
    if status != RecruitmentBatch.Status.ACTIVE:
        batch.status = status
        batch.save(update_fields=["status"])
    return batch
