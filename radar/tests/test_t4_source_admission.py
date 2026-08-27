import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from django.core.management import call_command
from django.test import TestCase

from radar.collectors.json_api import _field_value, _path_value
from radar.collectors.registry import AdapterRegistry
from radar.models import (
    ApprovedApplicationHost,
    OfficialSource,
    Organization,
    SourceAdmissionEvent,
)
from radar.services.admission import (
    approve_application_host,
    source_is_admitted,
    transition_source,
)
from tools.build_t4_source_catalog import build_rows


ROOT = Path(__file__).resolve().parents[2]


class T4CatalogTests(TestCase):
    def test_generated_catalog_has_the_frozen_25_and_confirmed_type_mix(self) -> None:
        rows = build_rows()

        self.assertEqual(len(rows), 25)
        self.assertEqual(len({row["organization_name"] for row in rows}), 25)
        counts = {}
        for row in rows:
            counts[row["company_type"]] = counts.get(row["company_type"], 0) + 1
        self.assertEqual(
            counts,
            {"private": 16, "state_owned": 3, "foreign": 3, "joint_venture": 3},
        )

    def test_all_25_configs_pass_the_registered_adapter_contract(self) -> None:
        for row in build_rows():
            parser_config = json.loads(row["parser_config"])
            header_names = {
                str(name).lower() for name in parser_config.get("headers", {})
            }
            self.assertTrue(
                header_names.isdisjoint(
                    {"cookie", "authorization", "token", "signature"}
                )
            )
            organization = Organization(
                name=row["organization_name"],
                company_type=row["company_type"],
                industry=row["industry"],
                official_domain=row["official_domain"],
            )
            source = OfficialSource(
                organization=organization,
                source_type=row["source_type"],
                source_url=row["source_url"],
                official_entrypoint_url=row["official_entrypoint_url"],
                admission_evidence=row["admission_evidence"],
                adapter_name=row["adapter_name"],
                parser_config=parser_config,
            )
            with self.subTest(source=row["organization_name"]):
                AdapterRegistry.validate_source_config(source)

    def test_catalog_import_and_full_admission_chains_are_valid(self) -> None:
        call_command(
            "import_source_catalog",
            "--path",
            str(ROOT / "data" / "source_catalog.csv"),
        )

        self.assertEqual(OfficialSource.objects.count(), 25)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 25)
        for source in OfficialSource.objects.select_related("organization"):
            transition_source(
                source,
                to_state=OfficialSource.AdmissionState.VERIFIED,
                actor_label="t4-test",
                reason="official ownership and saved evidence checked",
                evidence="offline T3 evidence and generated parser contract",
            )
            source.refresh_from_db()
            if source.source_type == OfficialSource.SourceType.ATS:
                approve_application_host(
                    source,
                    host=urlparse(source.source_url).hostname or "",
                    actor_label="t4-test",
                    evidence="official entrypoint links this public ATS host",
                )
            transition_source(
                source,
                to_state=OfficialSource.AdmissionState.ENABLED,
                actor_label="t4-test",
                reason="adapter contract accepted",
                evidence="offline structural validation passed",
            )
            source.refresh_from_db()
            with self.subTest(source=source.organization.name):
                self.assertTrue(source_is_admitted(source))

    def test_reimport_refreshes_only_candidate_configuration(self) -> None:
        catalog = str(ROOT / "data" / "source_catalog.csv")
        call_command("import_source_catalog", "--path", catalog)
        source = OfficialSource.objects.get(organization__name="美团")
        source.parser_config = {"stale": True}
        source.save(update_fields=["parser_config"])

        call_command("import_source_catalog", "--path", catalog)

        source.refresh_from_db()
        self.assertEqual(
            source.parser_config["field_map"]["location"], "cityList[].name"
        )
        self.assertEqual(SourceAdmissionEvent.objects.count(), 25)

    def test_cycle_02_command_verifies_but_does_not_enable_sources(self) -> None:
        catalog = str(ROOT / "data" / "source_catalog.csv")
        report = str(ROOT / "work" / "phase-02-t4-offline-validation-cycle-02.json")
        call_command("import_source_catalog", "--path", catalog)

        call_command("verify_t4_sources", "--report", report, "--dry-run")
        self.assertEqual(
            OfficialSource.objects.filter(
                admission_state=OfficialSource.AdmissionState.CANDIDATE
            ).count(),
            25,
        )

        call_command("verify_t4_sources", "--report", report)

        self.assertEqual(
            OfficialSource.objects.filter(
                admission_state=OfficialSource.AdmissionState.VERIFIED,
                is_verified=True,
                is_active=False,
            ).count(),
            25,
        )
        expected_ats = sum(row["source_type"] == "ats" for row in build_rows())
        self.assertEqual(ApprovedApplicationHost.objects.count(), expected_ats)
        self.assertEqual(SourceAdmissionEvent.objects.count(), 50)
        self.assertFalse(
            any(
                source_is_admitted(source)
                for source in OfficialSource.objects.select_related("organization")
            )
        )


class JsonPathContractTests(TestCase):
    def test_array_segments_and_fallback_paths_support_real_location_shapes(self) -> None:
        row = {
            "requirements": [{"city": "北京"}, {"city": "上海"}],
            "backup": "深圳",
        }

        self.assertEqual(
            _path_value(row, "requirements[].city"),
            ["北京", "上海"],
        )
        self.assertEqual(_field_value(row, "missing||backup"), "深圳")

    def test_unix_millisecond_update_time_is_parsed_as_a_date(self) -> None:
        from radar.collectors.json_api import JsonApiSourceAdapter

        self.assertEqual(
            JsonApiSourceAdapter._parse_date(1787803459000),
            date(2026, 8, 27),
        )

    def test_iso_datetime_update_time_is_parsed_as_a_date(self) -> None:
        from radar.collectors.json_api import JsonApiSourceAdapter

        self.assertEqual(
            JsonApiSourceAdapter._parse_date("2026-08-06T17:47:21"),
            date(2026, 8, 6),
        )
