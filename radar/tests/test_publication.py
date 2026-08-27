from dataclasses import replace
from datetime import date

from django.test import TestCase

from radar.collectors.base import FieldEvidenceValue
from radar.models import (ApplicationProgress, OfficialSource, Organization,
                          RecruitmentBatch, SourceVersion)
from radar.services.publication import publish_candidate
from radar.tests.helpers import complete_candidate, create_enabled_source


class PublicationTests(TestCase):
    def setUp(self) -> None:
        self.source = create_enabled_source(name="示例公司", host="careers.example.test")
        self.version = SourceVersion.objects.create(
            source=self.source, canonical_url="https://careers.example.test", content_hash="a" * 64
        )

    def candidate(self, *, title="2027 校园招聘", location="北京", url="https://careers.example.test/2027"):
        return complete_candidate(
            self.source,
            identity_key="batch-2027",
            title=title,
            location=location,
            official_page_url=url,
        )

    def test_accepts_candidate_outside_old_four_city_gate(self) -> None:
        result = publish_candidate(self.source, self.candidate(location="杭州"), self.version)
        self.assertEqual(result.action, "created")

    def test_updates_notice_without_overwriting_personal_progress(self) -> None:
        created = publish_candidate(self.source, self.candidate(), self.version)
        progress = ApplicationProgress.objects.create(
            batch=self.source.recruitment_batches.get(pk=created.batch_id),
            status="interviewed",
        )
        updated = publish_candidate(self.source, self.candidate(title="2027 校招更新"), self.version)
        self.assertEqual(updated.action, "updated")
        progress.refresh_from_db()
        self.assertEqual(progress.status, "interviewed")

    def test_declared_campus_type_wins_over_negative_words_in_position_title(self) -> None:
        self.source.adapter_name = "json_api"
        self.source.save(update_fields=["adapter_name"])
        candidate = self.candidate()
        position = candidate.positions[0]
        position_evidence = dict(position.field_evidence)
        position_evidence["position_title"] = FieldEvidenceValue(
            "招标采购工程师",
            "#position-1 .title",
            "招标采购工程师",
        )
        candidate = replace(
            candidate,
            positions=(
                replace(
                    position,
                    title="招标采购工程师",
                    field_evidence=position_evidence,
                ),
            ),
        )

        result = publish_candidate(self.source, candidate, self.version)

        self.assertEqual(result.action, "created")
        self.assertEqual(
            RecruitmentBatch.objects.get(pk=result.batch_id).recruitment_type,
            "campus_recruitment",
        )
