import json
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from radar.models import OfficialSource, Organization, SourceAdmissionEvent
from radar.services.admission import source_is_admitted, transition_source
from tools.build_t4_source_catalog import build_rows
from tools.t6_cycle02_config_corrections import CORRECTED_COMPANIES


class T6Cycle02ConfigCorrectionTests(TestCase):
    def setUp(self) -> None:
        catalog = {
            row["organization_name"]: row
            for row in build_rows()
            if row["organization_name"] in CORRECTED_COMPANIES
        }
        self.original_configs = {}
        for name in CORRECTED_COMPANIES:
            row = catalog[name]
            config = json.loads(row["parser_config"])
            self.original_configs[name] = config
            if name == "理想汽车":
                official_domain = "lixiang.com"
            elif name == "美团":
                official_domain = "meituan.com"
            else:
                official_domain = "zhaopin.com"
            organization = Organization.objects.create(
                name=name,
                company_type="private",
                industry="测试",
                official_domain=official_domain,
            )
            source = OfficialSource.objects.create(
                organization=organization,
                source_type="api",
                source_url=row["source_url"],
                admission_evidence="T4 fixture",
                adapter_name="json_api",
                parser_config=config,
            )
            transition_source(
                source,
                to_state="verified",
                actor_label="test-owner",
                reason="verified",
                evidence="saved T4 evidence",
            )
            transition_source(
                source,
                to_state="enabled",
                actor_label="test-owner",
                reason="enabled",
                evidence="offline contract passed",
            )

    def test_dry_run_does_not_change_configs_or_admission_chain(self) -> None:
        output = StringIO()

        call_command(
            "apply_t6_cycle02_config_corrections",
            "--dry-run",
            stdout=output,
        )

        self.assertIn("network_requests=0", output.getvalue())
        self.assertEqual(SourceAdmissionEvent.objects.count(), 6)
        for source in OfficialSource.objects.select_related("organization"):
            self.assertEqual(
                source.parser_config,
                self.original_configs[source.organization.name],
            )

    def test_apply_records_nine_events_and_keeps_all_sources_admitted(self) -> None:
        call_command("apply_t6_cycle02_config_corrections")

        self.assertEqual(SourceAdmissionEvent.objects.count(), 15)
        sources = {
            source.organization.name: source
            for source in OfficialSource.objects.select_related("organization")
        }
        self.assertEqual(
            sources["理想汽车"].parser_config["pagination"]["page_size"],
            100,
        )
        self.assertEqual(
            sources["美团"].parser_config["body"]["jobType"],
            [{"code": "2", "subCode": []}],
        )
        self.assertNotIn(
            "success",
            sources["中国联合网络通信集团有限公司"].parser_config,
        )
        self.assertTrue(all(source_is_admitted(source) for source in sources.values()))

    def test_live_diagnosis_can_restore_the_unicom_success_guard_auditably(self) -> None:
        call_command("apply_t6_cycle02_config_corrections")
        output = StringIO()
        call_command(
            "restore_t6_cycle02_unicom_guard",
            "--dry-run",
            stdout=output,
        )
        self.assertIn("network_requests=0", output.getvalue())

        call_command("restore_t6_cycle02_unicom_guard")

        source = OfficialSource.objects.get(
            organization__name="中国联合网络通信集团有限公司"
        )
        self.assertEqual(
            source.parser_config["success"],
            {"path": "code", "expect": 200},
        )
        self.assertEqual(source.admission_events.count(), 8)
        self.assertTrue(source_is_admitted(source))
