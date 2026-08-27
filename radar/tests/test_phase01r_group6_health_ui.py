from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from radar.models import FetchRun, RecruitmentPosition, OfficialSource, Organization, UpdateRun
from radar.services.admission import transition_source
from radar.services.publication import publish_candidates
from radar.services.update_runner import sanitize_error
from radar.services.update_status import scheduled_run_is_missing
from radar.tests.test_phase01r_group4_atomic_page import complete_candidate
from radar.tests.helpers import valid_html_parser_config


class CurrentPositionAndHealthViewTests(TestCase):
    def setUp(self) -> None:
        administrator = get_user_model().objects.create_superuser("owner", "owner@example.test", "test")
        self.client.force_login(administrator)
        organization = Organization.objects.create(
            name="Health Org",
            company_type="internet",
            industry="tech",
            official_domain="official.test",
        )
        self.source = OfficialSource.objects.create(
            organization=organization,
            source_type="website",
            source_url="https://official.test/careers",
            admission_evidence="candidate",
            parser_config=valid_html_parser_config(),
        )
        transition_source(
            self.source,
            to_state="verified",
            actor_label="owner",
            reason="verified",
            evidence="review",
        )
        transition_source(
            self.source,
            to_state="enabled",
            actor_label="owner",
            reason="enabled",
            evidence="fixture",
        )
        self.source.refresh_from_db()
        from radar.models import SourceVersion

        version = SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash="6" * 64,
            is_applied=True,
        )
        result = publish_candidates(
            self.source, [complete_candidate("Searchable")], version
        )[0]
        self.batch = self.source.recruitment_batches.get(pk=result.batch_id)
        RecruitmentPosition.objects.create(
            batch=self.batch,
            position_key="removed-position",
            title="Legacy Secret Role",
            location_text="北京",
            normalized_locations=["北京"],
            is_current=False,
        )

    def test_position_keyword_matches_only_current_positions(self) -> None:
        self.assertContains(
            self.client.get("/?position=Engineer"), self.batch.official_page_url
        )
        self.assertNotContains(
            self.client.get("/?position=Legacy+Secret"),
            self.batch.official_page_url,
        )

    def test_partial_failure_displays_source_degradation_summary(self) -> None:
        UpdateRun.objects.create(
            trigger="scheduled",
            scheduled_for_date=timezone.localdate(),
            status="success",
        )
        update = UpdateRun.objects.create(trigger="manual", status="partial_failure")
        FetchRun.objects.create(
            update_run=update,
            source=self.source,
            status="failed",
            error_message="TimeoutError: request timed out",
        )
        response = self.client.get("/")
        self.assertContains(response, "来源健康降级：1 个来源失败")
        self.assertContains(response, "Health Org")
        self.assertContains(response, "TimeoutError: request timed out")


class ScheduleFactAndSanitizationTests(TestCase):
    def test_2201_is_missing_and_manual_success_does_not_satisfy_schedule(self) -> None:
        now = datetime(2026, 8, 18, 22, 1, tzinfo=ZoneInfo("Asia/Shanghai"))
        self.assertTrue(scheduled_run_is_missing(now))
        UpdateRun.objects.create(trigger="manual", status="success")
        self.assertTrue(scheduled_run_is_missing(now))
        UpdateRun.objects.create(
            trigger="scheduled",
            scheduled_for_date=date(2026, 8, 18),
            status="partial_failure",
        )
        self.assertFalse(scheduled_run_is_missing(now))

    def test_error_sanitizer_removes_queries_secrets_and_local_user_paths(self) -> None:
        safe = sanitize_error(
            RuntimeError(
                r"GET https://official.test/jobs?token=secret#private failed "
                r"at C:\Users\Alice\project\file.html cookie=abc123"
            )
        )
        for secret in ("secret", "private", "Alice", "abc123"):
            self.assertNotIn(secret, safe)
        self.assertIn("https://official.test/jobs", safe)
        self.assertIn("[local-path]", safe)
