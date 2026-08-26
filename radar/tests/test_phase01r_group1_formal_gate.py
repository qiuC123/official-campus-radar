import hashlib

from django.apps import apps
from django.contrib import admin
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase

from radar.models import (
    ApprovedApplicationHost,
    ApplicationLink,
    Evidence,
    FetchRun,
    RecruitmentPosition,
    OfficialSource,
    Organization,
    OrganizationAlias,
    RecruitmentBatch,
    SourceAdmissionEvent,
    SourceVersion,
    UpdateRun,
)
from radar.services.admission import transition_source
from radar.tests.helpers import valid_html_parser_config


class FormalListingGateTests(TestCase):
    def setUp(self) -> None:
        self.organization = Organization.objects.create(
            name="Gate Org",
            company_type="internet",
            industry="tech",
            official_domain="official.test",
        )
        source_kwargs = {
            "organization": self.organization,
            "source_type": "website",
            "source_url": "https://official.test/careers",
            "admission_evidence": "reviewed",
            "parser_config": valid_html_parser_config(),
        }
        self.source = OfficialSource.objects.create(**source_kwargs)
        transition_source(
            self.source,
            to_state="verified",
            actor_label="test-owner",
            reason="official domain checked",
            evidence="saved review",
        )
        transition_source(
            self.source,
            to_state="enabled",
            actor_label="test-owner",
            reason="fixture checked",
            evidence="fixture result",
        )
        self.source.refresh_from_db()

    def test_notice_source_is_database_required(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            RecruitmentBatch.objects.create(
                organization=self.organization,
                title="Untraceable",
                official_page_url="https://official.test/untraceable",
            )

    def test_dashboard_requires_committed_publication_event_and_complete_evidence(self) -> None:
        batch = RecruitmentBatch.objects.create(
            organization=self.organization,
            source=self.source,
            title="2027 Campus",
            official_page_url="https://official.test/2027",
            identity_key="batch-2027",
        )
        self.assertNotContains(self.client.get("/"), batch.official_page_url)

        try:
            publication_event_model = apps.get_model("radar", "PublicationEvent")
        except LookupError:
            self.fail("PublicationEvent is required for a formal publication decision")
        version = SourceVersion.objects.create(
            source=self.source,
            canonical_url=self.source.source_url,
            content_hash="1" * 64,
            is_applied=True,
        )
        incomplete_event = publication_event_model.objects.create(
            source_version=version,
            event_type="published",
            identity_key=batch.identity_key,
            batch=batch,
            evidence_complete=False,
        )
        batch.latest_publication_event = incomplete_event
        batch.save(update_fields=["latest_publication_event"])
        self.assertNotContains(self.client.get("/"), batch.official_page_url)

        complete_event = publication_event_model.objects.create(
            source_version=version,
            event_type="updated",
            identity_key=batch.identity_key,
            batch=batch,
            evidence_complete=True,
        )
        batch.latest_publication_event = complete_event
        batch.save(update_fields=["latest_publication_event"])
        RecruitmentPosition.objects.create(
            batch=batch,
            position_key="position-1",
            title="Engineer",
            location_text="北京",
            normalized_locations=["北京"],
        )
        self.assertNotContains(self.client.get("/"), batch.official_page_url)
        position = batch.positions.get()
        batch_values = {
            "title": batch.title,
            "recruitment_type": batch.recruitment_type,
            "target_audience": batch.target_audience,
            "published_on": str(batch.published_on or ""),
            "deadline": str(batch.deadline or ""),
            "official_page_url": batch.official_page_url,
        }
        batch.target_audience = "2027届"
        batch.published_on = "2026-08-01"
        batch.deadline = "2026-09-01"
        batch.recruitment_type = RecruitmentBatch.RecruitmentType.CAMPUS_RECRUITMENT
        batch.save(
            update_fields=[
                "target_audience",
                "published_on",
                "deadline",
                "recruitment_type",
            ]
        )
        batch_values.update(
            recruitment_type="campus_recruitment",
            target_audience="2027届",
            published_on="2026-08-01",
            deadline="2026-09-01",
        )
        for field_name, value in batch_values.items():
            Evidence.objects.create(
                batch=batch,
                source_version=version,
                publication_event=complete_event,
                field_name=field_name,
                excerpt=value,
                locator=f"#{field_name}",
                raw_value=value,
                parsed_value=value,
                value_hash=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            )
        for field_name, value in (
            ("position_title", position.title),
            ("location", position.location_text),
        ):
            Evidence.objects.create(
                batch=batch,
                source_version=version,
                publication_event=complete_event,
                position=position,
                field_name=field_name,
                excerpt=value,
                locator=f"#{field_name}",
                raw_value=value,
                parsed_value=value,
                value_hash=hashlib.sha256(value.encode("utf-8")).hexdigest(),
            )
        self.assertContains(self.client.get("/"), batch.official_page_url)

        self.source.admission_state = "revoked"
        self.source.save(update_fields=["admission_state"])
        self.assertNotContains(self.client.get("/"), batch.official_page_url)


class AuditAdminBoundaryTests(TestCase):
    def test_audit_and_formal_projection_admins_cannot_add_change_or_delete(self) -> None:
        request = RequestFactory().get("/admin/")
        request.user = type(
            "Superuser",
            (),
            {"has_perm": staticmethod(lambda permission: True)},
        )()
        publication_event_model = apps.get_model("radar", "PublicationEvent")
        for model in (
            Organization,
            OrganizationAlias,
            OfficialSource,
            RecruitmentBatch,
            RecruitmentPosition,
            ApplicationLink,
            SourceVersion,
            Evidence,
            FetchRun,
            UpdateRun,
            SourceAdmissionEvent,
            ApprovedApplicationHost,
            publication_event_model,
        ):
            model_admin = admin.site._registry[model]
            self.assertFalse(model_admin.has_add_permission(request))
            self.assertFalse(model_admin.has_change_permission(request, object()))
            self.assertFalse(model_admin.has_delete_permission(request, object()))
