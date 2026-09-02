import json
import os
import subprocess
from pathlib import Path
from datetime import date
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch
from tempfile import TemporaryDirectory

import requests
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from radar.models import (
    AnnouncementDiscoveryCandidate,
    AnnouncementDiscoveryObservation,
    AnnouncementDiscoveryOrganizationRun,
    AnnouncementDiscoveryRun,
    AnnouncementDiscoveryProviderAttempt,
    OfficialSource,
    Organization,
)
from radar.management.commands.discover_official_announcements import _result_dict
from radar.services.exa_discovery import (
    AnnouncementDiscoveryOrchestrator,
    AnnouncementSearchPlanner,
    DiscoveryObservation,
    ExaDiscoveryClient,
    ExaDiscoveryError,
    ProviderQueryResult,
    SearchCriteria,
    build_exa_client_from_environment,
    merge_observations,
    normalize_discovery_url,
    parse_discovery_result_document,
    persist_discovery_result,
    rank_discovery_candidates,
    route_candidate,
)
from radar.services.announcement_discovery import (
    OfficialSiteCandidate,
    RefetchedOfficialCandidate,
    discover_official_candidates_with_codex,
    refetch_official_candidate,
    scrubbed_discovery_subprocess_environment,
    _codex_command_prefix,
)
from radar.services.announcements import verify_official_announcement
from radar.tests.helpers import create_enabled_source
from campus_radar.environment import load_project_exa_key


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None, raw_bytes=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._raw_bytes = (
            raw_bytes
            if raw_bytes is not None
            else json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        )

    def iter_content(self, chunk_size=65536):
        for offset in range(0, len(self._raw_bytes), chunk_size):
            yield self._raw_bytes[offset : offset + chunk_size]

    def close(self):
        return None


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.trust_env = True

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class ExaClientTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="星河科技",
            aliases=["星河招聘"],
            company_type=Organization.CompanyType.PRIVATE,
            industry="互联网/科技",
            official_domain="xinghe.example",
        )
        self.criteria = SearchCriteria(
            audiences=("2027届",),
            recruitment_types=("秋招",),
            published_after=date(2026, 6, 1),
            published_before=date(2026, 12, 31),
        )
        self.plan = AnnouncementSearchPlanner().plan(
            self.organization, self.criteria
        )[0]

    def test_search_uses_fixed_endpoint_bearer_auth_and_bounded_highlights(self):
        transport = FakeTransport([
            FakeResponse(
                payload={
                    "requestId": "exa-request-1",
                    "costDollars": {"total": 0.001},
                    "results": [{
                        "id": "exa-result-1",
                        "url": "https://xinghe.example/campus?utm_source=exa&project=2027",
                        "title": "星河科技 2027届秋季校园招聘",
                        "publishedDate": "2026-08-01T00:00:00.000Z",
                        "highlights": ["星河科技面向2027届毕业生启动秋招"],
                        "ignoredFutureField": {"safe": True},
                    }],
                    "ignoredEnvelopeField": True,
                },
                headers={"x-request-id": "header-request-id"},
            )
        ])
        client = ExaDiscoveryClient(
            api_key="test-only-key",
            transport=transport,
            sleeper=lambda _seconds: None,
        )

        result = client.search(self.plan)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.request_id, "exa-request-1")
        self.assertEqual(result.cost_dollars, 0.001)
        self.assertEqual(result.observations[0].provider, "exa")
        self.assertEqual(result.observations[0].result_id, "exa-result-1")
        url, kwargs = transport.calls[0]
        self.assertEqual(url, "https://api.exa.ai/search")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-only-key")
        self.assertNotIn("x-api-key", kwargs["headers"])
        self.assertFalse(kwargs["allow_redirects"])
        self.assertTrue(kwargs["stream"])
        self.assertEqual(kwargs["timeout"], (5, 20))
        self.assertEqual(kwargs["json"]["numResults"], 10)
        self.assertEqual(
            kwargs["json"]["contents"]["highlights"]["maxCharacters"],
            1000,
        )
        self.assertEqual(
            kwargs["json"]["startPublishedDate"],
            "2026-06-01T00:00:00.000Z",
        )
        self.assertFalse(transport.trust_env)

    def test_429_retries_once_and_honors_capped_retry_after(self):
        sleeps = []
        transport = FakeTransport([
            FakeResponse(status_code=429, headers={"Retry-After": "60"}),
            FakeResponse(payload={"requestId": "retry-ok", "results": []}),
        ])
        client = ExaDiscoveryClient(
            api_key="test-only-key",
            transport=transport,
            sleeper=sleeps.append,
        )

        result = client.search(self.plan)

        self.assertEqual(result.status, "empty")
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(sleeps, [10])

    def test_auth_contract_and_oversized_response_are_permanent_errors(self):
        for response, expected_code in (
            (FakeResponse(status_code=401), "AUTH_INVALID"),
            (FakeResponse(raw_bytes=b"x" * (1024 * 1024 + 1)), "RESPONSE_TOO_LARGE"),
        ):
            client = ExaDiscoveryClient(
                api_key="test-only-key",
                transport=FakeTransport([response]),
                sleeper=lambda _seconds: None,
            )
            with self.assertRaises(ExaDiscoveryError) as raised:
                client.search(self.plan)
            self.assertEqual(raised.exception.code, expected_code)
            self.assertFalse(raised.exception.fallback_allowed)

    def test_timeout_after_retry_is_fallback_eligible(self):
        transport = FakeTransport([
            requests.Timeout("first"),
            requests.Timeout("second"),
        ])
        client = ExaDiscoveryClient(
            api_key="test-only-key",
            transport=transport,
            sleeper=lambda _seconds: None,
        )
        with self.assertRaises(ExaDiscoveryError) as raised:
            client.search(self.plan)
        self.assertEqual(raised.exception.code, "TIMEOUT")
        self.assertTrue(raised.exception.fallback_allowed)

    def test_missing_key_invalid_json_and_5xx_have_stable_error_classes(self):
        with self.assertRaises(ExaDiscoveryError) as missing:
            build_exa_client_from_environment({})
        self.assertEqual(missing.exception.code, "API_KEY_MISSING")
        self.assertFalse(missing.exception.fallback_allowed)

        invalid_json = ExaDiscoveryClient(
            api_key="test-only-key",
            transport=FakeTransport([FakeResponse(raw_bytes=b"not-json")]),
        )
        with self.assertRaises(ExaDiscoveryError) as invalid:
            invalid_json.search(self.plan)
        self.assertEqual(invalid.exception.code, "INVALID_JSON")
        self.assertFalse(invalid.exception.fallback_allowed)

        server_error = ExaDiscoveryClient(
            api_key="test-only-key",
            transport=FakeTransport([
                FakeResponse(status_code=503),
                FakeResponse(status_code=503),
            ]),
            sleeper=lambda _seconds: None,
        )
        with self.assertRaises(ExaDiscoveryError) as unavailable:
            server_error.search(self.plan)
        self.assertEqual(unavailable.exception.code, "SERVER_ERROR")
        self.assertTrue(unavailable.exception.fallback_allowed)


class SearchPlanningAndRoutingTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="银河制造",
            aliases=["银河校招", "银河招聘"],
            company_type=Organization.CompanyType.PRIVATE,
            industry="制造业",
            official_domain="galaxy.example",
        )
        OfficialSource.objects.create(
            organization=self.organization,
            source_type=OfficialSource.SourceType.ATS,
            source_url="https://jobs.galaxy-ats.example/campus",
            admission_evidence="测试 ATS",
            is_verified=True,
            is_active=True,
            admission_state=OfficialSource.AdmissionState.ENABLED,
        )
        self.criteria = SearchCriteria(
            audiences=("2027届",),
            recruitment_types=("秋招",),
            published_after=date(2026, 6, 1),
            published_before=date(2026, 12, 31),
        )

    def observation(self, url, *, title="银河制造 2027届秋招", provider="exa", rank=1):
        return DiscoveryObservation(
            intent_key="intent-1",
            query="银河制造 2027届 秋招",
            url=url,
            title_hint=title,
            snippet="银河制造校园招聘正式启动",
            backend_date_hint="2026-08-01",
            provider=provider,
            rank=rank,
            result_id=f"{provider}-{rank}",
        )

    def test_planner_is_deterministic_and_uses_explicit_scope(self):
        planner = AnnouncementSearchPlanner(max_queries_per_company=4)
        first = planner.plan(self.organization, self.criteria)
        second = planner.plan(self.organization, self.criteria)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 2)
        self.assertIn("2027届", first[0].query)
        self.assertIn("秋招", first[0].query)
        self.assertIn("银河校招", first[0].query)
        self.assertFalse(first[0].include_domains)
        self.assertIn("galaxy.example", first[1].include_domains)

    def test_url_identity_removes_only_tracking_parameters(self):
        normalized = normalize_discovery_url(
            "HTTPS://GALAXY.EXAMPLE:443/Campus/Apply?utm_source=exa&project=2027&from=portal#jobs"
        )
        self.assertEqual(
            normalized.fetch_url,
            "https://galaxy.example/Campus/Apply?utm_source=exa&project=2027&from=portal",
        )
        self.assertEqual(
            normalized.identity_url,
            "https://galaxy.example/Campus/Apply?project=2027&from=portal",
        )

    def test_merge_preserves_exa_and_codex_observations(self):
        exa = self.observation("https://galaxy.example/campus?utm_source=exa")
        codex = self.observation(
            "https://galaxy.example/campus",
            provider="codex_web_search",
            rank=2,
        )
        merged = merge_observations((exa, codex))
        self.assertEqual(len(merged), 1)
        self.assertEqual(
            {item.provider for item in merged[0].observations},
            {"exa", "codex_web_search"},
        )

    def test_routing_separates_known_source_unknown_ats_and_aggregator(self):
        known = route_candidate(
            self.organization,
            merge_observations((self.observation("https://galaxy.example/campus/2027"),))[0],
            criteria=self.criteria,
        )
        unknown_ats = route_candidate(
            self.organization,
            merge_observations((self.observation("https://galaxy.mokahr.com/campus/2027"),))[0],
            criteria=self.criteria,
        )
        aggregator = route_candidate(
            self.organization,
            merge_observations((self.observation("https://www.nowcoder.com/jobs/galaxy"),))[0],
            criteria=self.criteria,
        )
        self.assertEqual(known.route_state, "known_official")
        self.assertTrue(known.qualified)
        self.assertEqual(unknown_ats.route_state, "source_identity_review_required")
        self.assertFalse(unknown_ats.qualified)
        self.assertEqual(aggregator.route_state, "rejected")

    def test_broad_corporate_domain_does_not_admit_arbitrary_subdomain(self):
        news = route_candidate(
            self.organization,
            merge_observations((
                self.observation("https://news.galaxy.example/2027-campus"),
            ))[0],
            criteria=self.criteria,
        )
        self.assertEqual(news.route_state, "rejected")
        self.assertFalse(news.qualified)

    def test_known_source_candidate_ranks_ahead_of_exa_aggregator(self):
        aggregator = route_candidate(
            self.organization,
            merge_observations((
                self.observation("https://www.nowcoder.com/jobs/galaxy", rank=1),
            ))[0],
            criteria=self.criteria,
        )
        known = route_candidate(
            self.organization,
            merge_observations((
                self.observation(
                    "https://jobs.galaxy-ats.example/campus/2027",
                    provider="codex_web_search",
                    rank=2,
                ),
            ))[0],
            criteria=self.criteria,
        )
        ranked = rank_discovery_candidates((aggregator, known))
        self.assertEqual(ranked[0], known)

    def test_frozen_ab_benchmark_has_explicit_scope_and_twelve_companies(self):
        path = Path(__file__).resolve().parents[2] / "data" / "announcement-discovery-benchmark-v1.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "1")
        self.assertEqual(payload["criteria"]["audiences"], ["2027届"])
        self.assertEqual(payload["criteria"]["recruitment_types"], ["秋招"])
        self.assertEqual(len(payload["companies"]), 12)
        self.assertEqual(
            len({item["organization"] for item in payload["companies"]}),
            12,
        )
        self.assertTrue(all(
            item["truth_urls"]
            and all(url.startswith("https://") for url in item["truth_urls"])
            for item in payload["companies"]
        ))


class OrchestratorAndPersistenceTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="晨星集团",
            aliases=["晨星招聘"],
            company_type=Organization.CompanyType.PRIVATE,
            industry="互联网/科技",
            official_domain="morning.example",
        )
        self.criteria = SearchCriteria(
            audiences=("2027届",),
            recruitment_types=("秋招",),
            published_after=date(2026, 6, 1),
            published_before=date(2026, 12, 31),
        )

    def observation(self, plan, provider="exa"):
        return DiscoveryObservation(
            intent_key=plan.intent_key,
            query=plan.query,
            url="https://morning.example/campus/2027",
            title_hint="晨星集团2027届秋招",
            snippet="晨星集团校园招聘正式启动",
            backend_date_hint="2026-08-01",
            provider=provider,
            rank=1,
            result_id=f"{provider}-1",
        )

    def test_sufficient_exa_candidate_does_not_start_codex(self):
        codex_calls = []

        class Exa:
            def search(inner, plan):
                return ProviderQueryResult.success(plan, (self.observation(plan),))

        orchestrator = AnnouncementDiscoveryOrchestrator(
            exa_client=Exa(),
            codex_searcher=lambda *args: codex_calls.append(args),
        )
        result = orchestrator.discover(
            [self.organization],
            self.criteria,
            allow_codex_fallback=True,
        )
        self.assertEqual(result.status, "complete")
        self.assertEqual(result.companies[0].status, "complete")
        self.assertFalse(codex_calls)

    def test_empty_exa_uses_one_company_scoped_codex_fallback(self):
        codex_calls = []

        class Exa:
            def search(inner, plan):
                return ProviderQueryResult.empty(plan)

        def codex(organization, plans, candidates, *, timeout_seconds):
            codex_calls.append((organization, plans, candidates))
            self.assertLessEqual(timeout_seconds, 180)
            return (self.observation(plans[0], provider="codex_web_search"),)

        result = AnnouncementDiscoveryOrchestrator(
            exa_client=Exa(),
            codex_searcher=codex,
        ).discover(
            [self.organization],
            self.criteria,
            allow_codex_fallback=True,
        )
        self.assertEqual(result.status, "complete")
        self.assertEqual(len(codex_calls), 1)
        self.assertEqual(codex_calls[0][0], self.organization)

    def test_permanent_exa_error_never_starts_codex(self):
        codex_calls = []

        class Exa:
            def search(inner, plan):
                raise ExaDiscoveryError("AUTH_INVALID", fallback_allowed=False)

        result = AnnouncementDiscoveryOrchestrator(
            exa_client=Exa(),
            codex_searcher=lambda *args: codex_calls.append(args),
        ).discover(
            [self.organization],
            self.criteria,
            allow_codex_fallback=True,
        )
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.companies[0].error_code, "AUTH_INVALID")
        self.assertFalse(codex_calls)

    def test_batch_deadline_prevents_late_codex_fallback(self):
        codex_calls = []

        class Exa:
            def search(inner, plan):
                return ProviderQueryResult.empty(plan)

        clock_values = iter((0, 601))
        result = AnnouncementDiscoveryOrchestrator(
            exa_client=Exa(),
            codex_searcher=lambda *args, **kwargs: codex_calls.append((args, kwargs)),
            clock=lambda: next(clock_values),
        ).discover(
            [self.organization],
            self.criteria,
            allow_codex_fallback=True,
        )

        self.assertEqual(result.status, "partial")
        self.assertEqual(
            result.companies[0].fallback_reason,
            "BATCH_DEADLINE_EXHAUSTED",
        )
        self.assertFalse(codex_calls)

    def test_codex_timeout_keeps_stable_error_code_and_duration(self):
        class Exa:
            def search(inner, plan):
                return ProviderQueryResult.empty(plan)

        def codex(*args, **kwargs):
            raise RuntimeError("Codex official-site discovery failed: TIMEOUT")

        latency_values = iter((10.0, 10.25))
        result = AnnouncementDiscoveryOrchestrator(
            exa_client=Exa(),
            codex_searcher=codex,
            clock=lambda: 0,
            latency_clock=lambda: next(latency_values),
        ).discover(
            [self.organization],
            self.criteria,
            allow_codex_fallback=True,
        )

        attempt = result.companies[0].attempts[-1]
        self.assertEqual(attempt.provider, "codex_web_search")
        self.assertEqual(attempt.error_code, "TIMEOUT")
        self.assertEqual(attempt.duration_ms, 250)

    def test_recording_is_company_atomic_and_preserves_multiple_observations(self):
        plan = AnnouncementSearchPlanner().plan(self.organization, self.criteria)[0]

        class Exa:
            def search(inner, current_plan):
                observations = (self.observation(current_plan),)
                if current_plan == plan:
                    observations += (
                        self.observation(current_plan, provider="codex_web_search"),
                    )
                return ProviderQueryResult.success(current_plan, observations)

        result = AnnouncementDiscoveryOrchestrator(
            exa_client=Exa(),
            codex_searcher=None,
        ).discover([self.organization], self.criteria)
        run = persist_discovery_result(result)

        self.assertEqual(run.status, AnnouncementDiscoveryRun.Status.COMPLETE)
        self.assertEqual(AnnouncementDiscoveryOrganizationRun.objects.count(), 1)
        candidate = AnnouncementDiscoveryCandidate.objects.get()
        self.assertEqual(candidate.identity_url, "https://morning.example/campus/2027")
        self.assertEqual(candidate.provider, "exa")
        observations = AnnouncementDiscoveryObservation.objects.filter(candidate=candidate)
        self.assertGreaterEqual(observations.count(), 2)
        observation = observations.first()
        observation.title_hint = "不能覆盖"
        with self.assertRaises(ValidationError):
            observation.save()

    def test_v2_output_can_be_replayed_and_recorded_without_cli_scope_flags(self):
        class Exa:
            def search(inner, plan):
                return ProviderQueryResult.success(plan, (self.observation(plan),))

        original = AnnouncementDiscoveryOrchestrator(
            exa_client=Exa(),
            codex_searcher=None,
        ).discover([self.organization], self.criteria)
        payload = _result_dict(original)

        replayed = parse_discovery_result_document(payload, [self.organization])
        self.assertEqual(replayed.criteria, self.criteria)
        self.assertEqual(replayed.companies[0].attempts[0].query, original.companies[0].attempts[0].query)

        invalid = json.loads(json.dumps(payload))
        invalid["criteria"]["audiences"] = "2027届"
        with self.assertRaises(ValueError):
            parse_discovery_result_document(invalid, [self.organization])

        output = StringIO()
        with patch("pathlib.Path.read_bytes", return_value=json.dumps(payload).encode("utf-8")):
            call_command(
                "discover_official_announcements",
                organization=[self.organization.name],
                input="result-v2.json",
                record=True,
                stdout=output,
            )
        recorded = json.loads(output.getvalue())
        self.assertIsNotNone(recorded["recorded_run_id"])
        self.assertTrue(AnnouncementDiscoveryCandidate.objects.exists())

    def test_one_company_permanent_failure_does_not_discard_other_company(self):
        failing = Organization.objects.create(
            name="故障企业",
            aliases=[],
            company_type=Organization.CompanyType.PRIVATE,
            industry="科技",
            official_domain="failure.example",
        )

        class Exa:
            def search(inner, plan):
                if plan.organization_id == failing.pk:
                    raise ExaDiscoveryError("AUTH_INVALID", fallback_allowed=False)
                return ProviderQueryResult.success(plan, (self.observation(plan),))

        result = AnnouncementDiscoveryOrchestrator(
            exa_client=Exa(),
            codex_searcher=None,
        ).discover([self.organization, failing], self.criteria)

        self.assertEqual(result.status, "partial")
        self.assertEqual([item.status for item in result.companies], ["complete", "failed"])

    def test_one_company_persistence_failure_is_isolated_and_marks_run_partial(self):
        second = Organization.objects.create(
            name="可写企业",
            aliases=[],
            company_type=Organization.CompanyType.PRIVATE,
            industry="科技",
            official_domain="writable.example",
        )

        class Exa:
            def search(inner, plan):
                domain = "morning.example" if plan.organization_id == self.organization.pk else "writable.example"
                return ProviderQueryResult.success(plan, (DiscoveryObservation(
                    intent_key=plan.intent_key,
                    query=plan.query,
                    url=f"https://{domain}/campus/2027",
                    title_hint="2027届秋招校园招聘",
                    snippet="校园招聘正式启动",
                    backend_date_hint="2026-08-01",
                    provider="exa",
                    rank=1,
                    result_id=f"exa-{plan.organization_id}",
                ),))

        result = AnnouncementDiscoveryOrchestrator(
            exa_client=Exa(),
            codex_searcher=None,
        ).discover([self.organization, second], self.criteria)
        real_create = AnnouncementDiscoveryProviderAttempt.objects.create

        def create_attempt(**kwargs):
            if kwargs["organization_run"].organization_id == self.organization.pk:
                raise RuntimeError("simulated write failure")
            return real_create(**kwargs)

        with patch.object(
            AnnouncementDiscoveryProviderAttempt.objects,
            "create",
            side_effect=create_attempt,
        ):
            run = persist_discovery_result(result)

        self.assertEqual(run.status, AnnouncementDiscoveryRun.Status.PARTIAL)
        statuses = dict(
            run.organization_runs.values_list("organization__name", "status")
        )
        self.assertEqual(statuses["晨星集团"], "failed")
        self.assertEqual(statuses["可写企业"], "complete")
        self.assertEqual(AnnouncementDiscoveryCandidate.objects.count(), 1)


class DiscoveryCommandSafetyTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="命令测试公司",
            aliases=[],
            company_type=Organization.CompanyType.PRIVATE,
            industry="科技",
            official_domain="command.example",
        )

    def test_all_requires_explicit_max_companies(self):
        with self.assertRaises(CommandError):
            call_command("discover_official_announcements", all=True, stdout=StringIO())

    def test_input_and_default_preview_do_not_write_without_record(self):
        payload = {
            "schema_version": "1",
            "query": "命令测试公司 2027届 秋招",
            "source": {"orchestrator": "codex", "providers": ["codex_web_search"]},
            "candidates": [{
                "url": "https://command.example/campus/2027",
                "title_hint": "命令测试公司2027届秋招",
                "provider": "codex_web_search",
                "rank": 1,
                "result_id": "legacy-1",
            }],
        }
        with patch("pathlib.Path.read_bytes", return_value=json.dumps(payload).encode("utf-8")):
            call_command(
                "discover_official_announcements",
                organization=[self.organization.name],
                input="legacy.json",
                stdout=StringIO(),
            )
        self.assertFalse(AnnouncementDiscoveryCandidate.objects.exists())
        self.assertFalse(AnnouncementDiscoveryRun.objects.exists())

    def test_default_preview_does_not_create_exa_client_or_start_codex(self):
        with (
            patch(
                "radar.management.commands.discover_official_announcements.build_exa_client_from_environment"
            ) as exa_builder,
            patch(
                "radar.management.commands.discover_official_announcements.discover_official_candidates_with_codex"
            ) as codex_search,
        ):
            call_command(
                "discover_official_announcements",
                organization=[self.organization.name],
                stdout=StringIO(),
            )
        exa_builder.assert_not_called()
        codex_search.assert_not_called()

    def test_live_search_requires_explicit_scope(self):
        with self.assertRaises(CommandError):
            call_command(
                "discover_official_announcements",
                organization=[self.organization.name],
                allow_live_search=True,
                stdout=StringIO(),
            )


