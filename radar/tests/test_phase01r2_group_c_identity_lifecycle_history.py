from dataclasses import replace

from django.test import TestCase

from radar.collectors.base import PositionCandidate
from radar.models import (
    ApplicationProgress,
    PublicationEvent,
    RecruitmentBatch,
    SourceVersion,
)
from radar.services.admission import transition_source
from radar.services.publication import publish_candidates
from radar.tests.helpers import (
    complete_candidate,
    create_enabled_source,
    field_evidence,
)


class IdentityAndLifecycleTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source(name="Identity Lifecycle")
        self.version_number = 0

    def version(self) -> SourceVersion:
        self.version_number += 1
        return SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash=str(self.version_number) * 64,
            is_applied=True,
        )

    def test_complete_page_with_any_city_replaces_old_projection(self) -> None:
        initial = complete_candidate(self.source)
        created = publish_candidates(self.source, [initial], self.version())[0]
        progress = ApplicationProgress.objects.create(
            batch=RecruitmentBatch.objects.get(pk=created.batch_id),
            status=ApplicationProgress.Status.INTERVIEWED,
        )
        hangzhou = PositionCandidate(
            title="Hangzhou Engineer",
            location_text="杭州",
            raw_text="Hangzhou Engineer 杭州",
            application_url=None,
            position_key="hangzhou-position",
            field_evidence={
                "position_title": field_evidence(
                    "Hangzhou Engineer", "#hangzhou .title"
                ),
                "location": field_evidence("杭州", "#hangzhou .location"),
            },
        )
        complete_non_target_page = replace(
            initial,
            positions=(hangzhou,),
            positions_complete=True,
        )

        result = publish_candidates(
            self.source, [complete_non_target_page], self.version()
        )[0]

        batch = RecruitmentBatch.objects.get(pk=created.batch_id)
        self.assertEqual(result.action, "updated")
        self.assertEqual(batch.latest_publication_event.event_type, PublicationEvent.EventType.UPDATED)
        self.assertEqual(list(batch.positions.filter(is_current=True).values_list("title", flat=True)), ["Hangzhou Engineer"])
        self.assertFalse(batch.application_links.filter(is_current=True).exists())
        progress.refresh_from_db()
        self.assertEqual(progress.status, ApplicationProgress.Status.INTERVIEWED)

    def test_identity_and_canonical_url_are_both_checked_before_writing(self) -> None:
        first = complete_candidate(
            self.source,
            identity_key="batch-a",
            official_page_url="https://official.test/batches/shared",
        )
        second = complete_candidate(
            self.source,
            identity_key="batch-b",
            official_page_url="https://official.test/batches/b",
        )
        publish_candidates(self.source, [first], self.version())
        published_second = publish_candidates(self.source, [second], self.version())[0]
        notice_b = RecruitmentBatch.objects.get(pk=published_second.batch_id)
        conflicting = replace(
            second,
            official_page_url=first.official_page_url,
            field_evidence={
                **second.field_evidence,
                "official_page_url": field_evidence(
                    first.official_page_url,
                    "#batch-b a.notice@href",
                ),
            },
        )

        result = publish_candidates(self.source, [conflicting], self.version())[0]

        self.assertEqual(result.action, "rejected")
        self.assertIn("ambiguous_identity", result.reasons)
        self.assertEqual(RecruitmentBatch.objects.count(), 2)
        notice_b.refresh_from_db()
        self.assertEqual(notice_b.official_page_url, second.official_page_url)
        self.assertTrue(RecruitmentBatch.objects.formal().filter(pk=notice_b.pk).exists())

    def test_identity_key_is_trimmed_before_lookup_and_storage(self) -> None:
        initial = complete_candidate(self.source, identity_key="batch-2027")
        created = publish_candidates(self.source, [initial], self.version())[0]
        spaced = replace(initial, identity_key="  batch-2027  ", title="Updated")
        spaced = replace(
            spaced,
            field_evidence={
                **spaced.field_evidence,
                "title": field_evidence("Updated", "#batch h2"),
            },
        )

        result = publish_candidates(self.source, [spaced], self.version())[0]

        self.assertEqual(result.action, "updated")
        self.assertEqual(result.batch_id, created.batch_id)
        self.assertEqual(RecruitmentBatch.objects.get().identity_key, "batch-2027")

    def test_database_allows_distinct_batches_to_share_a_portal_url(self) -> None:
        first = publish_candidates(
            self.source,
            [complete_candidate(self.source, identity_key="batch-a")],
            self.version(),
        )[0]
        original = RecruitmentBatch.objects.get(pk=first.batch_id)
        RecruitmentBatch.objects.create(
            organization=self.source.organization,
            source=self.source,
            identity_key="batch-b",
            title="Second project on shared portal",
            official_page_url=original.official_page_url,
        )
        self.assertEqual(RecruitmentBatch.objects.count(), 2)


class TrustedHistoryQueryTests(TestCase):
    def test_withdrawn_notice_with_prior_complete_chain_is_visible_only_in_history(self) -> None:
        source = create_enabled_source(name="History Org")
        version_one = SourceVersion.objects.create(
            source=source,
            canonical_url=source.source_url,
            content_hash="a" * 64,
            is_applied=True,
        )
        candidate = complete_candidate(source)
        created = publish_candidates(source, [candidate], version_one)[0]
        version_two = SourceVersion.objects.create(
            source=source,
            canonical_url=source.source_url,
            content_hash="b" * 64,
            is_applied=True,
        )
        publish_candidates(
            source,
            [replace(candidate, withdrawn=True, positions=(), field_evidence={})],
            version_two,
        )
        transition_source(
            source,
            to_state="revoked",
            actor_label="owner",
            reason="source retired",
            evidence="saved retirement decision",
        )
        batch = RecruitmentBatch.objects.get(pk=created.batch_id)

        self.assertNotContains(self.client.get("/"), batch.official_page_url)
        self.assertContains(
            self.client.get("/history/"), batch.official_page_url
        )
