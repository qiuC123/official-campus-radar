from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlsplit


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?key|cookie|authorization|password|secret|token)\s*[:=]"
)
_MAX_CANDIDATES = 100
_MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
WXCLI_HYDRATION_TIMEOUT_SECONDS = 660


class WxCliError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class WxCliHydrationResult:
    data: dict
    verified_candidates: tuple[dict, ...]
    partial: bool

    @property
    def verified_evidence(self) -> tuple[dict, ...]:
        return tuple(item["evidence"] for item in self.verified_candidates)


def _parse_version(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"\s*(\d+)\.(\d+)\.(\d+)(?:[-+].*)?\s*", value)
    if match is None:
        raise WxCliError("INVALID_VERSION", "wxcli returned an invalid version")
    return tuple(int(item) for item in match.groups())


class WxCliClient:
    """Subprocess boundary for wxcli 0.4 Article Evidence JSON."""

    def __init__(
        self,
        executable: str = "wxcli",
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
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise WxCliError("WXCLI_UNAVAILABLE", "wxcli is unavailable") from error
        if completed.returncode != 0:
            raise WxCliError("WXCLI_UNAVAILABLE", "wxcli is unavailable")
        version = _parse_version(completed.stdout)
        if version < (0, 4, 0):
            raise WxCliError("WXCLI_TOO_OLD", "wxcli 0.4.0 or newer is required")
        return version

    def hydrate_candidate_batch(
        self,
        candidate_batch: dict,
        *,
        allow_browser: bool = False,
        timeout_seconds: int = WXCLI_HYDRATION_TIMEOUT_SECONDS,
    ) -> WxCliHydrationResult:
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
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise WxCliError("WXCLI_EXEC_FAILED", "wxcli execution failed") from error
        try:
            envelope = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise WxCliError("INVALID_JSON", "wxcli did not return one JSON document") from error
        if not isinstance(envelope, dict):
            raise WxCliError("INVALID_JSON", "wxcli JSON envelope must be an object")
        if completed.returncode != 0 or envelope.get("ok") is not True:
            error_value = envelope.get("error") if isinstance(envelope.get("error"), dict) else {}
            code = str(error_value.get("code") or f"EXIT_{completed.returncode}")
            raise WxCliError(code, "wxcli could not hydrate the candidate batch")
        data = envelope.get("data")
        if not isinstance(data, dict) or data.get("schema_version") != "1":
            raise WxCliError("UNSUPPORTED_SCHEMA", "wxcli returned an unsupported schema")
        candidates = data.get("candidates")
        if not isinstance(candidates, list):
            raise WxCliError("INVALID_RESULT", "wxcli result has no candidate list")
        verified = tuple(
            item
            for item in candidates
            if isinstance(item, dict)
            and item.get("verification_status") == "verified"
            and isinstance(item.get("evidence"), dict)
        )
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        return WxCliHydrationResult(data, verified, bool(summary.get("partial")))


def build_wechat_candidate_batch(
    *,
    query: str,
    company: str,
    expected_accounts: list[dict],
    candidates: list[dict],
    providers: list[str],
) -> dict:
    """Build only wxcli's public schema-v1 fields; never accepts credentials."""

    query = str(query or "").strip()
    company = str(company or "").strip()
    if not query or len(query) > 500 or not company or len(company) > 200:
        raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid query or company hint")
    if not isinstance(expected_accounts, list) or len(expected_accounts) > 100:
        raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid expected account list")
    clean_accounts = []
    for account in expected_accounts:
        if not isinstance(account, dict) or set(account) - {"biz_id", "display_names"}:
            raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid expected account fields")
        names = account.get("display_names", [])
        if not isinstance(names, list) or any(
            not str(name).strip() or len(str(name).strip()) > 200 for name in names
        ):
            raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid account display names")
        clean = {"display_names": [str(name).strip() for name in names]}
        if account.get("biz_id"):
            biz_id = str(account["biz_id"]).strip()
            if len(biz_id) > 512:
                raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid account biz_id")
            clean["biz_id"] = biz_id
        if not clean["display_names"] and not clean.get("biz_id"):
            raise WxCliError("INVALID_CANDIDATE_BATCH", "expected account has no identity hint")
        clean_accounts.append(clean)
    if not isinstance(providers, list) or not providers or any(
        not _IDENTIFIER.fullmatch(str(provider or "").strip()) for provider in providers
    ):
        raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid discovery providers")
    if not isinstance(candidates, list) or len(candidates) > _MAX_CANDIDATES:
        raise WxCliError("INVALID_CANDIDATE_BATCH", "too many WeChat candidates")
    clean_candidates = []
    for candidate in candidates:
        allowed = {"url", "title_hint", "snippet", "backend_date_hint", "search_provenance"}
        if not isinstance(candidate, dict) or set(candidate) - allowed:
            raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid WeChat candidate fields")
        url = str(candidate.get("url") or "").strip()
        parts = urlsplit(url)
        if (
            parts.scheme != "https"
            or (parts.hostname or "").casefold() != "mp.weixin.qq.com"
            or parts.username
            or parts.password
            or not re.match(r"^/s(?:/|$)", parts.path)
        ):
            raise WxCliError("INVALID_CANDIDATE_BATCH", "candidate is not a public WeChat article URL")
        provenance = candidate.get("search_provenance")
        if not isinstance(provenance, dict) or set(provenance) != {"provider", "rank", "result_id"}:
            raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid candidate provenance")
        try:
            rank = int(provenance["rank"])
        except (TypeError, ValueError) as error:
            raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid candidate rank") from error
        provider = str(provenance["provider"] or "").strip()
        result_id = str(provenance["result_id"] or "").strip()
        if provider not in providers or rank < 1 or len(result_id) > 128:
            raise WxCliError("INVALID_CANDIDATE_BATCH", "candidate provenance was not declared")
        title_hint = str(candidate.get("title_hint") or "").strip()
        snippet = str(candidate.get("snippet") or "").strip()
        backend_date_hint = str(candidate.get("backend_date_hint") or "").strip()
        if len(title_hint) > 500 or len(snippet) > 2000 or len(backend_date_hint) > 64:
            raise WxCliError("INVALID_CANDIDATE_BATCH", "candidate metadata is too large")
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
        raise WxCliError("INVALID_CANDIDATE_BATCH", "candidate batch contains unsafe data")
    return payload


def validate_wechat_candidate_batch(payload: object) -> dict:
    """Validate and canonicalize one operator-supplied wxcli Candidate Batch."""

    if not isinstance(payload, dict):
        raise WxCliError("INVALID_CANDIDATE_BATCH", "candidate batch must be an object")
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > _MAX_DOCUMENT_BYTES or _CREDENTIAL_ASSIGNMENT.search(
        encoded.decode("utf-8", errors="ignore")
    ):
        raise WxCliError("INVALID_CANDIDATE_BATCH", "candidate batch contains unsafe data")
    if set(payload) != {
        "schema_version",
        "discovery_request",
        "source",
        "candidates",
        "hydration",
    } or payload.get("schema_version") != "1":
        raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid candidate batch fields")
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
        raise WxCliError("INVALID_CANDIDATE_BATCH", "invalid candidate batch structure")
    canonical = build_wechat_candidate_batch(
        query=request.get("query"),
        company=request["companies"][0],
        expected_accounts=request.get("expected_accounts"),
        candidates=payload.get("candidates"),
        providers=source.get("providers"),
    )
    if payload != canonical:
        raise WxCliError("INVALID_CANDIDATE_BATCH", "candidate batch is not canonical")
    return canonical
