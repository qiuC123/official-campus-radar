import hashlib
import json
from dataclasses import replace
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from radar.models import AnnouncementDiscoveryCandidate, Organization
from radar.services.announcement_discovery import (
    DiscoveryContractError,
    discover_official_candidates_with_codex,
    fetch_official_candidate_for_verification,
    known_source_candidate_batch,
    parse_official_candidate_batch,
)
from radar.services.exa_discovery import (
    AnnouncementDiscoveryOrchestrator,
    CompanyDiscoveryResult,
    DiscoveryBatchResult,
    DiscoveryObservation,
    ExaDiscoveryError,
    MergedCandidate,
    ProviderAttempt,
    SearchCriteria,
    build_exa_client_from_environment,
    merge_observations,
    parse_discovery_result_document,
    persist_discovery_result,
    route_candidate,
)


def _parse_date(value: str | None, label: str) -> date:
    try:
        return date.fromisoformat(str(value or ""))
    except ValueError as error:
        raise CommandError(f"{label} must use YYYY-MM-DD") from error


def _criteria_from_options(options) -> SearchCriteria:
    audiences = tuple(dict.fromkeys(options.get("audience") or ()))
    recruitment_types = tuple(dict.fromkeys(options.get("recruitment_type") or ()))
    if not audiences or not recruitment_types:
        raise CommandError(
            "live search and recorded input require --audience and --recruitment-type"
        )
    try:
        return SearchCriteria(
            audiences=audiences,
            recruitment_types=recruitment_types,
            published_after=_parse_date(options.get("published_after"), "--published-after"),
            published_before=_parse_date(options.get("published_before"), "--published-before"),
        )
    except ValueError as error:
        raise CommandError(str(error)) from error


def _candidate_dict(candidate: MergedCandidate) -> dict:
    return {
        "fetch_url": candidate.fetch_url,
        "identity_url": candidate.identity_url,
        "title_hint": candidate.title_hint,
        "backend_date_hint": candidate.backend_date_hint or None,
        "route_state": candidate.route_state,
        "qualified": candidate.qualified,
        "rejection_code": candidate.rejection_code or None,
        "observations": [
            {
                "query": observation.query,
                "provider": observation.provider,
                "rank": observation.rank,
                "result_id": observation.result_id,
                "intent_key": observation.intent_key,
                "request_key": observation.request_key,
                "discovered_at": observation.discovered_at.isoformat(),
            }
            for observation in candidate.observations
        ],
    }


def _result_dict(result: DiscoveryBatchResult, *, recorded_run_id=None) -> dict:
    return {
        "schema_version": "2",
        "ok": result.status == "complete",
        "status": result.status,
        "recorded_run_id": recorded_run_id,
        "criteria": result.criteria.as_dict(),
        "companies": [
            {
                "company": company.organization.name,
                "status": company.status,
                "fallback_reason": company.fallback_reason or None,
                "error_code": company.error_code or None,
                "attempts": [
                    {
                        "provider": attempt.provider,
                        "status": attempt.status,
                        "intent_key": attempt.intent_key,
                        "query": attempt.query,
                        "request_key": attempt.request_key,
                        "request_id": attempt.request_id or None,
                        "duration_ms": attempt.duration_ms,
                        "result_count": attempt.result_count,
                        "cost_dollars": attempt.cost_dollars,
                        "error_code": attempt.error_code or None,
                    }
                    for attempt in company.attempts
                ],
                "candidates": [_candidate_dict(item) for item in company.candidates],
            }
            for company in result.companies
        ],
    }


