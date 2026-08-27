import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from radar.models import OfficialSource, Organization, SourceAdmissionEvent
from radar.services.admission import (
    approve_application_host,
    source_is_admitted,
    transition_source,
)
from tools.build_t4_source_catalog import build_rows
from tools.t6_cycle03_unicom_config import COMPANY, corrected_parser_config
from tools.t6_cycle05_unicom_browser_config import BROWSER_CONFIG, NEW_ADAPTER


class T6Cycle05UnicomConfigTests(TestCase):
    def setUp(self) -> None:
        row = next(
            row for row in build_rows() if row["organization_name"] == COMPANY
        )
        self.original_config = corrected_parser_config(
            json.loads(row["parser_config"])
        )
        organization = Organization.objects.create(
            name=COMPANY,
            company_type="state_owned",
            industry="通信",
            official_domain="chinaunicom.com.cn",
        )
        source = OfficialSource.objects.create(
            organization=organization,
            source_type=OfficialSource.SourceType.ATS,
            source_url="https://zglt.zhaopin.com/",
            official_entrypoint_url=(
                "https://www.chinaunicom.com.cn/46/menu01/528/column06"
            ),
            admission_evidence="T6 Cycle 04 browser evidence",
            adapter_name="ats_json_api",
            parser_config=self.original_config,
        )
        transition_source(
            source,
            to_state="verified",
            actor_label="test-owner",
            reason="verified",
            evidence="saved evidence",
        )
        approve_application_host(
            source,
            host="zglt.zhaopin.com",
            actor_label="test-owner",
            evidence="official entrypoint links this public ATS host",
        )
        transition_source(
            source,
            to_state="enabled",
            actor_label="test-owner",
            reason="enabled",
            evidence="offline contract passed",
        )

    def test_dry_run_does_not_change_source_or_chain(self) -> None:
        output = StringIO()
        call_command(
            "apply_t6_cycle05_unicom_browser_config",
            "--dry-run",
            stdout=output,
        )

        source = OfficialSource.objects.get(organization__name=COMPANY)
        self.assertIn("network_requests=0", output.getvalue())
        self.assertEqual(source.adapter_name, "ats_json_api")
        self.assertNotIn("isolated_browser", source.parser_config)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 2)

    def test_apply_changes_adapter_and_records_three_audit_events(self) -> None:
        call_command("apply_t6_cycle05_unicom_browser_config")

        source = OfficialSource.objects.get(organization__name=COMPANY)
        self.assertEqual(source.adapter_name, NEW_ADAPTER)
        self.assertEqual(source.parser_config["isolated_browser"], BROWSER_CONFIG)
        self.assertEqual(source.parser_config["batch"]["target_audience"], "2027届")
        self.assertEqual(SourceAdmissionEvent.objects.count(), 5)
        self.assertTrue(source_is_admitted(source))

    def test_apply_refuses_an_unexpected_adapter_baseline(self) -> None:
        source = OfficialSource.objects.get(organization__name=COMPANY)
        source.adapter_name = "json_api"
        source.save(update_fields=["adapter_name"])

        with self.assertRaisesMessage(CommandError, "adapter baseline"):
            call_command("apply_t6_cycle05_unicom_browser_config")
