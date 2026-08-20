from dataclasses import replace

from django.db import IntegrityError, transaction
from django.test import TestCase

from radar.collectors.base import PositionCandidate
from radar.models import (
    ApplicationProgress,
    PublicationEvent,
    RecruitmentNotice,
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

    def test_complete_page_with_only_non_target_positions_retires_old_target_projection(self) -> None:
        initial = complete_candidate(self.source)
        created = publish_candidates(self.source, [initial], self.version())[0]
        progress = ApplicationProgress.objects.create(
            notice_id=created.notice_id,
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

        notice = RecruitmentNotice.objects.get(pk=created.notice_id)
        self.assertEqual(result.action, "updated")
        self.assertEqual(
            notice.latest_publication_event.event_type,
            PublicationEvent.EventType.OUT_OF_SCOPE,
        )
        self.assertFalse(notice.positions.filter(is_current=True).exists())
        self.assertFalse(notice.application_links.filter(is_current=True).exists())
        progress.refresh_from_db()
        self.assertEqual(progress.status, ApplicationProgress.Status.INTERVIEWED)

    def test_identity_and_canonical_url_are_both_checked_before_writing(self) -> None:
        first = complete_candidate(
            self.source,
            identity_key="notice-a",
            notice_url="https://official.test/notices/shared",
        )
        second = complete_candidate(
            self.source,
            identity_key="notice-b",
            notice_url="https://official.test/notices/b",
        )
        publish_candidates(self.source, [first], self.version())
        published_second = publish_candidates(self.source, [second], self.version())[0]
        notice_b = RecruitmentNotice.objects.get(pk=published_second.notice_id)
        conflicting = replace(
            second,
            official_notice_url=first.official_notice_url,
            field_evidence={
                **second.field_evidence,
                "notice_url": field_evidence(
                    first.official_notice_url,
                    "#notice-b a.notice@href",
                ),
            },
        )

        result = publish_candidates(self.source, [conflicting], self.version())[0]

        self.assertEqual(result.action, "rejected")
        self.assertIn("ambiguous_identity", result.reasons)
        self.assertEqual(RecruitmentNotice.objects.count(), 2)
        notice_b.refresh_from_db()
        self.assertEqual(notice_b.official_notice_url, second.official_notice_url)
        self.assertTrue(RecruitmentNotice.objects.formal().filter(pk=notice_b.pk).exists())

    def test_identity_key_is_trimmed_before_lookup_and_storage(self) -> None:
        initial = complete_candidate(self.source, identity_key="notice-2027")
        created = publish_candidates(self.source, [initial], self.version())[0]
        spaced = replace(initial, identity_key="  notice-2027  ", title="Updated")
        spaced = replace(
            spaced,
            field_evidence={
                **spaced.field_evidence,
                "title": field_evidence("Updated", "#notice h2"),
            },
        )

        result = publish_candidates(self.source, [spaced], self.version())[0]

        self.assertEqual(result.action, "updated")
        self.assertEqual(result.notice_id, created.notice_id)
        self.assertEqual(RecruitmentNotice.objects.get().identity_key, "notice-2027")

    def test_database_rejects_duplicate_source_and_canonical_notice_url(self) -> None:
        first = publish_candidates(
            self.source,
            [complete_candidate(self.source, identity_key="notice-a")],
            self.version(),
        )[0]
        original = RecruitmentNotice.objects.get(pk=first.notice_id)
        with self.assertRaises(IntegrityError), transaction.atomic():
            RecruitmentNotice.objects.create(
                organization=self.source.organization,
                source=self.source,
                identity_key="notice-b",
                title="Duplicate URL",
                official_notice_url=original.official_notice_url,
            )


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
        notice = RecruitmentNotice.objects.get(pk=created.notice_id)

        self.assertNotContains(self.client.get("/"), notice.official_notice_url)
        self.assertContains(
            self.client.get("/?status=withdrawn"), notice.official_notice_url
        )
