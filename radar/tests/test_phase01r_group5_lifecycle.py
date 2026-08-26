from dataclasses import replace

from django.test import TestCase

from radar.collectors.base import PositionCandidate
from radar.models import (
    ApplicationProgress,
    RecruitmentPosition,
    OfficialSource,
    Organization,
    PublicationEvent,
    SourceVersion,
)
from radar.services.admission import transition_source
from radar.services.publication import publish_candidates
from radar.tests.test_phase01r_group4_atomic_page import complete_candidate, evidence
from radar.tests.helpers import valid_html_parser_config


class NewAdmissionAndExistingLifecycleTests(TestCase):
    def setUp(self) -> None:
        organization = Organization.objects.create(
            name="Lifecycle Org",
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
            evidence="fixture passed",
        )
        self.source.refresh_from_db()
        self.version_number = 0

    def version(self) -> SourceVersion:
        self.version_number += 1
        return SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash=str(self.version_number) * 64,
            is_applied=True,
        )

    def publish_initial(self, *, two_positions: bool = False):
        candidate = complete_candidate("Initial")
        if two_positions:
            second = PositionCandidate(
                "Designer",
                "上海",
                "Designer 上海",
                None,
                position_key="position-2",
                field_evidence={
                    "position_title": evidence("Designer", ".position-2"),
                    "location": evidence("上海", ".location-2"),
                },
            )
            candidate = replace(candidate, positions=candidate.positions + (second,))
        result = publish_candidates(self.source, [candidate], self.version())[0]
        progress = ApplicationProgress.objects.create(
            batch=self.source.recruitment_batches.get(pk=result.batch_id),
            status="interviewed",
        )
        return candidate, result, progress

    def test_existing_explicit_withdrawal_bypasses_new_notice_location_gate(self) -> None:
        candidate, result, progress = self.publish_initial(two_positions=True)
        withdrawn = replace(
            candidate,
            withdrawn=True,
            positions=(),
            field_evidence={},
            positions_complete=False,
        )
        lifecycle = publish_candidates(self.source, [withdrawn], self.version())[0]
        self.assertEqual(lifecycle.action, "updated")
        batch = self.source.recruitment_batches.get(pk=result.batch_id)
        self.assertEqual(batch.status, "withdrawn")
        self.assertFalse(batch.positions.filter(is_current=True).exists())
        self.assertEqual(batch.latest_publication_event.event_type, "withdrawn")
        progress.refresh_from_db()
        self.assertEqual(progress.status, "interviewed")

    def test_complete_position_coverage_can_remove_all_old_target_positions(self) -> None:
        candidate, result, progress = self.publish_initial(two_positions=True)
        no_current_positions = replace(
            candidate,
            positions=(),
            positions_complete=True,
            field_evidence={},
        )
        lifecycle = publish_candidates(
            self.source, [no_current_positions], self.version()
        )[0]
        self.assertEqual(lifecycle.action, "rejected")
        batch = self.source.recruitment_batches.get(pk=result.batch_id)
        self.assertEqual(batch.positions.filter(is_current=True).count(), 2)
        self.assertTrue(self.source.recruitment_batches.formal().filter(pk=batch.pk).exists())
        progress.refresh_from_db()
        self.assertEqual(progress.status, "interviewed")

        new_url = "https://official.test/batches/brand-new"
        new_candidate = replace(
            no_current_positions,
            identity_key="brand-new",
            official_page_url=new_url,
            field_evidence={
                "official_page_url": evidence(new_url, "a.brand-new@href"),
            },
        )
        rejected = publish_candidates(self.source, [new_candidate], self.version())[0]
        self.assertEqual(rejected.action, "rejected")
        self.assertIn("missing_positions", rejected.reasons)

    def test_incomplete_position_coverage_does_not_remove_unseen_old_position(self) -> None:
        candidate, result, progress = self.publish_initial(two_positions=True)
        partial = replace(
            candidate,
            title="Partial parser result",
            positions=(candidate.positions[0],),
            positions_complete=False,
            field_evidence={
                **candidate.field_evidence,
                "title": evidence("Partial parser result", "h2"),
            },
        )
        partial_result = publish_candidates(self.source, [partial], self.version())[0]
        self.assertEqual(partial_result.action, "rejected")
        self.assertIn("incomplete_position_coverage", partial_result.reasons)
        batch = self.source.recruitment_batches.get(pk=result.batch_id)
        self.assertEqual(batch.title, "Initial")
        self.assertTrue(
            self.source.recruitment_batches.formal().filter(pk=batch.pk).exists()
        )
        self.assertEqual(
            set(
                RecruitmentPosition.objects.filter(batch=batch, is_current=True).values_list(
                    "position_key", flat=True
                )
            ),
            {"position-1", "position-2"},
        )
        progress.refresh_from_db()
        self.assertEqual(progress.status, "interviewed")
        self.assertFalse(
            PublicationEvent.objects.filter(
                batch=batch, event_type="withdrawn"
            ).exists()
        )
