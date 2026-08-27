import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "targets-phase-02-t3-cycle-07-next-group.json"


class Cycle07NextGroupTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.targets = cls.payload["targets"]

    def test_four_frozen_targets_cover_private_foreign_and_bank_types(self) -> None:
        self.assertEqual(len(self.targets), 4)
        self.assertEqual(
            {target["id"] for target in self.targets},
            {"P12-C07", "P08-C07", "F02-C07", "B01-C07"},
        )
        self.assertEqual(
            {target["company_type"] for target in self.targets},
            {"民企", "外资", "银行"},
        )
        self.assertEqual(self.payload["target_page_invocations_planned"], 4)

    def test_each_target_allows_one_page_and_one_bounded_replay_ladder(self) -> None:
        for target in self.targets:
            with self.subTest(target=target["id"]):
                self.assertEqual(target["cycle07_page_invocations"], 1)
                self.assertEqual(target["normalized_endpoint_replay_maximum"], 6)
                self.assertFalse(target["scroll"])
                self.assertNotIn("click", target)

    def test_cycle_never_claims_admission_or_production_browser(self) -> None:
        self.assertFalse(self.payload["source_admission_claimed"])
        self.assertFalse(self.payload["production_browser_authorized"])
        for target in self.targets:
            self.assertTrue(target["url"].startswith("https://"))
            self.assertTrue(target["official_evidence_url"].startswith("https://"))
            self.assertNotIn("login", target["url"].lower())


if __name__ == "__main__":
    unittest.main()
