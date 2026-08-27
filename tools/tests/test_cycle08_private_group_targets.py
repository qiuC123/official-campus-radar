import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "targets-phase-02-t3-cycle-08-private-group.json"


class Cycle08PrivateGroupTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.targets = cls.payload["targets"]

    def test_five_targets_are_frozen_pool_private_companies(self) -> None:
        self.assertEqual(len(self.targets), 5)
        self.assertEqual(
            {target["id"] for target in self.targets},
            {"P03-C08", "P06-C08", "P09-C08", "P10-C08", "P14-C08"},
        )
        self.assertEqual(
            self.payload["target_page_invocations_planned"], len(self.targets)
        )
        self.assertEqual({target["company_type"] for target in self.targets}, {"民企"})

    def test_each_target_has_one_passive_page_and_bounded_replay(self) -> None:
        for target in self.targets:
            with self.subTest(target=target["id"]):
                self.assertEqual(target["cycle08_page_invocations"], 1)
                self.assertEqual(target["normalized_endpoint_replay_maximum"], 6)
                self.assertFalse(target["scroll"])
                self.assertNotIn("click", target)
                self.assertGreaterEqual(target["wait"], 8)

    def test_cycle_is_read_only_discovery_not_admission(self) -> None:
        self.assertFalse(self.payload["source_admission_claimed"])
        self.assertFalse(self.payload["production_browser_authorized"])
        for target in self.targets:
            self.assertTrue(target["url"].startswith("https://"))
            self.assertTrue(target["official_evidence_url"].startswith("https://"))
            self.assertNotIn("login", target["url"].lower())


if __name__ == "__main__":
    unittest.main()
