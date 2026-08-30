import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from radar.models import OfficialSource, Organization, SourceAdmissionEvent
from radar.services.admission import source_is_admitted, transition_source
from tools.build_t4_source_catalog import build_rows


class PinduoduoTitleMappingCorrectionTests(TestCase):
    def setUp(self) -> None:
        row = next(
            item for item in build_rows() if item["organization_name"] == "拼多多"
        )
        config = json.loads(row["parser_config"])
        config["field_map"]["title"] = "jobName"
        organization = Organization.objects.create(
            name="拼多多",
            company_type="private",
            industry="互联网/科技",
            official_domain="pddglobalhr.com",
        )
        source = OfficialSource.objects.create(
            organization=organization,
            source_type="api",
            source_url=row["source_url"],
            admission_evidence="saved official API evidence",
            adapter_name="json_api",
            parser_config=config,
        )
        transition_source(
            source,
            to_state="verified",
            actor_label="test-owner",
            reason="verified",
            evidence="saved official API evidence",
        )
        transition_source(
            source,
            to_state="enabled",
            actor_label="test-owner",
            reason="enabled",
            evidence="offline contract passed",
        )

    def test_default_preview_does_not_change_config_or_events(self) -> None:
        output = StringIO()
        call_command("correct_pinduoduo_title_mapping", stdout=output)
        source = OfficialSource.objects.get(organization__name="拼多多")
        self.assertEqual(source.parser_config["field_map"]["title"], "jobName")
        self.assertEqual(SourceAdmissionEvent.objects.count(), 2)
        self.assertIn("network_requests=0", output.getvalue())

    def test_apply_is_audited_and_repeated_apply_is_idempotent(self) -> None:
        call_command("correct_pinduoduo_title_mapping", "--apply")
        source = OfficialSource.objects.get(organization__name="拼多多")
        self.assertEqual(source.parser_config["field_map"]["title"], "name")
        self.assertEqual(SourceAdmissionEvent.objects.count(), 5)
        self.assertTrue(source_is_admitted(source))

        output = StringIO()
        call_command("correct_pinduoduo_title_mapping", "--apply", stdout=output)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 5)
        self.assertIn("already_correct=1", output.getvalue())

    def test_unexpected_mapping_is_rejected(self) -> None:
        source = OfficialSource.objects.get(organization__name="拼多多")
        source.parser_config["field_map"]["title"] = "categoryName"
        source.save(update_fields=["parser_config"])
        with self.assertRaisesMessage(CommandError, "unexpected Pinduoduo title mapping"):
            call_command("correct_pinduoduo_title_mapping")