def _legacy_batch_result(organization, batch, criteria) -> DiscoveryBatchResult:
    intent_payload = json.dumps(
        [organization.pk, criteria.as_dict()],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    intent_key = hashlib.sha256(intent_payload.encode("utf-8")).hexdigest()[:32]
    observations = tuple(
        DiscoveryObservation(
            intent_key=intent_key,
            query=batch.query,
            url=candidate.url,
            title_hint=candidate.title_hint,
            snippet="",
            backend_date_hint="",
            provider=candidate.provider,
            rank=candidate.rank,
            result_id=candidate.result_id or hashlib.sha256(candidate.url.encode()).hexdigest(),
            request_key=hashlib.sha256(
                f"legacy:{candidate.provider}:{batch.query}".encode("utf-8")
            ).hexdigest(),
        )
        for candidate in batch.candidates
    )
    candidates = tuple(
        route_candidate(organization, item, criteria=criteria)
        for item in merge_observations(observations)
    )
    attempt = ProviderAttempt(
        provider=batch.providers[0],
        intent_key=intent_key,
        query=batch.query,
        status="success" if observations else "empty",
        request_key=hashlib.sha256(
            f"legacy:{batch.providers[0]}:{batch.query}".encode("utf-8")
        ).hexdigest(),
        result_count=len(observations),
    )
    now = timezone.now()
    return DiscoveryBatchResult(
        criteria=criteria,
        status="complete",
        companies=(CompanyDiscoveryResult(
            organization=organization,
            status="complete",
            candidates=candidates,
            attempts=(attempt,),
        ),),
        started_at=now,
        completed_at=now,
    )


class Command(BaseCommand):
    help = "Exa-first 发现官网/ATS 公告候选；默认只预演，不直接准入。"

    def add_arguments(self, parser):
        parser.add_argument("--organization", action="append")
        parser.add_argument("--batch-file", help="包含企业名称数组的 UTF-8 JSON")
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--max-companies", type=int)
        parser.add_argument("--input", help="已生成的 OfficialSiteCandidateBatch JSON")
        parser.add_argument("--audience", action="append")
        parser.add_argument("--recruitment-type", action="append")
        parser.add_argument("--published-after")
        parser.add_argument("--published-before")
        parser.add_argument("--allow-live-search", action="store_true")
        parser.add_argument("--allow-codex-fallback", action="store_true")
        parser.add_argument("--allow-live-fetch", action="store_true")
        parser.add_argument("--record", action="store_true")
        parser.add_argument("--codex-path", default="codex")

    def _organization_names(self, options) -> list[str]:
        raw = options.get("organization") or []
        if isinstance(raw, str):
            raw = [raw]
        selectors = bool(raw) + bool(options.get("batch_file")) + bool(options.get("all"))
        if selectors != 1:
            raise CommandError(
                "provide exactly one of --organization, --batch-file, or --all"
            )
        if options.get("all"):
            maximum = options.get("max_companies")
            if maximum is None or not 1 <= maximum <= 8:
                raise CommandError("--all requires --max-companies between 1 and 8")
            names = list(
                Organization.objects.order_by("name").values_list("name", flat=True)[:maximum]
            )
        elif options.get("batch_file"):
            try:
                payload = json.loads(Path(options["batch_file"]).read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise CommandError("--batch-file must contain UTF-8 JSON") from error
            if not isinstance(payload, list) or any(not isinstance(item, str) for item in payload):
                raise CommandError("--batch-file must contain a JSON string array")
            names = payload
        else:
            names = raw
        names = list(dict.fromkeys(value.strip() for value in names if value.strip()))
        if not names or len(names) > 8:
            raise CommandError("discovery requires 1 to 8 unique organizations")
        if options.get("max_companies") is not None and len(names) > options["max_companies"]:
            raise CommandError("selected organizations exceed --max-companies")
        return names

    def _organizations(self, options) -> list[Organization]:
        names = self._organization_names(options)
        organizations = list(Organization.objects.filter(name__in=names))
        by_name = {item.name: item for item in organizations}
        missing = [name for name in names if name not in by_name]
        if missing:
            raise CommandError(f"organization not found: {', '.join(missing)}")
        return [by_name[name] for name in names]

    def _known_source_result(self, organization, criteria, *, allow_live_fetch):
        batch = known_source_candidate_batch(organization)
        if not batch.candidates:
            return None
        existing = {
            item.url: item
            for item in AnnouncementDiscoveryCandidate.objects.filter(
                organization=organization,
                url__in=[candidate.url for candidate in batch.candidates],
            )
        }
        observations = []
        qualified_urls = set()
        for candidate in batch.candidates:
            stored = existing.get(candidate.url)
            title = candidate.title_hint
            qualified = bool(
                stored
                and (
                    stored.recruitment_signal_found
                    or stored.state == AnnouncementDiscoveryCandidate.State.VERIFIED
                )
            )
            if not qualified and allow_live_fetch:
                try:
                    fetched = fetch_official_candidate_for_verification(
                        organization,
                        candidate,
                        allow_browser=False,
                    )
                except Exception:
                    fetched = None
                if fetched is not None:
                    title = fetched.title or title
                    qualified = fetched.recruitment_signal_found
            request_key = hashlib.sha256(
                f"known:{organization.pk}:{candidate.url}".encode("utf-8")
            ).hexdigest()
            observations.append(DiscoveryObservation(
                intent_key=request_key[:32],
                query=batch.query,
                url=candidate.url,
                title_hint=title,
                snippet="",
                backend_date_hint="",
                provider="known_source",
                rank=candidate.rank,
                result_id=candidate.result_id,
                request_key=request_key,
            ))
            if qualified:
                qualified_urls.add(candidate.url)
        if not qualified_urls:
            return None
        routed = []
        for candidate in merge_observations(observations):
            item = route_candidate(organization, candidate, criteria=criteria)
            if candidate.fetch_url in qualified_urls:
                item = replace(item, qualified=True)
            routed.append(item)
        return CompanyDiscoveryResult(
            organization=organization,
            status="complete",
            candidates=tuple(routed),
            attempts=(ProviderAttempt(
                provider="known_source",
                intent_key="known_source",
                query=batch.query,
                status="success",
                request_key=hashlib.sha256(
                    f"known:{organization.pk}:{batch.query}".encode("utf-8")
                ).hexdigest(),
                result_count=len(routed),
            ),),
        )

    def _codex_searcher(self, codex_path):
        def search(organization, plans, candidates, *, timeout_seconds):
            batch = discover_official_candidates_with_codex(
                organization,
                codex_path=codex_path,
                timeout_seconds=timeout_seconds,
                search_queries=(plan.query for plan in plans),
                published_after=min(plan.published_after for plan in plans).isoformat(),
                published_before=max(plan.published_before for plan in plans).isoformat(),
                candidate_context=(
                    {
                        "url": candidate.identity_url,
                        "title_hint": candidate.title_hint,
                        "route_state": candidate.route_state,
                        "rejection_code": candidate.rejection_code,
                    }
                    for candidate in candidates
                ),
            )
            intent_key = plans[0].intent_key
            request_key = hashlib.sha256(
                f"codex:{organization.pk}:{intent_key}".encode("utf-8")
            ).hexdigest()
            return tuple(
                DiscoveryObservation(
                    intent_key=intent_key,
                    query=batch.query,
                    url=candidate.url,
                    title_hint=candidate.title_hint,
                    snippet="",
                    backend_date_hint="",
                    provider="codex_web_search",
                    rank=candidate.rank,
                    result_id=candidate.result_id,
                    request_key=request_key,
                )
                for candidate in batch.candidates
            )
        return search

    def handle(self, *args, **options):
        organizations = self._organizations(options)
        if options.get("input") and len(organizations) != 1:
            raise CommandError("--input requires exactly one --organization")
        if options.get("input") and (
            options.get("allow_live_search")
            or options.get("allow_codex_fallback")
            or options.get("allow_live_fetch")
        ):
            raise CommandError("--input cannot be combined with live permissions")
        if options.get("allow_codex_fallback") and not options.get("allow_live_search"):
            raise CommandError("--allow-codex-fallback requires --allow-live-search")

        if options.get("input"):
            try:
                raw = Path(options["input"]).read_bytes()
                envelope = json.loads(raw)
                schema_version = envelope.get("schema_version") if isinstance(envelope, dict) else None
                if schema_version == "2":
                    result = parse_discovery_result_document(raw, organizations)
                    if options.get("record"):
                        run = persist_discovery_result(result)
                        output = _result_dict(result, recorded_run_id=run.pk)
                        output["status"] = run.status
                        output["ok"] = run.status == "complete"
                    else:
                        output = _result_dict(result)
                    self.stdout.write(json.dumps(output, ensure_ascii=False))
                    return
                batch = parse_official_candidate_batch(raw)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, DiscoveryContractError, ValueError) as error:
                raise CommandError(type(error).__name__) from error
            if options.get("record"):
                criteria = _criteria_from_options(options)
                result = _legacy_batch_result(organizations[0], batch, criteria)
                run = persist_discovery_result(result)
                output = _result_dict(result, recorded_run_id=run.pk)
                output["status"] = run.status
                output["ok"] = run.status == "complete"
            else:
                output = {
                    "schema_version": "1",
                    "ok": True,
                    "status": "preview",
                    "recorded_run_id": None,
                    "company": organizations[0].name,
                    "candidate_count": len(batch.candidates),
                }
            self.stdout.write(json.dumps(output, ensure_ascii=False))
            return

        if not options.get("allow_live_search"):
            preview = {
                "schema_version": "2",
                "ok": True,
                "status": "preview",
                "recorded_run_id": None,
                "companies": [
                    {
                        "company": organization.name,
                        "known_source_candidates": len(
                            known_source_candidate_batch(organization).candidates
                        ),
                    }
                    for organization in organizations
                ],
            }
            self.stdout.write(json.dumps(preview, ensure_ascii=False))
            return

        criteria = _criteria_from_options(options)
        started_at = timezone.now()
        known_results = {}
        search_organizations = []
        for organization in organizations:
            known = self._known_source_result(
                organization,
                criteria,
                allow_live_fetch=options.get("allow_live_fetch", False),
            )
            if known is None:
                search_organizations.append(organization)
            else:
                known_results[organization.pk] = known

        searched = None
        if search_organizations:
            try:
                exa_client = build_exa_client_from_environment()
            except ExaDiscoveryError as error:
                output = {
                    "schema_version": "2",
                    "ok": False,
                    "status": "failed",
                    "error_code": error.code,
                    "companies": [],
                }
                self.stdout.write(json.dumps(output, ensure_ascii=False))
                raise CommandError("official announcement discovery failed") from error
            searched = AnnouncementDiscoveryOrchestrator(
                exa_client=exa_client,
                codex_searcher=(
                    self._codex_searcher(options["codex_path"])
                    if options.get("allow_codex_fallback")
                    else None
                ),
            ).discover(
                search_organizations,
                criteria,
                allow_codex_fallback=options.get("allow_codex_fallback", False),
            )
        searched_by_id = {
            item.organization.pk: item
            for item in (searched.companies if searched is not None else ())
        }
        company_results = tuple(
            known_results.get(organization.pk) or searched_by_id[organization.pk]
            for organization in organizations
        )
        if all(item.status == "failed" for item in company_results):
            status = "failed"
        elif any(item.status in {"failed", "degraded"} for item in company_results):
            status = "partial"
        else:
            status = "complete"
        result = DiscoveryBatchResult(
            criteria=criteria,
            status=status,
            companies=company_results,
            started_at=started_at,
            completed_at=timezone.now(),
        )
        recorded_run_id = None
        if options.get("record"):
            recorded_run = persist_discovery_result(result)
            recorded_run_id = recorded_run.pk
        output = _result_dict(result, recorded_run_id=recorded_run_id)
        if options.get("record"):
            output["status"] = recorded_run.status
            output["ok"] = recorded_run.status == "complete"
        self.stdout.write(json.dumps(output, ensure_ascii=False))
        if output["status"] != "complete":
            raise CommandError("official announcement discovery did not complete successfully")
