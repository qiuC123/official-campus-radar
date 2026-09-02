from __future__ import annotations

import hashlib
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Callable, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from django.db import transaction
from django.utils import timezone

from radar.models import (
    AnnouncementDiscoveryCandidate,
    AnnouncementDiscoveryObservation,
    AnnouncementDiscoveryOrganizationRun,
    AnnouncementDiscoveryProviderAttempt,
    AnnouncementDiscoveryRun,
    OfficialSource,
    Organization,
    RecruitmentAnnouncement,
)
from radar.services.normalization import normalize_identity_text


EXA_SEARCH_URL = "https://api.exa.ai/search"
MAX_EXA_RESPONSE_BYTES = 1024 * 1024
MAX_HIGHLIGHT_CHARACTERS = 1000
MAX_RESULTS_PER_QUERY = 10
MAX_BATCH_SECONDS = 600
MAX_CODEX_TIMEOUT_SECONDS = 180
MAX_COMPANIES_PER_RUN = 8
MAX_CODEX_FALLBACK_COMPANIES = 3
TRACKING_QUERY_KEYS = {"gclid", "fbclid"}
RECRUITMENT_TERMS = (
    "校园招聘",
    "校招",
    "秋招",
    "春招",
    "补录",
    "实习",
    "应届",
    "graduate",
    "campus",
    "intern",
)
GENERIC_RECRUITING_PATHS = {
    "/",
    "/careers",
    "/career",
    "/jobs",
    "/join-us",
    "/joinus",
    "/recruitment",
}
AGGREGATOR_HOST_SUFFIXES = (
    "nowcoder.com",
    "zhipin.com",
    "liepin.com",
    "jobui.com",
    "yingjiesheng.com",
)
ATS_HOST_SUFFIXES = (
    "mokahr.com",
    "zhiye.com",
    "hotjob.cn",
    "51job.com",
)
YEAR_AUDIENCE = re.compile(r"20\d{2}届")
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?key|cookie|authorization|password|secret|token)\s*[:=]"
)


class ExaDiscoveryError(RuntimeError):
    def __init__(self, code: str, *, fallback_allowed: bool):
        super().__init__(code)
        self.code = code
        self.fallback_allowed = fallback_allowed


@dataclass(frozen=True)
class SearchCriteria:
    audiences: tuple[str, ...]
    recruitment_types: tuple[str, ...]
    published_after: date
    published_before: date

    def __post_init__(self):
        if not self.audiences or not self.recruitment_types:
            raise ValueError("search criteria require audiences and recruitment types")
        if len(self.audiences) * len(self.recruitment_types) > 4:
            raise ValueError("search criteria define more than four intents")
        if self.published_after > self.published_before:
            raise ValueError("published_after must not be after published_before")
        for value in (*self.audiences, *self.recruitment_types):
            if not value.strip() or len(value.strip()) > 100:
                raise ValueError("search criteria contain an invalid value")

    def as_dict(self) -> dict:
        return {
            "audiences": list(self.audiences),
            "recruitment_types": list(self.recruitment_types),
            "published_after": self.published_after.isoformat(),
            "published_before": self.published_before.isoformat(),
        }


