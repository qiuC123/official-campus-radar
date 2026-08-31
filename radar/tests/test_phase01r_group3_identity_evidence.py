from datetime import date

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from radar.collectors.base import (
    FieldEvidenceValue,
    FetchedPage,
    RecruitmentBatchCandidate,
    PositionCandidate,
)
from radar.collectors.html import HtmlSourceAdapter
from radar.models import Evidence, OfficialSource, Organization, PublicationEvent, SourceVersion
from radar.services.admission import transition_source
from radar.services.publication import (
    BATCH_EVIDENCE_FIELDS,
    classify_recruitment,
    publish_candidates,
)
from radar.tests.helpers import valid_html_parser_config


class StrictRecruitmentClassificationTests(SimpleTestCase):
    def test_explicit_recruitment_season_and_stage_take_precedence(self) -> None:
        self.assertEqual(
            classify_recruitment("2026届春招补录，7月重新开放"),
            "spring_supplement",
        )
        self.assertEqual(classify_recruitment("2026届夏季校园招聘"), "summer")
        self.assertEqual(classify_recruitment("2027届秋季提前批"), "autumn_early")
        self.assertEqual(classify_recruitment("2027届秋招"), "autumn")

    def test_month_alone_does_not_invent_a_recruitment_season(self) -> None:
        self.assertEqual(
            classify_recruitment("2027届校园招聘，7月1日启动"),
            "campus_recruitment",
        )

    def test_generic_campus_and_internship_content_remain_eligible(self) -> None:
        self.assertEqual(classify_recruitment("2027 校园招聘"), "campus_recruitment")
        self.assertEqual(classify_recruitment("暑期实习生招聘"), "internship")
        self.assertEqual(classify_recruitment("招商合作公告"), "other")
        self.assertEqual(classify_recruitment("采购招标公告"), "other")
        self.assertEqual(classify_recruitment("校园招聘会新闻报道"), "other")
        self.assertEqual(classify_recruitment("人才动态"), "unknown")


