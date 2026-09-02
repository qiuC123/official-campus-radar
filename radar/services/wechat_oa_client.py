from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from typing import Callable
from urllib.parse import urlsplit


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?key|cookie|authorization|password|secret|token)\s*[:=]"
)
_MAX_CANDIDATES = 100
_MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
WECHAT_OA_HYDRATION_TIMEOUT_SECONDS = 660
WECHAT_OA_EXA_MINIMUM_VERSION = (0, 7, 0)
_EXA_AUTH_FAILURE_REASONS = {
    "not_configured",
    "credential_rejected",
}
_EXA_NETWORK_FAILURE_REASONS = {
    "rate_limited",
    "timeout",
    "network_error",
    "provider_error",
    "invalid_response",
}


def _scrubbed_subprocess_environment() -> dict[str, str]:
    values = dict(os.environ)
    values.pop("EXA_API_KEY", None)
    return values


class WeChatOAError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        provider: str = "",
        reason: str = "",
        exit_code: int | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.provider = provider
        self.reason = reason
        self.exit_code = exit_code


@dataclass(frozen=True)
class WeChatOAHydrationResult:
    data: dict
    verified_candidates: tuple[dict, ...]
    partial: bool

    @property
    def verified_evidence(self) -> tuple[dict, ...]:
        return tuple(item["evidence"] for item in self.verified_candidates)


def _clean_search_text(value: object, label: str, maximum: int) -> str:
    clean = str(value or "").strip()
    if (
        not clean
        or len(clean) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in clean)
    ):
        raise WeChatOAError("INVALID_DISCOVERY_REQUEST", f"invalid {label}")
    return clean


def _date_argument(value: date | str | None, label: str) -> str:
    if value is None or value == "":
        return ""
    raw = value.isoformat() if isinstance(value, date) else str(value).strip()
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError as error:
        raise WeChatOAError(
            "INVALID_DISCOVERY_REQUEST", f"{label} must use YYYY-MM-DD"
        ) from error


def _failure_from_envelope(completed, operation: str) -> WeChatOAError | None:
    try:
        envelope = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError) as error:
        return WeChatOAError(
            "INVALID_JSON",
            f"wechat-oa did not return one JSON document for {operation}",
            exit_code=completed.returncode,
        )
    if not isinstance(envelope, dict):
        return WeChatOAError(
            "INVALID_JSON",
            f"wechat-oa JSON envelope for {operation} must be an object",
            exit_code=completed.returncode,
        )
    if completed.returncode == 0 and envelope.get("ok") is True:
        return None
    error_value = envelope.get("error") if isinstance(envelope.get("error"), dict) else {}
    details = error_value.get("details") if isinstance(error_value.get("details"), dict) else {}
    code = str(error_value.get("code") or f"EXIT_{completed.returncode}")
    provider = str(details.get("provider") or "")
    reason = str(details.get("reason") or "")
    expected_reasons = {
        "AUTHENTICATION_ERROR": _EXA_AUTH_FAILURE_REASONS,
        "NETWORK_ERROR": _EXA_NETWORK_FAILURE_REASONS,
    }.get(code)
    if expected_reasons is not None and (
        provider != "exa" or reason not in expected_reasons
    ):
        return WeChatOAError(
            "INVALID_ERROR_CONTRACT",
            f"wechat-oa returned an invalid {operation} error contract",
            exit_code=completed.returncode,
        )
    return WeChatOAError(
        code,
        f"wechat-oa could not complete {operation}",
        provider=provider,
        reason=reason,
        exit_code=completed.returncode,
    )