class EvidenceAndCredentialIsolationTests(TestCase):
    def setUp(self):
        self.source = create_enabled_source(
            name="证据隔离公司",
            host="evidence-isolation.test",
        )

    def test_search_title_is_not_used_when_refetched_html_has_no_title(self):
        candidate = OfficialSiteCandidate(
            url="https://evidence-isolation.test/campus/2027",
            title_hint="搜索生成的2027届秋招标题",
            provider="exa",
            rank=1,
            result_id="exa-title",
        )

        class Response:
            status_code = 200
            headers = {}
            url = candidate.url
            content = "<html><body>2027届校园招聘正在投递</body></html>".encode()

            @staticmethod
            def raise_for_status():
                return None

        result = refetch_official_candidate(
            self.source.organization,
            candidate,
            session=SimpleNamespace(get=lambda *args, **kwargs: Response()),
            resolver=lambda _host: ("8.8.8.8",),
        )
        self.assertEqual(result.title, "")

    def test_verified_announcement_rejects_missing_refetched_title(self):
        candidate = AnnouncementDiscoveryCandidate.objects.create(
            organization=self.source.organization,
            source_kind="website",
            url="https://evidence-isolation.test/campus/2027",
            title_hint="搜索生成标题",
            provider="exa",
        )
        with self.assertRaisesMessage(
            ValidationError,
            "official page title must come from refetched evidence",
        ):
            verify_official_announcement(
                candidate,
                RefetchedOfficialCandidate(
                    url=candidate.url,
                    title="",
                    content_sha256="a" * 64,
                    fetched_at=timezone.now(),
                    recruitment_signal_found=True,
                ),
                identity_evidence="官网域名与企业主体一致",
            )

    def test_exa_key_is_removed_from_discovery_subprocess_environment(self):
        with patch.dict(os.environ, {"EXA_API_KEY": "must-not-leak"}):
            environment = scrubbed_discovery_subprocess_environment()
        self.assertNotIn("EXA_API_KEY", environment)

    def test_project_dotenv_loads_only_exa_key_and_overrides_old_process_value(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "EXA_API_KEY=new-test-key\nDJANGO_SECRET_KEY=must-not-load\n",
                encoding="utf-8",
            )
            environment = {
                "EXA_API_KEY": "old-system-key",
                "DJANGO_SECRET_KEY": "existing-secret",
            }

            loaded = load_project_exa_key(path, environ=environment)

        self.assertTrue(loaded)
        self.assertEqual(environment["EXA_API_KEY"], "new-test-key")
        self.assertEqual(environment["DJANGO_SECRET_KEY"], "existing-secret")

    def test_empty_or_missing_dotenv_does_not_clear_existing_key(self):
        with TemporaryDirectory() as directory:
            environment = {"EXA_API_KEY": "existing-key"}
            missing = load_project_exa_key(
                Path(directory) / "missing.env",
                environ=environment,
            )
            empty_path = Path(directory) / ".env"
            empty_path.write_text("EXA_API_KEY=\n", encoding="utf-8")
            empty = load_project_exa_key(empty_path, environ=environment)

        self.assertFalse(missing)
        self.assertFalse(empty)
        self.assertEqual(environment["EXA_API_KEY"], "existing-key")

    def test_codex_subprocess_receives_no_exa_key_and_provider_is_fixed(self):
        candidate_output = {
            "schema_version": "1",
            "query": "证据隔离公司 2027届 秋招",
            "source": {
                "orchestrator": "codex",
                "providers": ["codex_web_search"],
            },
            "candidates": [{
                "url": "https://evidence-isolation.test/campus/2027",
                "title_hint": "证据隔离公司2027届秋招",
                "provider": "codex_web_search",
                "rank": 1,
                "result_id": "codex-1",
            }],
        }
        calls = []

        def runner(command, **kwargs):
            calls.append(kwargs)
            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(candidate_output, ensure_ascii=False),
                "",
            )

        with patch.dict(os.environ, {"EXA_API_KEY": "must-not-leak"}):
            result = discover_official_candidates_with_codex(
                self.source.organization,
                search_queries=("证据隔离公司 2027届 秋招",),
                published_after="2026-06-01",
                published_before="2026-12-31",
                candidate_context=({
                    "url": "https://example.test/tracked",
                    "title_hint": "截断标题",
                    "route_state": "rejected",
                    "rejection_code": "UNROUTABLE_SOURCE",
                    "snippet": "不得进入 Codex 的 Exa 摘要",
                },),
                runner=runner,
            )

        self.assertNotIn("EXA_API_KEY", calls[0]["env"])
        self.assertIn("2027届 秋招", calls[0]["input"])
        self.assertIn("2026-06-01", calls[0]["input"])
        self.assertIn("UNROUTABLE_SOURCE", calls[0]["input"])
        self.assertNotIn("不得进入 Codex 的 Exa 摘要", calls[0]["input"])
        self.assertEqual(result.providers, ("codex_web_search",))
        self.assertEqual(result.candidates[0].provider, "codex_web_search")

    def test_windows_codex_wrapper_resolves_to_native_executable(self):
        prefix = _codex_command_prefix("codex")
        if os.name == "nt":
            self.assertEqual(len(prefix), 1)
            self.assertTrue(prefix[0].casefold().endswith("codex.exe"))
            self.assertNotIn("cmd.exe", prefix[0].casefold())
            with patch(
                "radar.services.announcement_discovery.shutil.which",
                return_value=None,
            ):
                with self.assertRaises(OSError):
                    _codex_command_prefix("codex")
