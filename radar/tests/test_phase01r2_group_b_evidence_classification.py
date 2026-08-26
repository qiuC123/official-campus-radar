from dataclasses import replace
from datetime import date

from django.test import TestCase

from radar.collectors.base import FetchedPage
from radar.collectors.html import HtmlSourceAdapter
from radar.models import Evidence, RecruitmentBatch, SourceVersion
from radar.services.publication import publish_candidates
from radar.tests.helpers import (
    complete_candidate,
    create_enabled_source,
    field_evidence,
    valid_html_parser_config,
)


class ProjectionEvidenceBindingTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source(name="Evidence Binding")
        self.version_number = 0

    def version(self) -> SourceVersion:
        self.version_number += 1
        return SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash=str(self.version_number) * 64,
            is_applied=True,
        )

    def publish(self, *, application_url: str | None = None) -> RecruitmentBatch:
        result = publish_candidates(
            self.source,
            [complete_candidate(self.source, application_url=application_url)],
            self.version(),
        )[0]
        return RecruitmentBatch.objects.get(pk=result.batch_id)

    def test_candidate_evidence_must_match_the_candidate_projection(self) -> None:
        candidate = complete_candidate(self.source)
        candidate = replace(
            candidate,
            field_evidence={
                **candidate.field_evidence,
                "title": field_evidence("old title", "#batch h2", "old title"),
            },
        )

        result = publish_candidates(self.source, [candidate], self.version())[0]

        self.assertEqual(result.action, "rejected")
        self.assertIn("incomplete_field_evidence", result.reasons)

    def test_formal_query_rejects_a_title_changed_after_evidence_was_written(self) -> None:
        batch = self.publish()
        RecruitmentBatch.objects.filter(pk=batch.pk).update(title="tampered title")

        self.assertFalse(RecruitmentBatch.objects.formal().filter(pk=batch.pk).exists())

    def test_formal_query_rejects_a_position_or_link_changed_after_publication(self) -> None:
        batch = self.publish(application_url="https://official.test/apply/1")
        batch.positions.filter(is_current=True).update(location_text="深圳")
        batch.application_links.filter(is_current=True).update(
            url="https://official.test/apply/tampered"
        )

        self.assertFalse(RecruitmentBatch.objects.formal().filter(pk=batch.pk).exists())

    def test_formal_query_recomputes_the_evidence_value_hash(self) -> None:
        batch = self.publish()
        Evidence.objects.filter(
            publication_event=batch.latest_publication_event,
            field_name="title",
        ).update(value_hash="0" * 64)

        self.assertFalse(RecruitmentBatch.objects.formal().filter(pk=batch.pk).exists())


class ClassificationAndLocatorTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source(name="Classification Binding")

    def test_negative_signal_in_title_or_node_text_wins_over_campus_type(self) -> None:
        candidate = complete_candidate(self.source)
        negative_position = replace(
            candidate.positions[0],
            raw_text="校园招聘会新闻：现场包含采购招标介绍",
        )
        candidate = replace(
            candidate,
            title="2027 校园招聘招商合作新闻",
            positions=(negative_position,),
            field_evidence={
                **candidate.field_evidence,
                "title": field_evidence(
                    "2027 校园招聘招商合作新闻",
                    "#batch h2",
                ),
            },
        )
        version = SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash="c" * 64,
            is_applied=True,
        )

        result = publish_candidates(self.source, [candidate], version)[0]

        self.assertEqual(result.action, "rejected")
        self.assertIn("not_eligible_recruitment_type", result.reasons)

    def test_missing_html_nodes_do_not_receive_container_level_fake_locators(self) -> None:
        self.source.parser_config = valid_html_parser_config()
        self.source.save(update_fields=["parser_config"])
        page = FetchedPage(
            self.source.source_url,
            """
            <article class="job" data-notice-id="batch-1" data-position-id="position-1">
              <a class="notice" href="/batch-1">batch</a>
              <h2>2027 Campus</h2><span class="type">校园招聘</span>
            </article>
            """,
            "d" * 64,
            200,
            None,
        )

        candidate = HtmlSourceAdapter().extract(self.source, page)[0]

        self.assertNotIn("target_audience", candidate.field_evidence)
        self.assertNotIn("published_on", candidate.field_evidence)
        self.assertNotIn("deadline", candidate.field_evidence)
        self.assertNotIn("location", candidate.positions[0].field_evidence)

    def test_node_without_stable_identity_gets_no_precise_evidence_locator(self) -> None:
        self.source.parser_config = valid_html_parser_config()
        self.source.save(update_fields=["parser_config"])
        page = FetchedPage(
            self.source.source_url,
            """
            <article class="job">
              <a class="notice" href="/batch-1">batch</a>
              <h2>2027 Campus</h2><span class="type">校园招聘</span>
              <span class="audience">2027届</span><time class="published">2026-08-01</time>
              <time class="deadline">2026-09-01</time>
              <span class="position-title">Engineer</span><span class="location">北京</span>
              <p class="description">Engineer 北京</p>
            </article>
            """,
            "e" * 64,
            200,
            None,
        )

        candidate = HtmlSourceAdapter().extract(self.source, page)[0]

        self.assertEqual(candidate.identity_key, "")
        self.assertEqual(candidate.field_evidence, {})
        self.assertEqual(candidate.positions[0].field_evidence, {})