@dataclass(frozen=True)
class SearchPlan:
    organization_id: int
    intent_key: str
    query: str
    include_domains: tuple[str, ...]
    published_after: date
    published_before: date

    @property
    def request_key(self) -> str:
        payload = json.dumps(
            [
                self.organization_id,
                self.intent_key,
                self.query,
                self.include_domains,
                self.published_after.isoformat(),
                self.published_before.isoformat(),
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DiscoveryObservation:
    intent_key: str
    query: str
    url: str
    title_hint: str
    snippet: str
    backend_date_hint: str
    provider: str
    rank: int
    result_id: str
    discovered_at: object = field(default_factory=timezone.now)
    request_key: str = ""


@dataclass(frozen=True)
class NormalizedCandidateUrl:
    fetch_url: str
    identity_url: str


@dataclass(frozen=True)
class ProviderAttempt:
    provider: str
    intent_key: str
    query: str
    status: str
    request_key: str = ""
    request_id: str = ""
    duration_ms: int = 0
    result_count: int = 0
    cost_dollars: float | None = None
    error_code: str = ""


@dataclass(frozen=True)
class ProviderQueryResult:
    plan: SearchPlan
    observations: tuple[DiscoveryObservation, ...]
    attempt: ProviderAttempt

    @classmethod
    def success(
        cls,
        plan: SearchPlan,
        observations: Iterable[DiscoveryObservation],
        *,
        request_id: str = "",
        duration_ms: int = 0,
        cost_dollars: float | None = None,
    ) -> "ProviderQueryResult":
        values = tuple(observations)
        return cls(
            plan,
            values,
            ProviderAttempt(
                provider="exa",
                intent_key=plan.intent_key,
                query=plan.query,
                status="success" if values else "empty",
                request_key=plan.request_key,
                request_id=request_id,
                duration_ms=duration_ms,
                result_count=len(values),
                cost_dollars=cost_dollars,
            ),
        )

    @classmethod
    def empty(cls, plan: SearchPlan) -> "ProviderQueryResult":
        return cls.success(plan, ())

    @property
    def status(self) -> str:
        return self.attempt.status

    @property
    def request_id(self) -> str:
        return self.attempt.request_id

    @property
    def cost_dollars(self) -> float | None:
        return self.attempt.cost_dollars


@dataclass(frozen=True)
class MergedCandidate:
    fetch_url: str
    identity_url: str
    title_hint: str
    backend_date_hint: str
    observations: tuple[DiscoveryObservation, ...]
    route_state: str = "unrouted"
    source_kind: str = RecruitmentAnnouncement.SourceKind.WEBSITE
    rejection_code: str = ""
    qualified: bool = False


@dataclass(frozen=True)
class CompanyDiscoveryResult:
    organization: Organization
    status: str
    candidates: tuple[MergedCandidate, ...]
    attempts: tuple[ProviderAttempt, ...]
    fallback_reason: str = ""
    error_code: str = ""


@dataclass(frozen=True)
class DiscoveryBatchResult:
    criteria: SearchCriteria
    status: str
    companies: tuple[CompanyDiscoveryResult, ...]
    started_at: object
    completed_at: object


def _clean_bounded_text(value: object, maximum: int) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()[:maximum]


def normalize_discovery_url(value: str) -> NormalizedCandidateUrl:
    raw = str(value or "").strip()
    parts = urlsplit(raw)
    if parts.scheme.casefold() != "https" or not parts.hostname:
        raise ValueError("candidate URL must be absolute HTTPS")
    if parts.username or parts.password:
        raise ValueError("candidate URL must not contain userinfo")
    try:
        port = parts.port
    except ValueError as error:
        raise ValueError("candidate URL has an invalid port") from error
    if port not in {None, 443}:
        raise ValueError("candidate URL must use HTTPS port 443")
    try:
        host = parts.hostname.rstrip(".").encode("idna").decode("ascii").casefold()
    except UnicodeError as error:
        raise ValueError("candidate URL has an invalid host") from error
    path = parts.path or "/"
    fetch_url = urlunsplit(("https", host, path, parts.query, ""))
    identity_pairs = [
        (key, item)
        for key, item in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_")
        and key.casefold() not in TRACKING_QUERY_KEYS
    ]
    identity_url = urlunsplit(("https", host, path, urlencode(identity_pairs), ""))
    return NormalizedCandidateUrl(fetch_url, identity_url)


def _organization_names(organization: Organization) -> tuple[str, ...]:
    values = [organization.name, *list(organization.aliases or [])]
    if organization.pk:
        values.extend(
            organization.normalized_aliases.order_by("pk").values_list("alias", flat=True)
        )
    return tuple(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def _admitted_source_hosts(organization: Organization) -> tuple[tuple[str, str], ...]:
    values = []
    if organization.official_domain:
        values.append((organization.official_domain.casefold().rstrip("."), "website"))
    sources = organization.official_sources.filter(
        admission_state__in={
            OfficialSource.AdmissionState.VERIFIED,
            OfficialSource.AdmissionState.ENABLED,
        },
        is_verified=True,
    )
    for source in sources:
        for raw_url in (source.source_url, source.official_entrypoint_url):
            host = (urlsplit(raw_url).hostname or "").casefold().rstrip(".")
            if host:
                values.append((host, source.source_type))
    return tuple(dict.fromkeys(values))


def _host_matches(host: str, known: str) -> bool:
    return host == known


def rank_discovery_candidates(
    candidates: Iterable[MergedCandidate],
) -> tuple[MergedCandidate, ...]:
    route_priority = {
        "known_official": 0,
        "known_ats": 0,
        "source_identity_review_required": 1,
        "rejected": 2,
        "unrouted": 3,
    }
    provider_priority = {"exa": 0, "codex_web_search": 1, "known_source": 2}

    def key(candidate: MergedCandidate):
        observations = candidate.observations
        best_observation = min(
            observations,
            key=lambda item: (
                provider_priority.get(item.provider, 9),
                item.rank,
                item.result_id,
            ),
        )
        return (
            0 if candidate.qualified else 1,
            route_priority.get(candidate.route_state, 9),
            provider_priority.get(best_observation.provider, 9),
            best_observation.rank,
            candidate.identity_url,
        )

    return tuple(sorted(candidates, key=key))


class AnnouncementSearchPlanner:
    def __init__(self, *, max_queries_per_company: int = 4):
        if not 1 <= max_queries_per_company <= 4:
            raise ValueError("max_queries_per_company must be between 1 and 4")
        self.max_queries_per_company = max_queries_per_company

    def plan(
        self,
        organization: Organization,
        criteria: SearchCriteria,
    ) -> tuple[SearchPlan, ...]:
        names = _organization_names(organization)
        names_text = " OR ".join(names[:3])
        domains = tuple(dict.fromkeys(host for host, _kind in _admitted_source_hosts(organization)))
        broad_plans = []
        domain_plans = []
        for audience in criteria.audiences:
            for recruitment_type in criteria.recruitment_types:
                intent_payload = json.dumps(
                    [organization.pk, audience, recruitment_type, criteria.as_dict()],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                intent_key = hashlib.sha256(intent_payload.encode("utf-8")).hexdigest()[:32]
                query = _clean_bounded_text(
                    f"{names_text} {audience} {recruitment_type} 校园招聘 官方 公告",
                    500,
                )
                broad_plans.append(SearchPlan(
                    organization_id=organization.pk,
                    intent_key=intent_key,
                    query=query,
                    include_domains=(),
                    published_after=criteria.published_after,
                    published_before=criteria.published_before,
                ))
                if domains:
                    domain_plans.append(SearchPlan(
                        organization_id=organization.pk,
                        intent_key=intent_key,
                        query=query,
                        include_domains=domains,
                        published_after=criteria.published_after,
                        published_before=criteria.published_before,
                    ))
        return tuple((broad_plans + domain_plans)[: self.max_queries_per_company])


class ExaDiscoveryClient:
    def __init__(
        self,
        *,
        api_key: str,
        transport=None,
        sleeper: Callable[[float], None] = time.sleep,
        max_retries: int = 1,
        max_response_bytes: int = MAX_EXA_RESPONSE_BYTES,
    ):
        if not str(api_key or "").strip():
            raise ExaDiscoveryError("API_KEY_MISSING", fallback_allowed=False)
        self.api_key = str(api_key).strip()
        self.transport = transport or requests.Session()
        self.transport.trust_env = False
        self.sleeper = sleeper
        self.max_retries = max_retries
        self.max_response_bytes = max_response_bytes

    def _request_body(self, plan: SearchPlan) -> dict:
        body = {
            "query": plan.query,
            "type": "auto",
            "numResults": MAX_RESULTS_PER_QUERY,
            "moderation": True,
            "startPublishedDate": f"{plan.published_after.isoformat()}T00:00:00.000Z",
            "endPublishedDate": f"{plan.published_before.isoformat()}T23:59:59.999Z",
            "contents": {
                "highlights": {"maxCharacters": MAX_HIGHLIGHT_CHARACTERS},
            },
        }
        if plan.include_domains:
            body["includeDomains"] = list(plan.include_domains)
        return body

    def _read_response(self, response) -> bytes:
        chunks = []
        size = 0
        try:
            for chunk in response.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                size += len(chunk)
                if size > self.max_response_bytes:
                    raise ExaDiscoveryError("RESPONSE_TOO_LARGE", fallback_allowed=False)
                chunks.append(chunk)
        finally:
            response.close()
        return b"".join(chunks)

    def search(self, plan: SearchPlan) -> ProviderQueryResult:
        started = time.monotonic()
        retries = 0
        while True:
            try:
                response = self.transport.post(
                    EXA_SEARCH_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json=self._request_body(plan),
                    timeout=(5, 20),
                    allow_redirects=False,
                    stream=True,
                )
            except requests.Timeout as error:
                if retries < self.max_retries:
                    retries += 1
                    continue
                raise ExaDiscoveryError("TIMEOUT", fallback_allowed=True) from error
            except requests.ConnectionError as error:
                if retries < self.max_retries:
                    retries += 1
                    continue
                raise ExaDiscoveryError("NETWORK_ERROR", fallback_allowed=True) from error

            status = int(response.status_code)
            if status in {429} or 500 <= status <= 599:
                response.close()
                if retries < self.max_retries:
                    retries += 1
                    retry_after = response.headers.get("Retry-After", "0")
                    try:
                        delay = min(10, max(0, int(retry_after)))
                    except (TypeError, ValueError):
                        delay = 0
                    if delay:
                        self.sleeper(delay)
                    continue
                code = "RATE_LIMITED" if status == 429 else "SERVER_ERROR"
                raise ExaDiscoveryError(code, fallback_allowed=True)
            if status in {401, 403}:
                response.close()
                raise ExaDiscoveryError("AUTH_INVALID", fallback_allowed=False)
            if status != 200:
                response.close()
                raise ExaDiscoveryError("HTTP_CONTRACT_ERROR", fallback_allowed=False)

            raw = self._read_response(response)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ExaDiscoveryError("INVALID_JSON", fallback_allowed=False) from error
            if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                raise ExaDiscoveryError("INVALID_RESPONSE_SCHEMA", fallback_allowed=False)
            raw_results = payload["results"]
            if len(raw_results) > MAX_RESULTS_PER_QUERY:
                raise ExaDiscoveryError("RESULT_LIMIT_EXCEEDED", fallback_allowed=False)
            observations = []
            for rank, item in enumerate(raw_results, 1):
                if not isinstance(item, dict):
                    raise ExaDiscoveryError("INVALID_RESPONSE_SCHEMA", fallback_allowed=False)
                url = str(item.get("url") or "").strip()
                try:
                    normalize_discovery_url(url)
                except ValueError:
                    continue
                title = _clean_bounded_text(item.get("title"), 500)
                highlights = item.get("highlights") or []
                if not isinstance(highlights, list):
                    raise ExaDiscoveryError("INVALID_RESPONSE_SCHEMA", fallback_allowed=False)
                snippet = _clean_bounded_text(" ".join(str(value) for value in highlights), 1000)
                result_id = _clean_bounded_text(item.get("id"), 128)
                if not result_id:
                    result_id = hashlib.sha256(url.encode("utf-8")).hexdigest()
                observations.append(DiscoveryObservation(
                    intent_key=plan.intent_key,
                    query=plan.query,
                    url=url,
                    title_hint=title,
                    snippet=snippet,
                    backend_date_hint=_clean_bounded_text(item.get("publishedDate"), 64),
                    provider="exa",
                    rank=rank,
                    result_id=result_id,
                    request_key=plan.request_key,
                ))
            request_id = _clean_bounded_text(payload.get("requestId"), 128)
            if not request_id:
                request_id = _clean_bounded_text(response.headers.get("x-request-id"), 128)
            cost_value = payload.get("costDollars")
            if isinstance(cost_value, dict):
                cost_value = cost_value.get("total")
            try:
                cost = float(cost_value) if cost_value is not None else None
            except (TypeError, ValueError):
                cost = None
            duration_ms = max(0, int((time.monotonic() - started) * 1000))
            return ProviderQueryResult.success(
                plan,
                observations,
                request_id=request_id,
                duration_ms=duration_ms,
                cost_dollars=cost,
            )


def build_exa_client_from_environment(
    environ: dict[str, str] | None = None,
    **kwargs,
) -> ExaDiscoveryClient:
    values = os.environ if environ is None else environ
    return ExaDiscoveryClient(api_key=values.get("EXA_API_KEY", ""), **kwargs)


def merge_observations(
    observations: Iterable[DiscoveryObservation],
) -> tuple[MergedCandidate, ...]:
    grouped: dict[str, list[tuple[NormalizedCandidateUrl, DiscoveryObservation]]] = {}
    order = []
    for observation in observations:
        try:
            normalized = normalize_discovery_url(observation.url)
        except ValueError:
            continue
        if normalized.identity_url not in grouped:
            grouped[normalized.identity_url] = []
            order.append(normalized.identity_url)
        grouped[normalized.identity_url].append((normalized, observation))
    merged = []
    for identity_url in order:
        values = grouped[identity_url]
        provider_priority = {"exa": 0, "codex_web_search": 1, "known_source": 2}
        values.sort(key=lambda value: (
            provider_priority.get(value[1].provider, 9),
            value[1].rank,
            value[1].result_id,
        ))
        first = values[0][0]
        obs = tuple(value[1] for value in values)
        merged.append(MergedCandidate(
            fetch_url=first.fetch_url,
            identity_url=identity_url,
            title_hint=next((item.title_hint for item in obs if item.title_hint), ""),
            backend_date_hint=next(
                (item.backend_date_hint for item in obs if item.backend_date_hint),
                "",
            ),
            observations=obs,
        ))
    return tuple(merged)


def parse_discovery_result_document(
    raw: str | bytes | dict,
    organizations: Iterable[Organization],
) -> DiscoveryBatchResult:
    if isinstance(raw, dict):
        payload = raw
        encoded = json.dumps(raw, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    else:
        encoded = raw if isinstance(raw, bytes) else raw.encode("utf-8")
        try:
            payload = json.loads(encoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("candidate batch v2 must be UTF-8 JSON") from error
    if len(encoded) > 2 * 1024 * 1024 or _CREDENTIAL_ASSIGNMENT.search(
        encoded.decode("utf-8", errors="ignore")
    ):
        raise ValueError("candidate batch v2 contains unsafe or oversized data")
    expected_top = {
        "schema_version",
        "ok",
        "status",
        "recorded_run_id",
        "criteria",
        "companies",
    }
    if not isinstance(payload, dict) or set(payload) != expected_top:
        raise ValueError("candidate batch v2 has invalid top-level fields")
    if payload.get("schema_version") != "2":
        raise ValueError("unsupported candidate batch v2 schema")
    criteria_value = payload.get("criteria")
    if not isinstance(criteria_value, dict) or set(criteria_value) != {
        "audiences",
        "recruitment_types",
        "published_after",
        "published_before",
    }:
        raise ValueError("candidate batch v2 has invalid criteria")
    if (
        not isinstance(criteria_value["audiences"], list)
        or not isinstance(criteria_value["recruitment_types"], list)
        or any(not isinstance(value, str) for value in criteria_value["audiences"])
        or any(
            not isinstance(value, str)
            for value in criteria_value["recruitment_types"]
        )
    ):
        raise ValueError("candidate batch v2 criteria lists must contain strings")
    try:
        criteria = SearchCriteria(
            audiences=tuple(criteria_value["audiences"]),
            recruitment_types=tuple(criteria_value["recruitment_types"]),
            published_after=date.fromisoformat(criteria_value["published_after"]),
            published_before=date.fromisoformat(criteria_value["published_before"]),
        )
    except (TypeError, ValueError) as error:
        raise ValueError("candidate batch v2 has invalid criteria values") from error
    by_name = {organization.name: organization for organization in organizations}
    companies_value = payload.get("companies")
    if not isinstance(companies_value, list) or len(companies_value) > MAX_COMPANIES_PER_RUN:
        raise ValueError("candidate batch v2 has invalid companies")
    company_results = []
    company_fields = {
        "company",
        "status",
        "fallback_reason",
        "error_code",
        "attempts",
        "candidates",
    }
    attempt_fields = {
        "provider",
        "status",
        "intent_key",
        "query",
        "request_key",
        "request_id",
        "duration_ms",
        "result_count",
        "cost_dollars",
        "error_code",
    }
    candidate_fields = {
        "fetch_url",
        "identity_url",
        "title_hint",
        "backend_date_hint",
        "route_state",
        "qualified",
        "rejection_code",
        "observations",
    }
    observation_fields = {
        "query",
        "provider",
        "rank",
        "result_id",
        "intent_key",
        "request_key",
        "discovered_at",
    }
    for company_value in companies_value:
        if not isinstance(company_value, dict) or set(company_value) != company_fields:
            raise ValueError("candidate batch v2 has invalid company fields")
        organization = by_name.get(str(company_value.get("company") or ""))
        if organization is None:
            raise ValueError("candidate batch v2 company is not selected")
        attempts = []
        if not isinstance(company_value["attempts"], list):
            raise ValueError("candidate batch v2 attempts must be a list")
        for attempt in company_value["attempts"]:
            if not isinstance(attempt, dict) or set(attempt) != attempt_fields:
                raise ValueError("candidate batch v2 has invalid attempt fields")
            provider = str(attempt.get("provider") or "")
            if provider not in {"exa", "codex_web_search", "known_source"}:
                raise ValueError("candidate batch v2 has an invalid provider")
            attempt_status = _clean_bounded_text(attempt.get("status"), 24)
            if attempt_status not in {
                "success",
                "empty",
                "transient_error",
                "permanent_error",
                "skipped",
            }:
                raise ValueError("candidate batch v2 has an invalid attempt status")
            intent_key = _clean_bounded_text(attempt.get("intent_key"), 64)
            query = _clean_bounded_text(attempt.get("query"), 500)
            request_key = _clean_bounded_text(attempt.get("request_key"), 64)
            if not intent_key or not query or not request_key:
                raise ValueError("candidate batch v2 attempt identity is incomplete")
            try:
                duration_ms = int(attempt["duration_ms"])
                result_count = int(attempt["result_count"])
            except (TypeError, ValueError) as error:
                raise ValueError("candidate batch v2 has invalid attempt counts") from error
            attempts.append(ProviderAttempt(
                provider=provider,
                intent_key=intent_key,
                query=query,
                status=attempt_status,
                request_key=request_key,
                request_id=_clean_bounded_text(attempt.get("request_id"), 128),
                duration_ms=max(0, duration_ms),
                result_count=max(0, result_count),
                cost_dollars=attempt.get("cost_dollars"),
                error_code=_clean_bounded_text(attempt.get("error_code"), 64),
            ))
        raw_observations = []
        if not isinstance(company_value["candidates"], list):
            raise ValueError("candidate batch v2 candidates must be a list")
        for candidate in company_value["candidates"]:
            if not isinstance(candidate, dict) or set(candidate) != candidate_fields:
                raise ValueError("candidate batch v2 has invalid candidate fields")
            normalized = normalize_discovery_url(candidate.get("fetch_url"))
            if normalized.identity_url != candidate.get("identity_url"):
                raise ValueError("candidate batch v2 identity URL does not match fetch URL")
            if not isinstance(candidate["observations"], list):
                raise ValueError("candidate batch v2 observations must be a list")
            for observation in candidate["observations"]:
                if not isinstance(observation, dict) or set(observation) != observation_fields:
                    raise ValueError("candidate batch v2 has invalid observation fields")
                provider = str(observation.get("provider") or "")
                if provider not in {"exa", "codex_web_search", "known_source"}:
                    raise ValueError("candidate batch v2 has an invalid provider")
                rank = observation.get("rank")
                if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
                    raise ValueError("candidate batch v2 has an invalid rank")
                result_id = _clean_bounded_text(observation.get("result_id"), 128)
                if not result_id:
                    raise ValueError("candidate batch v2 observation has no result ID")
                try:
                    discovered_at = datetime.fromisoformat(
                        str(observation.get("discovered_at") or "")
                    )
                except ValueError as error:
                    raise ValueError("candidate batch v2 has invalid discovered_at") from error
                if timezone.is_naive(discovered_at):
                    discovered_at = timezone.make_aware(discovered_at)
                raw_observations.append(DiscoveryObservation(
                    intent_key=_clean_bounded_text(observation.get("intent_key"), 64),
                    query=_clean_bounded_text(observation.get("query"), 500),
                    url=normalized.fetch_url,
                    title_hint=_clean_bounded_text(candidate.get("title_hint"), 500),
                    snippet="",
                    backend_date_hint=_clean_bounded_text(
                        candidate.get("backend_date_hint"), 64
                    ),
                    provider=provider,
                    rank=rank,
                    result_id=result_id,
                    discovered_at=discovered_at,
                    request_key=_clean_bounded_text(observation.get("request_key"), 64),
                ))
        routed = tuple(
            route_candidate(organization, item, criteria=criteria)
            for item in merge_observations(raw_observations)
        )
        company_status = str(company_value.get("status") or "")
        if company_status not in {"complete", "degraded", "failed"}:
            raise ValueError("candidate batch v2 has invalid company status")
        company_results.append(CompanyDiscoveryResult(
            organization=organization,
            status=company_status,
            candidates=routed,
            attempts=tuple(attempts),
            fallback_reason=_clean_bounded_text(company_value.get("fallback_reason"), 64),
            error_code=_clean_bounded_text(company_value.get("error_code"), 64),
        ))
    if (
        len(company_results) != len(by_name)
        or {item.organization.name for item in company_results} != set(by_name)
    ):
        raise ValueError("candidate batch v2 must contain every selected company exactly once")
    batch_status = str(payload.get("status") or "")
    if batch_status not in {"complete", "partial", "failed"}:
        raise ValueError("candidate batch v2 has invalid batch status")
    now = timezone.now()
    return DiscoveryBatchResult(
        criteria=criteria,
        status=batch_status,
        companies=tuple(company_results),
        started_at=now,
        completed_at=now,
    )


def _host_has_suffix(host: str, suffixes: Iterable[str]) -> bool:
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in suffixes)


def route_candidate(
    organization: Organization,
    candidate: MergedCandidate,
    *,
    criteria: SearchCriteria,
) -> MergedCandidate:
    host = (urlsplit(candidate.identity_url).hostname or "").casefold()
    metadata = normalize_identity_text(
        " ".join(
            [
                candidate.title_hint,
                *(item.snippet for item in candidate.observations),
            ]
        )
    )
    names = tuple(normalize_identity_text(value) for value in _organization_names(organization))
    admitted = _admitted_source_hosts(organization)
    matched_types = {
        source_type
        for known_host, source_type in admitted
        if _host_matches(host, known_host)
    }
    company_signal = bool(matched_types) or any(name and name in metadata for name in names)
    recruitment_signal = any(term.casefold() in metadata for term in RECRUITMENT_TERMS)
    years = set(YEAR_AUDIENCE.findall(metadata))
    target_years = {
        value
        for audience in criteria.audiences
        for value in YEAR_AUDIENCE.findall(audience)
    }
    conflicting_scope = bool(years and target_years and years.isdisjoint(target_years))
    path = urlsplit(candidate.identity_url).path.rstrip("/").casefold() or "/"
    generic = path in GENERIC_RECRUITING_PATHS and not years and not any(
        term.casefold() in metadata
        for term in ("秋招", "春招", "补录", "实习", "campus", "graduate")
    )

    if _host_has_suffix(host, AGGREGATOR_HOST_SUFFIXES):
        route_state = "rejected"
        source_kind = RecruitmentAnnouncement.SourceKind.WEBSITE
        rejection_code = "THIRD_PARTY_AGGREGATOR"
    elif matched_types:
        is_ats = bool(matched_types & {
            OfficialSource.SourceType.ATS,
            OfficialSource.SourceType.API,
        })
        route_state = "known_ats" if is_ats else "known_official"
        source_kind = (
            RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM
            if is_ats
            else RecruitmentAnnouncement.SourceKind.WEBSITE
        )
        rejection_code = ""
    elif _host_has_suffix(host, ATS_HOST_SUFFIXES) and company_signal and recruitment_signal:
        route_state = "source_identity_review_required"
        source_kind = RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM
        rejection_code = "SOURCE_IDENTITY_REVIEW_REQUIRED"
    else:
        route_state = "rejected"
        source_kind = RecruitmentAnnouncement.SourceKind.WEBSITE
        rejection_code = "UNROUTABLE_SOURCE"

    qualified = (
        route_state in {"known_official", "known_ats"}
        and company_signal
        and recruitment_signal
        and not conflicting_scope
        and not generic
    )
    return replace(
        candidate,
        route_state=route_state,
        source_kind=source_kind,
        rejection_code=rejection_code,
        qualified=qualified,
    )


@dataclass
class _CompanyExaPhase:
    organization: Organization
    plans: tuple[SearchPlan, ...]
    observations: tuple[DiscoveryObservation, ...]
    attempts: tuple[ProviderAttempt, ...]
    candidates: tuple[MergedCandidate, ...]
    missing_intents: tuple[str, ...]
    had_transient_error: bool = False
    permanent_error: str = ""


class AnnouncementDiscoveryOrchestrator:
    def __init__(
        self,
        *,
        exa_client,
        codex_searcher: Callable | None,
        planner: AnnouncementSearchPlanner | None = None,
        max_workers: int = 2,
        max_codex_fallback_companies: int = MAX_CODEX_FALLBACK_COMPANIES,
        max_batch_seconds: int = MAX_BATCH_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        latency_clock: Callable[[], float] = time.monotonic,
    ):
        self.exa_client = exa_client
        self.codex_searcher = codex_searcher
        self.planner = planner or AnnouncementSearchPlanner()
        self.max_workers = max_workers
        self.max_codex_fallback_companies = max_codex_fallback_companies
        self.max_batch_seconds = max_batch_seconds
        self.clock = clock
        self.latency_clock = latency_clock

    def _exa_phase(
        self,
        organization: Organization,
        criteria: SearchCriteria,
    ) -> _CompanyExaPhase:
        plans = self.planner.plan(organization, criteria)
        observations = []
        attempts = []
        transient = False
        for plan in plans:
            try:
                result = self.exa_client.search(plan)
            except ExaDiscoveryError as error:
                attempts.append(ProviderAttempt(
                    provider="exa",
                    intent_key=plan.intent_key,
                    query=plan.query,
                    status=("transient_error" if error.fallback_allowed else "permanent_error"),
                    request_key=plan.request_key,
                    error_code=error.code,
                ))
                if not error.fallback_allowed:
                    return _CompanyExaPhase(
                        organization,
                        plans,
                        tuple(observations),
                        tuple(attempts),
                        (),
                        (),
                        permanent_error=error.code,
                    )
                transient = True
                continue
            observations.extend(result.observations)
            attempts.append(result.attempt)
        candidates = rank_discovery_candidates(
            route_candidate(organization, item, criteria=criteria)
            for item in merge_observations(observations)
        )
        qualified_intents = {
            observation.intent_key
            for candidate in candidates
            if candidate.qualified
            for observation in candidate.observations
        }
        all_intents = tuple(dict.fromkeys(plan.intent_key for plan in plans))
        missing = tuple(value for value in all_intents if value not in qualified_intents)
        return _CompanyExaPhase(
            organization,
            plans,
            tuple(observations),
            tuple(attempts),
            candidates,
            missing,
            had_transient_error=transient,
        )

    def discover(
        self,
        organizations: Iterable[Organization],
        criteria: SearchCriteria,
        *,
        allow_codex_fallback: bool = False,
    ) -> DiscoveryBatchResult:
        organization_list = list(organizations)
        if not organization_list or len(organization_list) > MAX_COMPANIES_PER_RUN:
            raise ValueError("discovery requires 1 to 8 organizations")
        started_at = timezone.now()
        deadline = self.clock() + self.max_batch_seconds
        phases = {}
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(organization_list))) as pool:
            futures = {
                pool.submit(self._exa_phase, organization, criteria): organization.pk
                for organization in organization_list
            }
            for future in as_completed(futures):
                phases[futures[future]] = future.result()

        fallback_used = 0
        company_results = []
        for organization in organization_list:
            phase = phases[organization.pk]
            if phase.permanent_error:
                company_results.append(CompanyDiscoveryResult(
                    organization,
                    "failed",
                    (),
                    phase.attempts,
                    error_code=phase.permanent_error,
                ))
                continue
            candidates = phase.candidates
            attempts = list(phase.attempts)
            fallback_reason = ""
            status = "degraded" if phase.had_transient_error else "complete"
            if phase.missing_intents:
                fallback_reason = (
                    "EXA_TRANSIENT_ERROR"
                    if phase.had_transient_error
                    else "NO_QUALIFIED_EXA_CANDIDATE"
                )
                if allow_codex_fallback and self.codex_searcher is not None:
                    remaining_seconds = int(deadline - self.clock())
                    if remaining_seconds <= 0:
                        status = "degraded"
                        fallback_reason = "BATCH_DEADLINE_EXHAUSTED"
                    elif fallback_used >= self.max_codex_fallback_companies:
                        status = "degraded"
                        fallback_reason = "FALLBACK_BUDGET_EXHAUSTED"
                    else:
                        fallback_used += 1
                        codex_started = self.latency_clock()
                        try:
                            codex_observations = tuple(
                                replace(item, provider="codex_web_search")
                                for item in self.codex_searcher(
                                    organization,
                                    phase.plans,
                                    phase.candidates,
                                    timeout_seconds=min(
                                        MAX_CODEX_TIMEOUT_SECONDS,
                                        remaining_seconds,
                                    ),
                                )
                            )
                        except Exception as error:
                            codex_observations = ()
                            codex_duration_ms = max(
                                0,
                                int((self.latency_clock() - codex_started) * 1000),
                            )
                            codex_error_code = (
                                "TIMEOUT"
                                if "TIMEOUT" in str(error).upper()
                                else "CODEX_EXEC_FAILED"
                            )
                            attempts.append(ProviderAttempt(
                                provider="codex_web_search",
                                intent_key=",".join(phase.missing_intents),
                                query="controlled company fallback",
                                status="permanent_error",
                                request_key=hashlib.sha256(
                                    f"codex:{organization.pk}:{','.join(phase.missing_intents)}".encode("utf-8")
                                ).hexdigest(),
                                duration_ms=codex_duration_ms,
                                error_code=codex_error_code,
                            ))
                            status = "degraded"
                        else:
                            codex_duration_ms = max(
                                0,
                                int((self.latency_clock() - codex_started) * 1000),
                            )
                            attempts.append(ProviderAttempt(
                                provider="codex_web_search",
                                intent_key=",".join(phase.missing_intents),
                                query="controlled company fallback",
                                status="success" if codex_observations else "empty",
                                request_key=hashlib.sha256(
                                    f"codex:{organization.pk}:{','.join(phase.missing_intents)}".encode("utf-8")
                                ).hexdigest(),
                                duration_ms=codex_duration_ms,
                                result_count=len(codex_observations),
                            ))
                            candidates = rank_discovery_candidates(
                                route_candidate(organization, item, criteria=criteria)
                                for item in merge_observations(
                                    (*phase.observations, *codex_observations)
                                )
                            )
                            if phase.had_transient_error:
                                status = "degraded"
                elif phase.had_transient_error:
                    status = "degraded"
            company_results.append(CompanyDiscoveryResult(
                organization,
                status,
                candidates,
                tuple(attempts),
                fallback_reason=fallback_reason,
            ))
        if company_results and all(item.status == "failed" for item in company_results):
            batch_status = "failed"
        elif any(item.status in {"failed", "degraded"} for item in company_results):
            batch_status = "partial"
        else:
            batch_status = "complete"
        return DiscoveryBatchResult(
            criteria=criteria,
            status=batch_status,
            companies=tuple(company_results),
            started_at=started_at,
            completed_at=timezone.now(),
        )


def _decimal_cost(value: float | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.000001"))
    except (InvalidOperation, ValueError):
        return None


def persist_discovery_result(result: DiscoveryBatchResult) -> AnnouncementDiscoveryRun:
    run = AnnouncementDiscoveryRun.objects.create(
        criteria=result.criteria.as_dict(),
        status=result.status,
        started_at=result.started_at,
        completed_at=result.completed_at,
    )
    persistence_failed = False
    for company in result.companies:
        try:
            with transaction.atomic():
                organization_run = AnnouncementDiscoveryOrganizationRun.objects.create(
                    run=run,
                    organization=company.organization,
                    status=company.status,
                    fallback_reason=company.fallback_reason,
                    error_code=company.error_code,
                )
                for attempt in company.attempts:
                    AnnouncementDiscoveryProviderAttempt.objects.create(
                        organization_run=organization_run,
                        provider=attempt.provider,
                        request_key=attempt.request_key or hashlib.sha256(
                            f"{attempt.provider}:{attempt.intent_key}:{attempt.query}".encode("utf-8")
                        ).hexdigest(),
                        intent_key=attempt.intent_key[:64],
                        query=attempt.query[:500],
                        status=attempt.status,
                        request_id=attempt.request_id,
                        duration_ms=attempt.duration_ms,
                        result_count=attempt.result_count,
                        cost_dollars=_decimal_cost(attempt.cost_dollars),
                        error_code=attempt.error_code,
                    )
                for item in company.candidates:
                    first_observation = item.observations[0]
                    candidate, created = AnnouncementDiscoveryCandidate.objects.get_or_create(
                        organization=company.organization,
                        identity_url=item.identity_url,
                        defaults={
                            "source_kind": item.source_kind,
                            "url": item.fetch_url,
                            "title_hint": item.title_hint,
                            "provider": first_observation.provider,
                            "provider_result_id": first_observation.result_id,
                            "route_state": item.route_state,
                            "state": AnnouncementDiscoveryCandidate.State.NEW,
                            "error_code": item.rejection_code,
                        },
                    )
                    if not created and candidate.state in {
                        AnnouncementDiscoveryCandidate.State.NEW,
                        AnnouncementDiscoveryCandidate.State.FAILED,
                    }:
                        candidate.title_hint = item.title_hint
                        candidate.route_state = item.route_state
                        candidate.source_kind = item.source_kind
                        candidate.error_code = item.rejection_code
                        candidate.save(update_fields=[
                            "title_hint",
                            "route_state",
                            "source_kind",
                            "error_code",
                        ])
                    for observation in item.observations:
                        metadata = normalize_identity_text(
                            f"{observation.title_hint} {observation.snippet}"
                        )
                        AnnouncementDiscoveryObservation.objects.get_or_create(
                            organization_run=organization_run,
                            candidate=candidate,
                            provider=observation.provider,
                            request_key=observation.request_key or hashlib.sha256(
                                f"{observation.provider}:{observation.intent_key}:{observation.query}".encode("utf-8")
                            ).hexdigest(),
                            result_id=observation.result_id,
                            defaults={
                                "intent_key": observation.intent_key,
                                "query": observation.query,
                                "rank": observation.rank,
                                "title_hint": observation.title_hint,
                                "backend_date_hint": observation.backend_date_hint,
                                "snippet_sha256": (
                                    hashlib.sha256(observation.snippet.encode("utf-8")).hexdigest()
                                    if observation.snippet
                                    else ""
                                ),
                                "company_signal_found": any(
                                    normalize_identity_text(name) in metadata
                                    for name in _organization_names(company.organization)
                                ),
                                "recruitment_signal_found": any(
                                    term.casefold() in metadata for term in RECRUITMENT_TERMS
                                ),
                                "discovered_at": observation.discovered_at,
                            },
                        )
        except Exception:
            persistence_failed = True
            AnnouncementDiscoveryOrganizationRun.objects.create(
                run=run,
                organization=company.organization,
                status=AnnouncementDiscoveryOrganizationRun.Status.FAILED,
                error_code="PERSISTENCE_FAILED",
            )
    if persistence_failed:
        persisted_statuses = list(
            run.organization_runs.values_list("status", flat=True)
        )
        run.status = (
            AnnouncementDiscoveryRun.Status.FAILED
            if persisted_statuses
            and all(
                status == AnnouncementDiscoveryOrganizationRun.Status.FAILED
                for status in persisted_statuses
            )
            else AnnouncementDiscoveryRun.Status.PARTIAL
        )
        run.error_code = (
            "PERSISTENCE_FAILED"
            if run.status == AnnouncementDiscoveryRun.Status.FAILED
            else "PERSISTENCE_PARTIAL"
        )
        run.save(update_fields=["status", "error_code"])
    return run
