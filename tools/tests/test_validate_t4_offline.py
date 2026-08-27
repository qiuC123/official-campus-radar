import json
import unittest

from tools.build_t4_source_catalog import build_rows
from tools.validate_t4_offline import inflate_sample, validate_offline


class T4OfflineValidationTests(unittest.TestCase):
    def test_all_frozen_sources_pass_without_network_or_database_writes(self) -> None:
        report = validate_offline()

        self.assertTrue(report["passed"])
        self.assertEqual(report["source_count"], 25)
        self.assertEqual(report["passed_count"], 25)
        self.assertEqual(report["failed_count"], 0)
        self.assertEqual(report["network_requests_made"], 0)
        self.assertFalse(report["database_writes"])
        self.assertTrue(
            all(result["extracted_position_count"] for result in report["results"])
        )

    def test_catalog_keeps_scope_and_update_semantics_from_cycle_02(self) -> None:
        configs = {
            row["organization_name"]: json.loads(row["parser_config"])
            for row in build_rows()
        }

        self.assertEqual(
            configs["美团"]["field_map"]["location"],
            "cityList[].name",
        )
        self.assertEqual(configs["腾讯"]["row_filters"], [])
        self.assertEqual(configs["比亚迪"]["row_filters"], [])
        self.assertEqual(
            configs["一汽-大众汽车有限公司"]["row_filters"],
            [{"path": "projectName", "equals_any": ["2026校园招聘"]}],
        )
        self.assertEqual(
            configs["百度"]["field_map"]["updated_at"], "updateDate"
        )
        self.assertEqual(
            configs["中国联合网络通信集团有限公司"]["field_map"]["updated_at"],
            "job.modifiedTime",
        )
        self.assertNotIn(
            "updated_at", configs["中国电信集团有限公司"]["field_map"]
        )
        self.assertEqual(
            configs["苹果中国"]["field_map"]["updated_at"], ""
        )

    def test_redacted_flat_array_and_dotted_keys_are_rebuilt(self) -> None:
        inflated = inflate_sample(
            {
                "job.id": 42,
                "job.title": "工程师",
                "locations[].city": "深圳市",
            }
        )

        self.assertEqual(
            inflated,
            {
                "job": {"id": 42, "title": "工程师"},
                "locations": [{"city": "深圳市"}],
            },
        )


if __name__ == "__main__":
    unittest.main()
