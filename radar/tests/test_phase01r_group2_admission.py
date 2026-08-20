import csv
import json
import tempfile

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from radar.models import OfficialSource, Organization
from radar.services import admission
from radar.tests.helpers import valid_html_parser_config


class AppendOnlyAdmissionTests(TestCase):
    def setUp(self) -> None:
        self.organization = Organization.objects.create(
            name="Admission Org",
            company_type="internet",
            industry="tech",
            official_domain="official.test",
        )
        self.source = OfficialSource.objects.create(
            organization=self.organization,
            source_type="website",
            source_url="https://official.test/careers",
            admission_evidence="catalog candidate note",
            parser_config=valid_html_parser_config(),
        )

    def test_candidate_must_follow_verified_then_enabled_with_append_only_events(self) -> None:
        transition_source = getattr(admission, "transition_source")
        with self.assertRaises(ValidationError):
            transition_source(
                self.source,
                to_state="enabled",
                actor_label="owner",
                reason="skip verification",
                evidence="none",
            )

        transition_source(
            self.source,
            to_state="verified",
            actor_label="owner",
            reason="official domain checked",
            evidence="saved local review record",
        )
        transition_source(
            self.source,
            to_state="enabled",
            actor_label="owner",
            reason="approved for low-frequency collection",
            evidence="selectors validated against fixture",
        )
        self.source.refresh_from_db()
        self.assertEqual(self.source.admission_state, "enabled")
        events = list(self.source.admission_events.order_by("pk"))
        self.assertEqual(
            [(event.from_state, event.to_state) for event in events],
            [("candidate", "verified"), ("verified", "enabled")],
        )
        events[0].reason = "rewrite history"
        with self.assertRaises(ValidationError):
            events[0].save()

    def test_legacy_booleans_cannot_bypass_admission_state(self) -> None:
        self.source.is_verified = True
        self.source.is_active = True
        self.source.save(update_fields=["is_verified", "is_active"])
        self.assertFalse(admission.source_is_admitted(self.source))

    def test_management_command_records_audited_transition(self) -> None:
        call_command(
            "transition_source_admission",
            "--source-id",
            str(self.source.pk),
            "--to-state",
            "verified",
            "--actor",
            "local-owner",
            "--reason",
            "official domain checked",
            "--evidence",
            "saved local verification",
        )
        self.source.refresh_from_db()
        self.assertEqual(self.source.admission_state, "verified")
        event = self.source.admission_events.get()
        self.assertEqual(event.actor_label, "local-owner")
        self.assertEqual(event.to_state, "verified")


class HostTrustChainTests(TestCase):
    def setUp(self) -> None:
        organization = Organization.objects.create(
            name="Host Org",
            company_type="internet",
            industry="tech",
            official_domain="official.test",
        )
        self.source = OfficialSource.objects.create(
            organization=organization,
            source_type="website",
            source_url="https://official.test/careers",
            official_entrypoint_url="https://official.test/careers",
            admission_evidence="candidate",
        )
        admission.transition_source(
            self.source,
            to_state="verified",
            actor_label="owner",
            reason="official domain checked",
            evidence="saved verification",
        )

    def test_notice_host_and_external_application_host_are_separate(self) -> None:
        self.assertTrue(
            admission.source_permits_notice_url(
                self.source, "https://official.test/notices/2027"
            )
        )
        self.assertFalse(
            admission.source_permits_application_url(
                self.source, "https://apply.ats.test/jobs/1"
            )
        )
        admission.approve_application_host(
            self.source,
            host="apply.ats.test",
            actor_label="owner",
            evidence="official career page links to this ATS host",
        )
        self.assertTrue(
            admission.source_permits_application_url(
                self.source, "https://apply.ats.test/jobs/1"
            )
        )
        self.assertFalse(
            admission.source_permits_notice_url(
                self.source, "https://apply.ats.test/jobs/1"
            )
        )


class AliasConflictTests(TestCase):
    def test_catalog_resolution_hard_fails_when_name_and_alias_point_to_different_orgs(self) -> None:
        alias_model = apps.get_model("radar", "OrganizationAlias")
        exact = Organization.objects.create(
            name="Shared Name", company_type="internet", industry="tech"
        )
        other = Organization.objects.create(
            name="Other Org", company_type="internet", industry="tech"
        )
        alias_model.objects.create(
            organization=other,
            alias=" shared   name ",
            normalized_alias="shared name",
        )
        file = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False
        )
        with file:
            fields = [
                "organization_name",
                "company_type",
                "industry",
                "official_domain",
                "source_type",
                "source_url",
                "admission_evidence",
                "adapter_name",
                "parser_config",
                "is_active",
            ]
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerow(
                {
                    "organization_name": "Shared Name",
                    "company_type": "internet",
                    "industry": "tech",
                    "official_domain": "official.test",
                    "source_type": "website",
                    "source_url": "https://official.test/jobs",
                    "admission_evidence": "candidate note",
                    "adapter_name": "html_selector",
                    "parser_config": json.dumps(
                        {"notice_selector": "article", "title_selector": "h2"}
                    ),
                    "is_active": "false",
                }
            )
        with self.assertRaises(CommandError):
            call_command("import_source_catalog", "--path", file.name)
        self.assertEqual(Organization.objects.count(), 2)
        self.assertFalse(OfficialSource.objects.exists())
        self.assertTrue(Organization.objects.filter(pk=exact.pk).exists())