class StableIdentityAndEvidenceTests(TestCase):
    def setUp(self) -> None:
        organization = Organization.objects.create(
            name="Evidence Org",
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
            reason="official domain checked",
            evidence="saved review",
        )
        transition_source(
            self.source,
            to_state="enabled",
            actor_label="owner",
            reason="fixture parser accepted",
            evidence="offline fixture validation",
        )
        self.source.refresh_from_db()
        self.version = SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash="3" * 64,
        )

    @staticmethod
    def evidence(raw: str, locator: str, parsed: str | None = None) -> FieldEvidenceValue:
        return FieldEvidenceValue(raw, locator, raw if parsed is None else parsed)

    def candidate(
        self,
        *,
        identity_key: str = "batch-2027",
        url: str = "https://official.test/batches/2027",
        title: str = "2027 Campus",
    ) -> RecruitmentBatchCandidate:
        notice_evidence = {
            "title": self.evidence(title, "article[data-notice-id='batch-2027'] h2"),
            "recruitment_type": self.evidence("校园招聘", "article .type", "campus_recruitment"),
            "target_audience": self.evidence("2027届", "article .audience"),
            "published_on": self.evidence("2026-08-01", "article time.published"),
            "deadline": self.evidence("2026-09-01", "article time.deadline"),
            "official_page_url": self.evidence(url, "article a.notice", url),
        }
        position_evidence = {
            "position_title": self.evidence("Engineer", "article .position"),
            "location": self.evidence("北京", "article .location"),
            "application_link": self.evidence(
                "https://official.test/apply/1",
                "article a.apply@href",
            ),
        }
        return RecruitmentBatchCandidate(
            title=title,
            official_page_url=url,
            recruitment_type="校园招聘",
            target_audience="2027届",
            published_on=date(2026, 8, 1),
            deadline=date(2026, 9, 1),
            withdrawn=False,
            evidence_excerpt="context only",
            positions=(
                PositionCandidate(
                    title="Engineer",
                    location_text="北京",
                    raw_text="Engineer 北京",
                    application_url="https://official.test/apply/1",
                    position_key="position-1",
                    field_evidence=position_evidence,
                ),
            ),
            identity_key=identity_key,
            field_evidence=notice_evidence,
            positions_complete=True,
        )

    def test_missing_stable_identity_creates_only_rejected_decision(self) -> None:
        results = publish_candidates(
            self.source, [self.candidate(identity_key="")], self.version
        )
        self.assertEqual(results[0].action, "rejected")
        self.assertIn("missing_stable_identity", results[0].reasons)
        event = PublicationEvent.objects.get()
        self.assertEqual(event.event_type, "rejected")
        self.assertIsNone(event.batch_id)

    def test_identity_or_canonical_url_conflict_is_ambiguous_and_never_merged(self) -> None:
        first = self.candidate(identity_key="same", title="First")
        second = self.candidate(identity_key="same", title="Different")
        third = self.candidate(
            identity_key="other",
            url="https://official.test/batches/2027#second-node",
            title="Third",
        )
        results = publish_candidates(self.source, [first, second, third], self.version)
        self.assertEqual([result.action for result in results], ["rejected"] * 3)
        self.assertEqual(
            set(PublicationEvent.objects.values_list("event_type", flat=True)),
            {"ambiguous"},
        )
        self.assertFalse(self.source.recruitment_batches.exists())

    def test_every_display_field_has_immutable_event_scoped_evidence(self) -> None:
        result = publish_candidates(self.source, [self.candidate()], self.version)[0]
        self.assertEqual(result.action, "created")
        event = PublicationEvent.objects.get(batch_id=result.batch_id)
        self.assertTrue(event.evidence_complete)
        evidence = Evidence.objects.filter(publication_event=event)
        self.assertEqual(
            set(evidence.values_list("field_name", flat=True)),
            {
                "title",
                "recruitment_type",
                "target_audience",
                "published_on",
                "deadline",
                "official_page_url",
                "position_title",
                "location",
                "application_link",
            },
        )
        self.assertFalse(evidence.filter(locator="").exists())
        self.assertFalse(evidence.filter(value_hash="").exists())
        record = evidence.get(field_name="title")
        record.parsed_value = "tampered"
        with self.assertRaises(ValidationError):
            record.save()

    def test_html_extractor_uses_stable_node_ids_and_precise_field_locators(self) -> None:
        self.source.parser_config = {
            "notice_selector": "article.job",
            "notice_id_attribute": "data-notice-id",
            "position_id_attribute": "data-position-id",
            "notice_url_selector": "a.notice",
            "title_selector": "h2",
            "recruitment_type_selector": ".type",
            "target_audience_selector": ".audience",
            "published_on_selector": ".published",
            "deadline_selector": ".deadline",
            "location_selector": ".location",
            "application_selector": "a.apply",
            "position_title_selector": ".position-title",
            "excerpt_selector": ".description",
        }
        self.source.save(update_fields=["parser_config"])
        page = FetchedPage(
            self.source.source_url,
            """
            <article class="job" data-notice-id="batch-2027" data-position-id="position-1">
              <a class="notice" href="/batches/2027">batch</a>
              <h2>2027 Campus</h2><span class="type">校园招聘</span>
              <span class="audience">2027届</span><time class="published">2026-08-01</time>
              <time class="deadline">2026-09-01</time><span class="position-title">Engineer</span><span class="location">北京</span>
              <a class="apply" href="/apply/1">apply</a>
              <p class="description">Engineer 北京</p>
            </article>
            """,
            "4" * 64,
            200,
            None,
        )
        candidate = HtmlSourceAdapter().extract(self.source, page)[0]
        self.assertEqual(candidate.identity_key, "batch-2027")
        self.assertEqual(candidate.positions[0].position_key, "position-1")
        self.assertEqual(set(candidate.field_evidence), BATCH_EVIDENCE_FIELDS)
        self.assertEqual(
            set(candidate.positions[0].field_evidence),
            {"position_title", "location", "raw_text", "application_link"},
        )
        self.assertEqual(
            candidate.field_evidence["official_page_url"].raw_value,
            "/batches/2027",
        )
        self.assertFalse(candidate.positions_complete)
