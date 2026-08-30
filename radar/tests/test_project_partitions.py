import csv
import json
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase

from radar.collectors.registry import AdapterRegistry
from radar.services.project_partitions import (
    PARTITIONED_COMPANIES,
    partitioned_parser_config,
)


ROOT = Path(__file__).resolve().parents[2]


class ProjectPartitionConfigurationTests(SimpleTestCase):
    @staticmethod
    def catalog_rows() -> dict[str, dict]:
        with (ROOT / "data" / "source_catalog.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            return {
                row["organization_name"]: row
                for row in csv.DictReader(handle)
                if row["organization_name"] in PARTITIONED_COMPANIES
            }

    def test_all_four_partition_contracts_are_valid_and_idempotent(self) -> None:
        rows = self.catalog_rows()
        self.assertEqual(set(rows), set(PARTITIONED_COMPANIES))
        expected_counts = {"京东": 3, "腾讯": 3, "美团": 3, "大疆创新": 2}
        for company in PARTITIONED_COMPANIES:
            with self.subTest(company=company):
                row = rows[company]
                base = json.loads(row["parser_config"])
                configured = partitioned_parser_config(
                    company,
                    row["adapter_name"],
                    base,
                )
                configured_again = partitioned_parser_config(
                    company,
                    row["adapter_name"],
                    configured,
                )
                self.assertEqual(configured_again, configured)
                partitions = configured["batch_partitions"]
                self.assertEqual(len(partitions), expected_counts[company])
                self.assertEqual(
                    len({item["batch"]["identity_key"] for item in partitions}),
                    len(partitions),
                )
                self.assertEqual(
                    {item["batch"]["official_page_url"] for item in partitions},
                    {configured["batch"]["official_page_url"]},
                )
                source = SimpleNamespace(
                    adapter_name=row["adapter_name"],
                    parser_config=configured,
                    source_url=row["source_url"],
                    official_entrypoint_url=row["official_entrypoint_url"],
                    organization=SimpleNamespace(
                        official_domain=row["official_domain"]
                    ),
                )
                self.assertIsNone(AdapterRegistry.validate_source_config(source))

    def test_contract_rejects_an_unexpected_endpoint_or_tenant(self) -> None:
        rows = self.catalog_rows()
        jd = json.loads(rows["京东"]["parser_config"])
        jd["endpoint"] = "https://campus.jd.com/api/other"
        with self.assertRaisesRegex(ValueError, "unexpected endpoint"):
            partitioned_parser_config("京东", "json_api", jd)

        dji = json.loads(rows["大疆创新"]["parser_config"])
        dji["site_id"] = 1
        with self.assertRaisesRegex(ValueError, "unexpected Moka tenant"):
            partitioned_parser_config("大疆创新", "moka_public_api", dji)
