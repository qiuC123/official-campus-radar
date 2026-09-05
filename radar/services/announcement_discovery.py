from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import os
import socket
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

from radar.models import (
    AnnouncementDiscoveryCandidate,
    Organization,
    RecruitmentAnnouncement,
)
from radar.services.normalization import canonicalize_url


OFFICIAL_CANDIDATE_SCHEMA_VERSION = "1"
MAX_CANDIDATES = 100
MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?key|cookie|authorization|password|secret|token)\s*[:=]"
)
_RECRUITMENT_TERMS = (
    "校园招聘",
    "校招",
    "春招",
    "补录",
    "秋招",
    "实习",
    "招聘计划",
    "campus",
    "graduate",
)


def _normalized_text_hash(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DiscoveryContractError(ValueError):
    pass


def _codex_failure_category(stderr: str) -> str:
    value = (stderr or "").casefold()
    for needle, category in (
        ("invalid json schema", "INVALID_OUTPUT_SCHEMA"),
        ("additionalproperties", "INVALID_OUTPUT_SCHEMA"),
        ("unexpected argument", "CLI_ARGUMENT_ERROR"),
        ("unrecognized", "CLI_ARGUMENT_ERROR"),
        ("not logged in", "AUTH_REQUIRED"),
        ("authentication", "AUTH_REQUIRED"),
        ("rate limit", "RATE_LIMITED"),
        ("429", "RATE_LIMITED"),
        ("timed out", "TIMEOUT"),
        ("network", "NETWORK_ERROR"),
        ("connection", "NETWORK_ERROR"),
    ):
        if needle in value:
            return category
    return "CODEX_EXEC_FAILED"


@dataclass(frozen=True)
class OfficialSiteCandidate:
    url: str
    title_hint: str
    provider: str
    rank: int
    result_id: str
    source_kind: str = RecruitmentAnnouncement.SourceKind.WEBSITE


@dataclass(frozen=True)
class OfficialSiteCandidateBatch:
    query: str
    orchestrator: str
    providers: tuple[str, ...]
    candidates: tuple[OfficialSiteCandidate, ...]


@dataclass(frozen=True)
class RefetchedOfficialCandidate:
    url: str
    title: str
    content_sha256: str
    fetched_at: object
    recruitment_signal_found: bool
    verification_method: str = "http"


@dataclass(frozen=True)
class RenderedOfficialPage:
    url: str
    title: str
    body_text: str
    html: str


def _codex_command_prefix(value: str) -> list[str]:
    if os.name != "nt":
        return [value]
    resolved = shutil.which("codex.cmd") if value.casefold() == "codex" else value
    if not resolved:
        raise OSError("Codex executable is unavailable")
    if str(resolved).casefold().endswith((".cmd", ".bat")):
        wrapper = Path(resolved).resolve()
        native_candidates = sorted(
            wrapper.parent.glob(
                "node_modules/@openai/codex/node_modules/@openai/"
                "codex-win32-*/vendor/*/bin/codex.exe"
            )
        )
        native_candidates.extend(sorted(
            wrapper.parent.glob(
                "node_modules/@openai/codex/vendor/*/bin/codex.exe"
            )
        ))
        if not native_candidates:
            raise OSError("Codex native executable is unavailable")
        return [str(native_candidates[0])]
    return [str(resolved)]


def scrubbed_discovery_subprocess_environment(
    environ: dict[str, str] | None = None,
) -> dict[str, str]:
    values = dict(os.environ if environ is None else environ)
    values.pop("EXA_API_KEY", None)
    return values


def _expect_keys(value: dict, allowed: set[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise DiscoveryContractError(
            f"{label} contains unknown fields: {', '.join(sorted(unknown))}"
        )


def _safe_identifier(value: object, label: str) -> str:
    normalized = str(value or "").strip().casefold()
    if not _IDENTIFIER.fullmatch(normalized):
        raise DiscoveryContractError(f"invalid {label}")
    return normalized


def _safe_provider_identifier(value: object) -> str:
    normalized = re.sub(
        r"[^a-z0-9._-]+",
        "_",
        str(value or "").strip().casefold(),
    ).strip("_.-")
    if not _IDENTIFIER.fullmatch(normalized):
        raise DiscoveryContractError("invalid provider")
    return normalized


def _clean_url(value: object) -> str:
    raw = str(value or "").strip()
    parts = urlsplit(raw)
    if parts.scheme != "https" or not parts.hostname:
        raise DiscoveryContractError("candidate URL must be an absolute HTTPS URL")
    if parts.username or parts.password:
        raise DiscoveryContractError("candidate URL must not contain credentials")
    if parts.hostname.casefold() == "mp.weixin.qq.com":
        raise DiscoveryContractError(
            "WeChat URLs belong to the wechat-oa candidate contract"
        )
    return canonicalize_url(raw)


def parse_official_candidate_batch(raw: str | bytes | dict) -> OfficialSiteCandidateBatch:
    if isinstance(raw, dict):
        encoded = json.dumps(raw, ensure_ascii=False).encode("utf-8")
        payload = raw
    else:
        encoded = raw if isinstance(raw, bytes) else raw.encode("utf-8")
        if len(encoded) > MAX_DOCUMENT_BYTES:
            raise DiscoveryContractError("candidate batch exceeds the 2 MiB limit")
        try:
            payload = json.loads(encoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise DiscoveryContractError("candidate batch is not valid UTF-8 JSON") from error
    if len(encoded) > MAX_DOCUMENT_BYTES:
        raise DiscoveryContractError("candidate batch exceeds the 2 MiB limit")
    if not isinstance(payload, dict):
        raise DiscoveryContractError("candidate batch must be an object")
    if _CREDENTIAL_ASSIGNMENT.search(encoded.decode("utf-8", errors="ignore")):
        raise DiscoveryContractError("candidate batch must not contain credential assignments")
    _expect_keys(payload, {"schema_version", "query", "source", "candidates"}, "batch")
    if payload.get("schema_version") != OFFICIAL_CANDIDATE_SCHEMA_VERSION:
        raise DiscoveryContractError("unsupported official candidate schema version")
    query = str(payload.get("query") or "").strip()
    if not query or len(query) > 500 or any(ord(char) < 32 for char in query):
        raise DiscoveryContractError("invalid discovery query")
    source = payload.get("source")
    if not isinstance(source, dict):
        raise DiscoveryContractError("source must be an object")
    _expect_keys(source, {"orchestrator", "providers"}, "source")
    orchestrator = _safe_identifier(source.get("orchestrator"), "orchestrator")
    provider_values = source.get("providers")
    if not isinstance(provider_values, list) or not 1 <= len(provider_values) <= 10:
        raise DiscoveryContractError("source providers must contain 1 to 10 items")
    providers = tuple(dict.fromkeys(_safe_provider_identifier(item) for item in provider_values))
    candidate_values = payload.get("candidates")
    if not isinstance(candidate_values, list) or len(candidate_values) > MAX_CANDIDATES:
        raise DiscoveryContractError("candidates must contain at most 100 items")
    candidates: list[OfficialSiteCandidate] = []
    seen: set[str] = set()
    for item in candidate_values:
        if not isinstance(item, dict):
            raise DiscoveryContractError("each candidate must be an object")
        _expect_keys(item, {"url", "title_hint", "provider", "rank", "result_id"}, "candidate")
        provider = _safe_provider_identifier(item.get("provider"))
        if provider not in providers:
            raise DiscoveryContractError("candidate provider was not declared by the batch")
        url = _clean_url(item.get("url"))
        title = str(item.get("title_hint") or "").strip()
        result_id = str(item.get("result_id") or "").strip()
        try:
            rank = int(item.get("rank"))
        except (TypeError, ValueError) as error:
            raise DiscoveryContractError("candidate rank must be an integer") from error
        if rank < 1 or len(title) > 500 or len(result_id) > 128:
            raise DiscoveryContractError("candidate metadata is out of bounds")
        if url in seen:
            continue
        seen.add(url)
        candidates.append(OfficialSiteCandidate(url, title, provider, rank, result_id))
    return OfficialSiteCandidateBatch(query, orchestrator, providers, tuple(candidates))


def official_candidate_json_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "query", "source", "candidates"],
        "properties": {
            "schema_version": {"type": "string", "enum": ["1"]},
            "query": {"type": "string"},
            "source": {
                "type": "object",
                "additionalProperties": False,
                "required": ["orchestrator", "providers"],
                "properties": {
                    "orchestrator": {"type": "string", "enum": ["codex"]},
                    "providers": {"type": "array", "items": {"type": "string"}},
                },
            },
            "candidates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["url", "title_hint", "provider", "rank", "result_id"],
                    "properties": {
                        "url": {"type": "string"},
                        "title_hint": {"type": "string"},
                        "provider": {"type": "string", "enum": ["codex_web_search"]},
                        "rank": {"type": "integer"},
                        "result_id": {"type": "string"},
                    },
                },
            },
        },
    }