def _discovery_result(completed, *, provider: str, operation: str) -> WeChatOAHydrationResult:
    failure = _failure_from_envelope(completed, operation)
    if failure is not None:
        raise failure
    envelope = json.loads(completed.stdout)
    data = envelope.get("data")
    if not isinstance(data, dict) or data.get("schema_version") != "1":
        raise WeChatOAError(
            "UNSUPPORTED_SCHEMA", "wechat-oa returned an unsupported schema"
        )
    candidates = data.get("candidates")
    summary = data.get("summary")
    if (
        not isinstance(candidates, list)
        or len(candidates) > _MAX_CANDIDATES
        or not isinstance(summary, dict)
        or not isinstance(summary.get("partial"), bool)
    ):
        raise WeChatOAError("INVALID_RESULT", "wechat-oa returned an invalid result")
    if provider and data.get("search_provider") != provider:
        raise WeChatOAError(
            "INVALID_RESULT", "wechat-oa returned an unexpected search provider"
        )
    for candidate in candidates:
        provenance = candidate.get("search_provenance") if isinstance(candidate, dict) else None
        parts = urlsplit(str(candidate.get("fetch_url") or "")) if isinstance(candidate, dict) else None
        if (
            not isinstance(candidate, dict)
            or not isinstance(provenance, dict)
            or provenance.get("provider") != provider
            or not isinstance(provenance.get("rank"), int)
            or isinstance(provenance.get("rank"), bool)
            or provenance["rank"] < 1
            or not str(provenance.get("result_id") or "").strip()
            or len(str(provenance.get("result_id") or "")) > 128
            or parts is None
            or parts.scheme != "https"
            or (parts.hostname or "").casefold() != "mp.weixin.qq.com"
            or parts.username
            or parts.password
            or not re.match(r"^/s(?:/|$)", parts.path)
        ):
            raise WeChatOAError(
                "INVALID_RESULT", "wechat-oa returned an invalid discovery candidate"
            )
    verified = tuple(
        item
        for item in candidates
        if item.get("verification_status") == "verified"
        and isinstance(item.get("evidence"), dict)
    )
    return WeChatOAHydrationResult(data, verified, summary["partial"])


def _parse_version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"\s*(\d+)\.(\d+)\.(\d+)(?:[-+].*)?\s*", value)
    if match is None:
        raise WeChatOAError("INVALID_VERSION", "wechat-oa returned an invalid version")
    return tuple(int(item) for item in match.groups())


