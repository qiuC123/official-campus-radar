import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "targets-phase-02-t3-cycle-09-precise-pages.json"


class Cycle09PrecisePageTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.targets = cls.payload["targets"]

    def test_seven_targets_are_unique_frozen_private_companies(self) -> None:
        self.assertEqual(len(self.targets), 7)
        self.assertEqual(len({target["id"] for target in self.targets}), 7)
        self.assertEqual(
            {target["id"].split("-", 1)[0] for target in self.targets},
            {"P03", "P06", "P09", "P10", "P16", "P17", "P19"},
        )
        self.assertEqual({target["company_type"] for target in self.targets}, {"民企"})
        self.assertEqual(self.payload["target_page_invocations_planned"], 7)

    def test_each_target_is_one_passive_precise_page(self) -> None:
        for target in self.targets:
            with self.subTest(target=target["id"]):
                self.assertEqual(target["cycle09_page_invocations"], 1)
                self.assertEqual(target["normalized_endpoint_replay_maximum"], 6)
                self.assertFalse(target["scroll"])
                self.assertNotIn("click", target)
                self.assertGreaterEqual(target["wait"], 8)

    def test_cycle_is_read_only_and_never_claims_admission(self) -> None:
        self.assertFalse(self.payload["source_admission_claimed"])
        self.assertFalse(self.payload["production_browser_authorized"])
        for target in self.targets:
            self.assertTrue(target["url"].startswith("https://"))
            self.assertTrue(target["official_evidence_url"].startswith("https://"))
            self.assertNotIn("login", target["url"].lower())


if __name__ == "__main__":
    unittest.main()
