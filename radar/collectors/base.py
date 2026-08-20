from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from radar.models import OfficialSource


@dataclass(frozen=True)
class FieldEvidenceValue:
    raw_value: str
    locator: str
    parsed_value: str


@dataclass(frozen=True)
class FetchedPage:
    canonical_url: str
    body: str
    content_hash: str
    http_status: int
    etag: str | None
    not_modified: bool = False


@dataclass(frozen=True)
class PositionCandidate:
    title: str
    location_text: str
    raw_text: str
    application_url: str | None
    locator: str = ""
    application_locator: str = ""
    position_key: str = ""
    field_evidence: dict[str, FieldEvidenceValue] = field(default_factory=dict)


@dataclass(frozen=True)
class NoticeCandidate:
    title: str
    official_notice_url: str
    recruitment_type: str
    target_audience: str
    published_on: date | None
    deadline: date | None
    withdrawn: bool
    evidence_excerpt: str
    positions: tuple[PositionCandidate, ...]
    field_locators: dict[str, str] = field(default_factory=dict)
    identity_key: str = ""
    field_evidence: dict[str, FieldEvidenceValue] = field(default_factory=dict)
    positions_complete: bool = False


class SourceAdapter(Protocol):
    def fetch(self, source: OfficialSource) -> FetchedPage: ...
    def extract(self, source: OfficialSource, page: FetchedPage) -> list[NoticeCandidate]: ...