class WeChatOAClient:
    """Subprocess boundary for wechat-oa Article Evidence JSON."""

    def __init__(
        self,
        executable: str = "wechat-oa",
        *,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ) -> None:
        self.executable = executable
        self.runner = runner

    def version(self) -> tuple[int, int, int]:
        try:
            completed = self.runner(
                [self.executable, "--version"],
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=15,
                check=False,
                env=_scrubbed_subprocess_environment(),
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise WeChatOAError(
                "WECHAT_OA_UNAVAILABLE", "wechat-oa is unavailable"
            ) from error
        if completed.returncode != 0:
            raise WeChatOAError("WECHAT_OA_UNAVAILABLE", "wechat-oa is unavailable")
        version = _parse_version(completed.stdout)
        if version < (0, 4, 0):
            raise WeChatOAError(
                "WECHAT_OA_TOO_OLD", "wechat-oa 0.4.0 or newer is required"
            )
        return version

    def hydrate_candidate_batch(
        self,
        candidate_batch: dict,
        *,
        allow_browser: bool = False,
        timeout_seconds: int = WECHAT_OA_HYDRATION_TIMEOUT_SECONDS,
    ) -> WeChatOAHydrationResult:
        self.version()
        command = [
            self.executable,
            "--json",
            "discovery",
            "hydrate",
            "--input",
            "-",
        ]
        if allow_browser:
            command.append("--browser")
        payload = json.dumps(candidate_batch, ensure_ascii=False, separators=(",", ":"))
        try:
            completed = self.runner(
                command,
                input=payload,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                env=_scrubbed_subprocess_environment(),
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise WeChatOAError(
                "WECHAT_OA_EXEC_FAILED", "wechat-oa execution failed"
            ) from error
        try:
            envelope = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise WeChatOAError(
                "INVALID_JSON", "wechat-oa did not return one JSON document"
            ) from error
        if not isinstance(envelope, dict):
            raise WeChatOAError(
                "INVALID_JSON", "wechat-oa JSON envelope must be an object"
            )
        if completed.returncode != 0 or envelope.get("ok") is not True:
            error_value = envelope.get("error") if isinstance(envelope.get("error"), dict) else {}
            code = str(error_value.get("code") or f"EXIT_{completed.returncode}")
            raise WeChatOAError(code, "wechat-oa could not hydrate the candidate batch")
        data = envelope.get("data")
        if not isinstance(data, dict) or data.get("schema_version") != "1":
            raise WeChatOAError(
                "UNSUPPORTED_SCHEMA", "wechat-oa returned an unsupported schema"
            )
        candidates = data.get("candidates")
        if not isinstance(candidates, list):
            raise WeChatOAError("INVALID_RESULT", "wechat-oa result has no candidate list")
        verified = tuple(
            item
            for item in candidates
            if isinstance(item, dict)
            and item.get("verification_status") == "verified"
            and isinstance(item.get("evidence"), dict)
        )
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        return WeChatOAHydrationResult(data, verified, bool(summary.get("partial")))

    def search_articles_with_exa(
        self,
        *,
        query: str,
        company: str,
        account_names: list[str] | tuple[str, ...],
        published_after: date | str | None = None,
        published_before: date | str | None = None,
        timeout_seconds: int = WECHAT_OA_HYDRATION_TIMEOUT_SECONDS,
    ) -> WeChatOAHydrationResult:
        """Run WeChat OA 0.7 Direct Discovery without browser or media privileges."""

        clean_query = _clean_search_text(query, "query", 500)
        clean_company = _clean_search_text(company, "company", 200)
        clean_accounts = tuple(dict.fromkeys(
            _clean_search_text(value, "account", 200) for value in account_names
        ))
        if not clean_accounts:
            raise WeChatOAError(
                "INVALID_DISCOVERY_REQUEST", "at least one verified account is required"
            )
        if _CREDENTIAL_ASSIGNMENT.search(
            " ".join((clean_query, clean_company, *clean_accounts))
        ):
            raise WeChatOAError(
                "INVALID_DISCOVERY_REQUEST", "discovery text contains credential-like data"
            )
        after = _date_argument(published_after, "published_after")
        before = _date_argument(published_before, "published_before")
        if after and before and after > before:
            raise WeChatOAError(
                "INVALID_DISCOVERY_REQUEST", "published_after must not be after published_before"
            )
        version = self.version()
        if version < WECHAT_OA_EXA_MINIMUM_VERSION:
            raise WeChatOAError(
                "WECHAT_OA_TOO_OLD", "wechat-oa 0.7.0 or newer is required"
            )
        command = [
            self.executable,
            "--json",
            "discovery",
            "search",
            clean_query,
            "--company",
            clean_company,
        ]
        for account in clean_accounts:
            command.extend(("--account", account))
        if after:
            command.extend(("--published-after", after))
        if before:
            command.extend(("--published-before", before))
        command.extend(("--provider", "exa", "--hydrate", "--no-browser"))
        try:
            completed = self.runner(
                command,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                env=_scrubbed_subprocess_environment(),
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise WeChatOAError(
                "WECHAT_OA_EXEC_FAILED",
                "wechat-oa Exa discovery execution failed",
                provider="exa",
                reason="timeout" if isinstance(error, subprocess.TimeoutExpired) else "",
            ) from error
        return _discovery_result(
            completed,
            provider="exa",
            operation="Exa discovery",
        )


def build_wechat_candidate_batch(
    *,
    query: str,
    company: str,
    expected_accounts: list[dict],
    candidates: list[dict],
    providers: list[str],
) -> dict:
    """Build only wechat-oa's public schema-v1 fields; never accepts credentials."""

    query = str(query or "").strip()
    company = str(company or "").strip()
    if not query or len(query) > 500 or not company or len(company) > 200:
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid query or company hint")
    if not isinstance(expected_accounts, list) or len(expected_accounts) > 100:
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid expected account list")
    clean_accounts = []
    for account in expected_accounts:
        if not isinstance(account, dict) or set(account) - {"biz_id", "display_names"}:
            raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid expected account fields")
        names = account.get("display_names", [])
        if not isinstance(names, list) or any(
            not str(name).strip() or len(str(name).strip()) > 200 for name in names
        ):
            raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid account display names")
        clean = {"display_names": [str(name).strip() for name in names]}
        if account.get("biz_id"):
            biz_id = str(account["biz_id"]).strip()
            if len(biz_id) > 512:
                raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid account biz_id")
            clean["biz_id"] = biz_id
        if not clean["display_names"] and not clean.get("biz_id"):
            raise WeChatOAError(
                "INVALID_CANDIDATE_BATCH", "expected account has no identity hint"
            )
        clean_accounts.append(clean)
    if not isinstance(providers, list) or not providers or any(
        not _IDENTIFIER.fullmatch(str(provider or "").strip()) for provider in providers
    ):
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid discovery providers")
    if not isinstance(candidates, list) or len(candidates) > _MAX_CANDIDATES:
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "too many WeChat candidates")
    clean_candidates = []
    for candidate in candidates:
        allowed = {"url", "title_hint", "snippet", "backend_date_hint", "search_provenance"}
        if not isinstance(candidate, dict) or set(candidate) - allowed:
            raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid WeChat candidate fields")
        url = str(candidate.get("url") or "").strip()
        parts = urlsplit(url)
        if (
            parts.scheme != "https"
            or (parts.hostname or "").casefold() != "mp.weixin.qq.com"
            or parts.username
            or parts.password
            or not re.match(r"^/s(?:/|$)", parts.path)
        ):
            raise WeChatOAError(
                "INVALID_CANDIDATE_BATCH",
                "candidate is not a public WeChat article URL",
            )
        provenance = candidate.get("search_provenance")
        if not isinstance(provenance, dict) or set(provenance) != {"provider", "rank", "result_id"}:
            raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid candidate provenance")
        try:
            rank = int(provenance["rank"])
        except (TypeError, ValueError) as error:
            raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid candidate rank") from error
        provider = str(provenance["provider"] or "").strip()
        result_id = str(provenance["result_id"] or "").strip()
        if provider not in providers or rank < 1 or len(result_id) > 128:
            raise WeChatOAError(
                "INVALID_CANDIDATE_BATCH", "candidate provenance was not declared"
            )
        title_hint = str(candidate.get("title_hint") or "").strip()
        snippet = str(candidate.get("snippet") or "").strip()
        backend_date_hint = str(candidate.get("backend_date_hint") or "").strip()
        if len(title_hint) > 500 or len(snippet) > 2000 or len(backend_date_hint) > 64:
            raise WeChatOAError("INVALID_CANDIDATE_BATCH", "candidate metadata is too large")
        clean_candidates.append({
            "url": url,
            "title_hint": title_hint,
            "snippet": snippet,
            "backend_date_hint": backend_date_hint or None,
            "search_provenance": {
                "provider": provider,
                "rank": rank,
                "result_id": result_id,
            },
        })
    payload = {
        "schema_version": "1",
        "discovery_request": {
            "query": query,
            "companies": [company],
            "expected_accounts": clean_accounts,
        },
        "source": {
            "orchestrator": "codex",
            "providers": list(dict.fromkeys(providers)),
        },
        "candidates": clean_candidates,
        "hydration": {
            "priority_count": min(10, len(candidates)),
            "maximum_attempts": min(20, len(candidates)),
        },
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > _MAX_DOCUMENT_BYTES or _CREDENTIAL_ASSIGNMENT.search(
        encoded.decode("utf-8", errors="ignore")
    ):
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "candidate batch contains unsafe data")
    return payload


def validate_wechat_candidate_batch(payload: object) -> dict:
    """Validate and canonicalize one operator-supplied wechat-oa Candidate Batch."""

    if not isinstance(payload, dict):
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "candidate batch must be an object")
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > _MAX_DOCUMENT_BYTES or _CREDENTIAL_ASSIGNMENT.search(
        encoded.decode("utf-8", errors="ignore")
    ):
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "candidate batch contains unsafe data")
    if set(payload) != {
        "schema_version",
        "discovery_request",
        "source",
        "candidates",
        "hydration",
    } or payload.get("schema_version") != "1":
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid candidate batch fields")
    request = payload.get("discovery_request")
    source = payload.get("source")
    hydration = payload.get("hydration")
    if (
        not isinstance(request, dict)
        or set(request) != {"query", "companies", "expected_accounts"}
        or not isinstance(request.get("companies"), list)
        or len(request["companies"]) != 1
        or not isinstance(source, dict)
        or set(source) != {"orchestrator", "providers"}
        or source.get("orchestrator") != "codex"
        or not isinstance(hydration, dict)
        or set(hydration) != {"priority_count", "maximum_attempts"}
    ):
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "invalid candidate batch structure")
    canonical = build_wechat_candidate_batch(
        query=request.get("query"),
        company=request["companies"][0],
        expected_accounts=request.get("expected_accounts"),
        candidates=payload.get("candidates"),
        providers=source.get("providers"),
    )
    if payload != canonical:
        raise WeChatOAError("INVALID_CANDIDATE_BATCH", "candidate batch is not canonical")
    return canonical
