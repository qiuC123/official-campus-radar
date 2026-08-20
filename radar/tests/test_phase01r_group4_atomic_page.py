from datetime import date
from unittest.mock import patch

from django.test import TestCase

from radar.collectors.base import (
    FieldEvidenceValue,
    FetchedPage,
    NoticeCandidate,
    PositionCandidate,
)
from radar.models import Evidence, FetchRun, OfficialSource, Organization, SourceVersion
from radar.services.admission import transition_source
from radar.services.update_runner import run_update
from radar.tests.helpers import valid_html_parser_config


def evidence(raw: str, locator: str, parsed: str | None = None) -> FieldEvidenceValue:
    return FieldEvidenceValue(raw, locator, raw if parsed is None else parsed)


def complete_candidate(title: str) -> NoticeCandidate:
    url = "https://official.test/notices/2027"
    return NoticeCandidate(
        title=title,
        official_notice_url=url,
        recruitment_type="校园招聘",
        target_audience="2027届",
        published_on=date(2026, 8, 1),
        deadline=date(2026, 9, 1),
        withdrawn=False,
        evidence_excerpt="context",
        positions=(
            PositionCandidate(
                "Engineer",
                "北京",
                "Engineer 北京",
                None,
                position_key="position-1",
                field_evidence={
                    "position_title": evidence("Engineer", ".position"),
                    "location": evidence("北京", ".location"),
                },
            ),
        ),
        identity_key="notice-2027",
        field_evidence={
            "title": evidence(title, "h2"),
            "recruitment_type": evidence("校园招聘", ".type", "campus_recruitment"),
            "target_audience": evidence("2027届", ".audience"),
            "published_on": evidence("2026-08-01", ".published"),
            "deadline": evidence("2026-09-01", ".deadline"),
            "notice_url": evidence(url, "a.notice@href"),
        },
        positions_complete=True,
    )


class SequenceAdapter:
    def __init__(self, bodies: list[str]) -> None:
        self.bodies = bodies

    def fetch(self, source):
        body = self.bodies.pop(0)
        return FetchedPage(source.source_url, body, body * 64, 200, None)

    def extract(self, source, page):
        return [complete_candidate(f"Campus {page.body}")]


class AtomicPageUpdateTests(TestCase):
    def setUp(self) -> None:
        organization = Organization.objects.create(
            name="Atomic Org",
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
            evidence="local review",
        )
        transition_source(
            self.source,
            to_state="enabled",
            actor_label="owner",
            reason="enabled",
            evidence="fixture passed",
        )
        self.source.refresh_from_db()

    def test_only_consecutive_hash_is_unchanged_and_a_b_a_is_three_versions(self) -> None:
        adapter = SequenceAdapter(["a", "b", "a", "a"])
        with patch(
            "radar.services.update_runner.AdapterRegistry.get", return_value=adapter
        ):
            run_update(trigger="manual")
            run_update(trigger="manual")
            run_update(trigger="manual")
            fourth = run_update(trigger="manual")
        self.assertEqual(
            list(
                SourceVersion.objects.filter(source=self.source)
                .order_by("pk")
                .values_list("content_hash", flat=True)
            ),
            ["a" * 64, "b" * 64, "a" * 64],
        )
        self.assertTrue(
            all(
                SourceVersion.objects.filter(source=self.source).values_list(
                    "is_applied", flat=True
                )
            )
        )
        self.assertEqual(fourth.notices_updated, 0)
        self.assertEqual(
            FetchRun.objects.filter(source=self.source, status="unchanged").count(),
            1,
        )

    def test_mid_page_write_failure_rolls_back_then_same_hash_retries(self) -> None:
        adapter = SequenceAdapter(["x", "x"])
        with patch(
            "radar.services.update_runner.AdapterRegistry.get", return_value=adapter
        ):
            with patch.object(
                Evidence.objects,
                "create",
                side_effect=RuntimeError("database write failed"),
            ):
                failed = run_update(trigger="manual")
            self.assertEqual(failed.sources_failed, 1)
            self.assertFalse(SourceVersion.objects.filter(source=self.source).exists())
            self.assertFalse(self.source.recruitment_notices.exists())
            failed_runs = FetchRun.objects.filter(source=self.source, status="failed")
            self.assertEqual(failed_runs.count(), 1)
            self.assertFalse(
                FetchRun.objects.filter(source=self.source, status="running").exists()
            )

            retried = run_update(trigger="manual")
        self.assertEqual(retried.notices_created, 1)
        self.assertEqual(SourceVersion.objects.filter(source=self.source).count(), 1)
        self.assertTrue(SourceVersion.objects.get(source=self.source).is_applied)
