import csv
import json
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase

from radar.collectors.registry import AdapterRegistry
from radar.services.application_pages import (
    BATCH_APPLICATION_URLS,
    configured_batch_application_url,
)
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
        expected_counts = {"京东": 3, "腾讯": 6, "美团": 3, "大疆创新": 2}
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

    def test_all_project_application_urls_are_configured_and_same_host(self) -> None:
        expected_application_urls = {
            "京东": {
                "official-project:jd:plan:56": (
                    "https://campus.jd.com/#/jobs?selProjects=56"
                ),
                "official-project:jd:plan:57": (
                    "https://campus.jd.com/#/jobs?selProjects=57"
                ),
                "official-project:jd:plan:58": (
                    "https://campus.jd.com/#/jobs?selProjects=58"
                ),
            },
            "腾讯": {
                "official-project:tencent:project:1": (
                    "https://join.qq.com/post.html?query=p_1"
                ),
                "official-project:tencent:project:2": (
                    "https://join.qq.com/post.html?query=p_2"
                ),
                "official-project:tencent:projects:4-12": (
                    "https://join.qq.com/post.html?query=p_104"
                ),
                "official-project:tencent:project:14": (
                    "https://join.qq.com/post.html?query=p_14"
                ),
                "official-project:tencent:project:20": (
                    "https://join.qq.com/post.html?query=p_20"
                ),
                "official-project:tencent:project:9": (
                    "https://join.qq.com/post.html?query=p_9"
                ),
            },
            "美团": {
                "official-project:meituan:special:6": (
                    "https://zhaopin.meituan.com/web/position?hiringType=2_6"
                ),
                "official-project:meituan:special:8": (
                    "https://zhaopin.meituan.com/web/longcat"
                ),
                "official-project:meituan:special:3": (
                    "https://zhaopin.meituan.com/web/beidou"
                ),
            },
            "大疆创新": {
                "official-project:dji:tuojiangzhe:2027": (
                    "https://apply.careers.dji.com/campus-recruitment/dji/143359"
                    "?locale=zh-CN#/jobs"
                ),
                "official-project:dji:digital-management:2027": (
                    "https://apply.careers.dji.com/campus-recruitment/dji/143359"
                    "?locale=zh-CN#/jobs?keyword="
                    "%E6%95%B0%E5%AD%97%E7%AE%A1%E7%90%86"
                    "&page=1&anchorName=jobsList"
                ),
            },
        }
        self.assertEqual(
            {
                company: BATCH_APPLICATION_URLS[company]
                for company in PARTITIONED_COMPANIES
            },
            expected_application_urls,
        )
        rows = self.catalog_rows()
        for company, mappings in expected_application_urls.items():
            source = SimpleNamespace(
                source_url=rows[company]["source_url"],
                organization=SimpleNamespace(name=company),
            )
            configured = partitioned_parser_config(
                company,
                rows[company]["adapter_name"],
                json.loads(rows[company]["parser_config"]),
            )
            self.assertEqual(
                set(mappings),
                {
                    item["batch"]["identity_key"]
                    for item in configured["batch_partitions"]
                },
            )
            for identity_key, expected_url in mappings.items():
                self.assertEqual(
                    configured_batch_application_url(source, identity_key),
                    expected_url,
                )
        wrong_host = SimpleNamespace(
            source_url="https://untrusted.example/",
            organization=SimpleNamespace(name="美团"),
        )
        self.assertIsNone(
            configured_batch_application_url(
                wrong_host,
                "official-project:meituan:special:8",
            )
        )

    def test_tencent_scope_includes_all_official_mapping_ids_without_an_overseas_duplicate(self) -> None:
        row = self.catalog_rows()["腾讯"]
        configured = partitioned_parser_config(
            "腾讯",
            row["adapter_name"],
            json.loads(row["parser_config"]),
        )

        self.assertEqual(
            configured["body"]["projectMappingIdList"],
            [1, 2, 104, 14, 20, 9],
        )
        identities = {
            item["batch"]["identity_key"]
            for item in configured["batch_partitions"]
        }
        self.assertEqual(len(identities), 6)
        self.assertFalse(any("overseas" in identity for identity in identities))