def discover_official_candidates_with_codex(
    organization: Organization,
    *,
    codex_path: str = "codex",
    timeout_seconds: int = 180,
    search_queries: Iterable[str] = (),
    published_after: str = "",
    published_before: str = "",
    candidate_context: Iterable[dict] = (),
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> OfficialSiteCandidateBatch:
    known_hosts = sorted(
        {
            host
            for host in (
                organization.official_domain,
                *(urlsplit(url).hostname or "" for url in organization.official_sources.values_list("source_url", flat=True)),
            )
            if host
        }
    )
    bounded_queries = [str(value).strip()[:500] for value in search_queries][:4]
    bounded_context = [
        {
            "url": str(value.get("url") or "")[:2000],
            "title_hint": str(value.get("title_hint") or "")[:500],
            "route_state": str(value.get("route_state") or "")[:40],
            "rejection_code": str(value.get("rejection_code") or "")[:64],
        }
        for value in candidate_context
        if isinstance(value, dict)
    ][:40]
    scope = json.dumps(
        {
            "queries": bounded_queries,
            "published_after": str(published_after or "")[:10],
            "published_before": str(published_before or "")[:10],
            "existing_candidate_classifications": bounded_context,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    prompt = (
        "搜索企业当前校园招聘的官方正式公告或官方招聘系统项目页。"
        "只返回企业官网、集团官网或官方招聘系统页面，不返回聚合站和微信公众号。"
        "搜索结果只是候选，不要声称已完成身份验证。\n"
        f"企业：{organization.name}\n"
        f"已知官方域名：{', '.join(known_hosts) or '未配置'}\n"
        f"显式检索范围与已有候选分类：{scope}\n"
        "不要根据当前年份推断届次；不要把已有候选的标题提示当作证据。\n"
        "输出必须符合给定 JSON Schema；provider 固定填写 codex_web_search。"
    )
    with tempfile.TemporaryDirectory(prefix="radar-codex-discovery-") as directory:
        schema_path = Path(directory) / "schema.json"
        schema_path.write_text(
            json.dumps(official_candidate_json_schema(), ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            completed = runner(
                [
                    *_codex_command_prefix(codex_path),
                    "--search",
                    "exec",
                    "--ephemeral",
                    "--sandbox",
                    "read-only",
                    "--output-schema",
                    str(schema_path),
                    "-",
                ],
                input=prompt,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                env=scrubbed_discovery_subprocess_environment(),
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Codex official-site discovery failed: TIMEOUT") from error
    if completed.returncode != 0:
        category = _codex_failure_category(completed.stderr)
        raise RuntimeError(f"Codex official-site discovery failed: {category} (exit {completed.returncode})")
    batch = parse_official_candidate_batch(completed.stdout)
    return OfficialSiteCandidateBatch(
        query=batch.query,
        orchestrator="codex",
        providers=("codex_web_search",),
        candidates=tuple(
            replace(candidate, provider="codex_web_search")
            for candidate in batch.candidates
        ),
    )


def _bulk_candidate_json_schema(company_names: list[str]) -> dict:
    candidate = official_candidate_json_schema()["properties"]["candidates"]["items"]
    candidate = json.loads(json.dumps(candidate))
    candidate["required"] = ["company", *candidate["required"]]
    candidate["properties"]["company"] = {"enum": company_names}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "source", "candidates"],
        "properties": {
            "schema_version": {"type": "string", "enum": ["1"]},
            "source": official_candidate_json_schema()["properties"]["source"],
            "candidates": {
                "type": "array",
                "items": candidate,
            },
        },
    }


def parse_bulk_official_candidate_batch(
    raw: str | bytes | dict,
    organizations: Iterable[Organization],
) -> dict[int, OfficialSiteCandidateBatch]:
    organization_list = list(organizations)
    by_name = {item.name: item for item in organization_list}
    if isinstance(raw, dict):
        encoded = json.dumps(raw, ensure_ascii=False).encode("utf-8")
        payload = raw
    else:
        encoded = raw if isinstance(raw, bytes) else raw.encode("utf-8")
        if len(encoded) > MAX_DOCUMENT_BYTES:
            raise DiscoveryContractError("bulk candidate batch exceeds the 2 MiB limit")
        try:
            payload = json.loads(encoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise DiscoveryContractError("bulk candidate batch is not valid JSON") from error
    if not isinstance(payload, dict) or len(encoded) > MAX_DOCUMENT_BYTES:
        raise DiscoveryContractError("invalid bulk candidate batch")
    if _CREDENTIAL_ASSIGNMENT.search(encoded.decode("utf-8", errors="ignore")):
        raise DiscoveryContractError("bulk candidate batch must not contain credential assignments")
    _expect_keys(payload, {"schema_version", "source", "candidates"}, "bulk batch")
    if payload.get("schema_version") != "1":
        raise DiscoveryContractError("unsupported bulk candidate schema")
    source = payload.get("source")
    if not isinstance(source, dict):
        raise DiscoveryContractError("bulk source must be an object")
    _expect_keys(source, {"orchestrator", "providers"}, "bulk source")
    orchestrator = _safe_identifier(source.get("orchestrator"), "orchestrator")
    raw_providers = source.get("providers")
    if not isinstance(raw_providers, list) or not 1 <= len(raw_providers) <= 10:
        raise DiscoveryContractError("bulk providers must contain 1 to 10 items")
    providers = tuple(dict.fromkeys(_safe_provider_identifier(item) for item in raw_providers))
    raw_candidates = payload.get("candidates")
    if not isinstance(raw_candidates, list) or len(raw_candidates) > MAX_CANDIDATES:
        raise DiscoveryContractError("bulk candidates must contain at most 100 items")
    grouped: dict[int, list[OfficialSiteCandidate]] = {item.pk: [] for item in organization_list}
    seen: dict[int, set[str]] = {item.pk: set() for item in organization_list}
    for value in raw_candidates:
        if not isinstance(value, dict):
            raise DiscoveryContractError("bulk candidate must be an object")
        _expect_keys(
            value,
            {"company", "url", "title_hint", "provider", "rank", "result_id"},
            "bulk candidate",
        )
        organization = by_name.get(str(value.get("company") or "").strip())
        if organization is None:
            raise DiscoveryContractError("bulk candidate company is not in the requested set")
        provider = _safe_provider_identifier(value.get("provider"))
        if provider not in providers:
            raise DiscoveryContractError("bulk candidate provider was not declared")
        url = _clean_url(value.get("url"))
        if url in seen[organization.pk]:
            continue
        seen[organization.pk].add(url)
        try:
            rank = int(value.get("rank"))
        except (TypeError, ValueError) as error:
            raise DiscoveryContractError("bulk candidate rank must be an integer") from error
        if rank < 1:
            raise DiscoveryContractError("bulk candidate rank must be positive")
        title_hint = str(value.get("title_hint") or "").strip()
        result_id = str(value.get("result_id") or "").strip()
        if len(title_hint) > 500 or len(result_id) > 128:
            raise DiscoveryContractError("bulk candidate metadata is out of bounds")
        grouped[organization.pk].append(OfficialSiteCandidate(
            url=url,
            title_hint=title_hint,
            provider=provider,
            rank=rank,
            result_id=result_id,
        ))
    return {
        item.pk: OfficialSiteCandidateBatch(
            query=f"{item.name} 当前校园招聘公告",
            orchestrator=orchestrator,
            providers=providers,
            candidates=tuple(grouped[item.pk]),
        )
        for item in organization_list
    }


def discover_official_candidates_bulk_with_codex(
    organizations: Iterable[Organization],
    *,
    codex_path: str = "codex",
    timeout_seconds: int = 300,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> dict[int, OfficialSiteCandidateBatch]:
    organization_list = list(organizations)
    if not organization_list:
        return {}
    company_lines = []
    for organization in organization_list:
        hosts = sorted(_known_organization_hosts(organization))
        company_lines.append(f"- {organization.name}；已知域名：{', '.join(hosts) or '未配置'}")
    prompt = (
        "逐家搜索以下企业当前校园招聘的官方正式公告或官方招聘系统项目页。"
        "只返回企业官网、集团官网或官方招聘系统页面，不返回聚合站和微信公众号。"
        "每个结果必须准确填写给定企业名。搜索结果只是候选，不要声称完成身份核验。\n"
        + "\n".join(company_lines)
    )
    with tempfile.TemporaryDirectory(prefix="radar-codex-bulk-discovery-") as directory:
        schema_path = Path(directory) / "schema.json"
        schema_path.write_text(
            json.dumps(
                _bulk_candidate_json_schema([item.name for item in organization_list]),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        try:
            completed = runner(
                [*_codex_command_prefix(codex_path), "--search", "exec", "--ephemeral", "--sandbox", "read-only", "--output-schema", str(schema_path), "-"],
                input=prompt,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                env=scrubbed_discovery_subprocess_environment(),
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Codex bulk official-site discovery failed: TIMEOUT") from error
    if completed.returncode != 0:
        category = _codex_failure_category(completed.stderr)
        raise RuntimeError(f"Codex bulk official-site discovery failed: {category} (exit {completed.returncode})")
    return parse_bulk_official_candidate_batch(completed.stdout, organization_list)


def _known_organization_hosts(organization: Organization) -> set[str]:
    from radar.services.admission import source_is_admitted

    hosts = {organization.official_domain.casefold()} if organization.official_domain else set()
    for source in organization.official_sources.select_related("organization").prefetch_related(
        "admission_events", "approved_application_hosts__admission_event"
    ):
        if not source_is_admitted(source):
            continue
        host = urlsplit(source.source_url).hostname
        if host:
            hosts.add(host.casefold())
    return hosts


def _source_kind_for_url(organization: Organization, url: str) -> str:
    host = (urlsplit(url).hostname or "").casefold()
    matched = []
    for source in organization.official_sources.all():
        source_host = (urlsplit(source.source_url).hostname or "").casefold()
        if source_host and (host == source_host or host.endswith(f".{source_host}")):
            matched.append((len(source_host), source.source_type))
    if matched and max(matched)[1] in {"ats", "api"}:
        return RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM
    return RecruitmentAnnouncement.SourceKind.WEBSITE


def _host_is_known(host: str, known_hosts: Iterable[str]) -> bool:
    normalized = host.casefold().rstrip(".")
    return any(normalized == known or normalized.endswith(f".{known}") for known in known_hosts)


def _host_is_local_or_private(host: str) -> bool:
    normalized = host.casefold().rstrip(".")
    if normalized in {"localhost", "localhost.localdomain"} or normalized.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return not address.is_global


def _resolved_addresses(host: str) -> tuple[str, ...]:
    return tuple({
        item[4][0]
        for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    })


def _require_public_host(
    host: str,
    *,
    resolver: Callable[[str], Iterable[str]],
) -> None:
    if _host_is_local_or_private(host):
        raise DiscoveryContractError("official-site request targets a local or private host")
    try:
        addresses = tuple(resolver(host))
    except OSError as error:
        raise DiscoveryContractError("official-site host could not be resolved") from error
    try:
        unsafe = not addresses or any(
            not ipaddress.ip_address(address).is_global for address in addresses
        )
    except ValueError as error:
        raise DiscoveryContractError("official-site host resolved to an invalid address") from error
    if unsafe:
        raise DiscoveryContractError("official-site host did not resolve only to public addresses")


def _stable_final_url(requested_url: str, observed_url: str) -> str:
    requested = canonicalize_url(requested_url)
    observed = canonicalize_url(observed_url)
    requested_parts = urlsplit(requested)
    observed_parts = urlsplit(observed)
    if (
        requested_parts.scheme == observed_parts.scheme
        and requested_parts.hostname == observed_parts.hostname
        and requested_parts.path.rstrip("/") == observed_parts.path.rstrip("/")
    ):
        return requested
    return observed


def playwright_render_official_page(
    url: str,
    *,
    timeout_seconds: int,
    wait_for_text: Iterable[str] = _RECRUITMENT_TERMS,
) -> RenderedOfficialPage:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    timeout_ms = timeout_seconds * 1000
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--no-proxy-server"],
                env=scrubbed_discovery_subprocess_environment(),
            )
            context_options = {
                "service_workers": "block",
                "accept_downloads": False,
            }
            if "/mobile/" in urlsplit(url).path.casefold():
                context_options.update({
                    "viewport": {"width": 390, "height": 844},
                    "is_mobile": True,
                    "has_touch": True,
                    "user_agent": (
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                        "Mobile/15E148 Safari/604.1"
                    ),
                })
            context = browser.new_context(
                **context_options,
            )
            try:
                page = context.new_page()

                def block_private_network(route, request):
                    host = urlsplit(request.url).hostname or ""
                    if _host_is_local_or_private(host):
                        route.abort()
                    else:
                        route.continue_()

                page.route("**/*", block_private_network)
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.locator("body").wait_for(state="attached", timeout=timeout_ms)
                body_text = ""
                remaining_wait_ms = min(10_000, timeout_ms // 2)
                while remaining_wait_ms > 0:
                    body_text = page.locator("body").inner_text(timeout=timeout_ms)
                    if any(
                        term.casefold() in body_text.casefold()
                        for term in wait_for_text
                    ):
                        break
                    wait_ms = min(500, remaining_wait_ms)
                    page.wait_for_timeout(wait_ms)
                    remaining_wait_ms -= wait_ms
                body_text = page.locator("body").inner_text(timeout=timeout_ms)
                rendered = RenderedOfficialPage(
                    url=page.url,
                    title=page.title(),
                    body_text=body_text,
                    html=page.content(),
                )
            finally:
                context.close()
                browser.close()
    except PlaywrightTimeoutError as error:
        raise DiscoveryContractError("official-site browser rendering timed out") from error
    except PlaywrightError as error:
        raise DiscoveryContractError("official-site browser rendering failed") from error
    return rendered


def render_official_candidate(
    organization: Organization,
    candidate: OfficialSiteCandidate,
    *,
    timeout_seconds: int = 30,
    renderer: Callable[..., RenderedOfficialPage] = playwright_render_official_page,
) -> RefetchedOfficialCandidate:
    """Render one reviewed official URL in an isolated, non-persistent browser."""

    host = urlsplit(candidate.url).hostname or ""
    known_hosts = _known_organization_hosts(organization)
    if not _host_is_known(host, known_hosts):
        raise DiscoveryContractError("candidate host is not an admitted organization host")
    rendered = renderer(candidate.url, timeout_seconds=timeout_seconds)
    observed_url = canonicalize_url(rendered.url)
    observed_parts = urlsplit(observed_url)
    if (
        observed_parts.scheme != "https"
        or observed_parts.username
        or observed_parts.password
        or not _host_is_known(observed_parts.hostname or "", known_hosts)
    ):
        raise DiscoveryContractError("rendered candidate redirected outside admitted organization hosts")
    final_url = _stable_final_url(candidate.url, observed_url)
    encoded_html = rendered.html.encode("utf-8")
    encoded_text = rendered.body_text.encode("utf-8")
    if len(encoded_html) > MAX_DOCUMENT_BYTES or len(encoded_text) > MAX_DOCUMENT_BYTES:
        raise DiscoveryContractError("rendered official page exceeds the 2 MiB evidence limit")
    text_value = rendered.body_text.casefold()
    return RefetchedOfficialCandidate(
        url=final_url,
        title=(rendered.title.strip() or candidate.title_hint)[:500],
        content_sha256=_normalized_text_hash(rendered.body_text),
        fetched_at=timezone.now(),
        recruitment_signal_found=any(
            term.casefold() in text_value for term in _RECRUITMENT_TERMS
        ),
        verification_method="browser",
    )


def refetch_official_candidate(
    organization: Organization,
    candidate: OfficialSiteCandidate,
    *,
    session=requests,
    timeout_seconds: int = 20,
    resolver: Callable[[str], Iterable[str]] = _resolved_addresses,
) -> RefetchedOfficialCandidate:
    known_hosts = _known_organization_hosts(organization)
    current_url = candidate.url
    response = None
    for _hop in range(6):
        parts = urlsplit(current_url)
        host = parts.hostname or ""
        if (
            parts.scheme != "https"
            or parts.username
            or parts.password
            or not _host_is_known(host, known_hosts)
        ):
            raise DiscoveryContractError("candidate redirect left admitted organization hosts")
        _require_public_host(host, resolver=resolver)
        response = session.get(
            current_url,
            timeout=timeout_seconds,
            headers={"User-Agent": "official-campus-radar/announcement-verifier"},
            allow_redirects=False,
        )
        status_code = int(getattr(response, "status_code", 200))
        if status_code not in {301, 302, 303, 307, 308}:
            break
        location = str(getattr(response, "headers", {}).get("Location") or "").strip()
        if not location:
            raise DiscoveryContractError("official-site redirect has no Location")
        current_url = canonicalize_url(urljoin(current_url, location))
    else:
        raise DiscoveryContractError("official-site redirect limit exceeded")
    if response is None:
        raise DiscoveryContractError("official-site request did not produce a response")
    response.raise_for_status()
    observed_url = canonicalize_url(getattr(response, "url", current_url) or current_url)
    observed_parts = urlsplit(observed_url)
    final_host = observed_parts.hostname or ""
    if (
        observed_parts.scheme != "https"
        or observed_parts.username
        or observed_parts.password
        or not _host_is_known(final_host, _known_organization_hosts(organization))
    ):
        raise DiscoveryContractError("candidate redirected outside admitted organization hosts")
    canonical_url = _stable_final_url(candidate.url, observed_url)
    body = response.content
    if len(body) > MAX_DOCUMENT_BYTES:
        raise DiscoveryContractError("official page exceeds the 2 MiB evidence limit")
    from radar.services.html_encoding import decode_html

    headers = getattr(response, "headers", {})
    content_type = next(
        (str(value) for key, value in headers.items() if key.lower() == "content-type"),
        "",
    )
    try:
        markup = decode_html(body, content_type)
    except (ValueError, UnicodeError) as exc:
        raise DiscoveryContractError("official HTML encoding could not be verified") from exc
    soup = BeautifulSoup(markup, "html.parser")
    title = (soup.title.get_text(" ", strip=True) if soup.title else "").strip()
    text = soup.get_text(" ", strip=True).casefold()
    return RefetchedOfficialCandidate(
        url=canonical_url,
        title=title[:500],
        content_sha256=_normalized_text_hash(soup.get_text(" ", strip=True)),
        fetched_at=timezone.now(),
        recruitment_signal_found=any(term.casefold() in text for term in _RECRUITMENT_TERMS),
        verification_method="http",
    )


def snapshot_official_candidate(
    organization: Organization,
    candidate: OfficialSiteCandidate,
    *,
    snapshot_bytes: bytes,
    snapshot_title: str,
    human_confirmed_signal: bool,
) -> RefetchedOfficialCandidate:
    """Create explicitly human-reviewed evidence when the official page blocks reads."""

    host = urlsplit(candidate.url).hostname or ""
    if not _host_is_known(host, _known_organization_hosts(organization)):
        raise DiscoveryContractError("candidate host is not an admitted organization host")
    if not snapshot_bytes or len(snapshot_bytes) > 10 * 1024 * 1024:
        raise DiscoveryContractError("snapshot must contain 1 byte to 10 MiB")
    if not human_confirmed_signal:
        raise DiscoveryContractError("snapshot recruitment signal requires explicit human confirmation")
    title = snapshot_title.strip()
    if not title or len(title) > 500:
        raise DiscoveryContractError("snapshot title is invalid")
    return RefetchedOfficialCandidate(
        url=canonicalize_url(candidate.url),
        title=title,
        content_sha256=hashlib.sha256(snapshot_bytes).hexdigest(),
        fetched_at=timezone.now(),
        recruitment_signal_found=True,
        verification_method="human_snapshot",
    )


def fetch_official_candidate_for_verification(
    organization: Organization,
    candidate: OfficialSiteCandidate,
    *,
    allow_browser: bool = False,
    force_browser: bool = False,
    session=requests,
    resolver: Callable[[str], Iterable[str]] = _resolved_addresses,
    renderer: Callable[..., RenderedOfficialPage] = playwright_render_official_page,
) -> RefetchedOfficialCandidate:
    """Use HTTP first; render only when explicitly allowed and HTTP is insufficient."""

    if force_browser:
        if not allow_browser:
            raise DiscoveryContractError("force_browser requires explicit browser permission")
        return render_official_candidate(
            organization,
            candidate,
            renderer=renderer,
        )

    try:
        refetched = refetch_official_candidate(
            organization,
            candidate,
            session=session,
            resolver=resolver,
        )
    except requests.RequestException:
        if not allow_browser:
            raise
    else:
        if refetched.recruitment_signal_found or not allow_browser:
            return refetched
    return render_official_candidate(
        organization,
        candidate,
        renderer=renderer,
    )


def store_official_candidates(
    organization: Organization,
    batch: OfficialSiteCandidateBatch,
) -> tuple[AnnouncementDiscoveryCandidate, ...]:
    stored = []
    for candidate in batch.candidates:
        source_kind = _source_kind_for_url(organization, candidate.url)
        item, created = AnnouncementDiscoveryCandidate.objects.get_or_create(
            organization=organization,
            url=candidate.url,
            defaults={
                "source_kind": source_kind,
                "title_hint": candidate.title_hint,
                "provider": candidate.provider,
                "provider_result_id": candidate.result_id,
                "state": AnnouncementDiscoveryCandidate.State.NEW,
                "error_code": "",
            },
        )
        if not created and item.state in {
            AnnouncementDiscoveryCandidate.State.NEW,
            AnnouncementDiscoveryCandidate.State.FAILED,
        }:
            item.source_kind = source_kind
            item.title_hint = candidate.title_hint
            item.provider = candidate.provider
            item.provider_result_id = candidate.result_id
            item.save(update_fields=[
                "source_kind",
                "title_hint",
                "provider",
                "provider_result_id",
            ])
        stored.append(item)
    return tuple(stored)


def probe_official_candidates(
    organization: Organization,
    candidates: Iterable[AnnouncementDiscoveryCandidate],
    *,
    session=requests,
    resolver: Callable[[str], Iterable[str]] = _resolved_addresses,
) -> tuple[AnnouncementDiscoveryCandidate, ...]:
    """Re-fetch candidates without promoting search metadata into evidence."""

    probed = []
    for stored in candidates:
        candidate = OfficialSiteCandidate(
            url=stored.url,
            title_hint=stored.title_hint,
            provider=stored.provider,
            rank=1,
            result_id=stored.provider_result_id,
        )
        try:
            result = refetch_official_candidate(
                organization,
                candidate,
                session=session,
                resolver=resolver,
            )
        except DiscoveryContractError:
            stored.state = AnnouncementDiscoveryCandidate.State.NEW
            stored.error_code = "HOST_IDENTITY_REVIEW_REQUIRED"
            stored.technical_verified_at = timezone.now()
            stored.save(update_fields=["state", "error_code", "technical_verified_at"])
        except requests.RequestException:
            stored.state = AnnouncementDiscoveryCandidate.State.FAILED
            stored.error_code = "NETWORK_ERROR"
            stored.technical_verified_at = timezone.now()
            stored.save(update_fields=["state", "error_code", "technical_verified_at"])
        else:
            stored.final_url = result.url
            stored.title_hint = result.title or stored.title_hint
            stored.content_sha256 = result.content_sha256
            stored.recruitment_signal_found = result.recruitment_signal_found
            stored.technical_verified_at = result.fetched_at
            # A successful raw HTTP fetch may still expose only a JavaScript shell.
            # Missing keywords therefore means semantic review is required, not that
            # the company has no current official announcement.
            stored.state = AnnouncementDiscoveryCandidate.State.NEW
            stored.error_code = (
                "SEMANTIC_REVIEW_REQUIRED"
                if result.recruitment_signal_found
                else "CONTENT_REVIEW_REQUIRED"
            )
            stored.save(update_fields=[
                "final_url",
                "title_hint",
                "content_sha256",
                "recruitment_signal_found",
                "technical_verified_at",
                "state",
                "error_code",
            ])
        probed.append(stored)
    return tuple(probed)


def known_source_candidate_batch(organization: Organization) -> OfficialSiteCandidateBatch:
    """Use configured official entry points before spending an external search call."""

    candidates = []
    seen = set()
    sources = organization.official_sources.filter(
        source_type__in={"website", "announcement", "ats"},
        admission_state__in={"verified", "enabled"},
    ).order_by("pk")
    for rank, source in enumerate(sources, 1):
        raw_url = source.official_entrypoint_url or source.source_url
        try:
            url = _clean_url(raw_url)
        except DiscoveryContractError:
            continue
        if url in seen:
            continue
        seen.add(url)
        candidates.append(OfficialSiteCandidate(
            url=url,
            title_hint=f"{organization.name}官方招聘入口",
            provider="known_source",
            rank=rank,
            result_id=f"source-{source.pk}",
            source_kind=(
                RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM
                if source.source_type == "ats"
                else RecruitmentAnnouncement.SourceKind.WEBSITE
            ),
        ))
    return OfficialSiteCandidateBatch(
        query=f"{organization.name} 当前校园招聘公告",
        orchestrator="radar",
        providers=("known_source",),
        candidates=tuple(candidates),
    )
