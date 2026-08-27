import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "targets-phase-02-t3-cycle-10-dji-ats.json"


class Cycle10DjiAtsTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.target = cls.payload["targets"][0]

    def test_only_the_verified_official_dji_ats_page_is_targeted(self) -> None:
        self.assertEqual(self.payload["target_page_invocations_planned"], 1)
        self.assertEqual(len(self.payload["targets"]), 1)
        self.assertEqual(self.target["id"], "P14-C10")
        self.assertEqual(self.target["company"], "大疆创新")
        self.assertEqual(
            self.target["url"],
            "https://apply.careers.dji.com/campus-recruitment/dji/143359?locale=zh-CN#/jobs",
        )

    def test_cycle_is_bounded_read_only_and_does_not_claim_admission(self) -> None:
        self.assertFalse(self.payload["source_admission_claimed"])
        self.assertFalse(self.payload["production_browser_authorized"])
        self.assertEqual(self.target["cycle10_page_invocations"], 1)
        self.assertEqual(self.target["normalized_endpoint_replay_maximum"], 6)
        self.assertFalse(self.target["scroll"])
        self.assertNotIn("click", self.target)
        self.assertGreaterEqual(self.target["wait"], 8)


if __name__ == "__main__":
    unittest.main()
