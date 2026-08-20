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
    NoticePosition,
    OfficialSource,
    Organization,
    OrganizationAlias,
    RecruitmentNotice,
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
            RecruitmentNotice.objects.create(
                organization=self.organization,
                title="Untraceable",
                official_notice_url="https://official.test/untraceable",
            )

    def test_dashboard_requires_committed_publication_event_and_complete_evidence(self) -> None:
        notice = RecruitmentNotice.objects.create(
            organization=self.organization,
            source=self.source,
            title="2027 Campus",
            official_notice_url="https://official.test/2027",
            identity_key="notice-2027",
        )
        self.assertNotContains(self.client.get("/"), notice.official_notice_url)

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
            identity_key=notice.identity_key,
            notice=notice,
            evidence_complete=False,
        )
        notice.latest_publication_event = incomplete_event
        notice.save(update_fields=["latest_publication_event"])
        self.assertNotContains(self.client.get("/"), notice.official_notice_url)

        complete_event = publication_event_model.objects.create(
            source_version=version,
            event_type="updated",
            identity_key=notice.identity_key,
            notice=notice,
            evidence_complete=True,
        )
        notice.latest_publication_event = complete_event
        notice.save(update_fields=["latest_publication_event"])
        NoticePosition.objects.create(
            notice=notice,
            position_key="position-1",
            title="Engineer",
            location_text="北京",
            normalized_locations=["北京"],
        )
        self.assertNotContains(self.client.get("/"), notice.official_notice_url)
        position = notice.positions.get()
        notice_values = {
            "title": notice.title,
            "recruitment_type": notice.recruitment_type,
            "target_audience": notice.target_audience,
            "published_on": str(notice.published_on or ""),
            "deadline": str(notice.deadline or ""),
            "notice_url": notice.official_notice_url,
        }
        notice.target_audience = "2027届"
        notice.published_on = "2026-08-01"
        notice.deadline = "2026-09-01"
        notice.recruitment_type = RecruitmentNotice.RecruitmentType.CAMPUS_RECRUITMENT
        notice.save(
            update_fields=[
                "target_audience",
                "published_on",
                "deadline",
                "recruitment_type",
            ]
        )
        notice_values.update(
            recruitment_type="campus_recruitment",
            target_audience="2027届",
            published_on="2026-08-01",
            deadline="2026-09-01",
        )
        for field_name, value in notice_values.items():
            Evidence.objects.create(
                notice=notice,
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
                notice=notice,
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
        self.assertContains(self.client.get("/"), notice.official_notice_url)

        self.source.admission_state = "revoked"
        self.source.save(update_fields=["admission_state"])
        self.assertNotContains(self.client.get("/"), notice.official_notice_url)


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
            RecruitmentNotice,
            NoticePosition,
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
