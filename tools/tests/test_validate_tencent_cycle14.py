import json
import unittest
from pathlib import Path

from tools.validate_tencent_cycle14 import run


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "api-acceptance-cycle-14-tencent-offline.json"


class TencentCycle14Tests(unittest.TestCase):
    def test_offline_re_evaluation_preserves_failure_and_passes_correct_scope(self) -> None:
        report = run(CONFIG)
        self.assertTrue(report["source_cycle_failure_preserved"])
        self.assertEqual(report["network_requests_made"], 0)
        self.assertEqual(report["reported_total"], 437)
        self.assertEqual(report["unique_ids"], 437)
        self.assertTrue(report["passed"])
        self.assertTrue(all(report["checks"].values()))

    def test_frozen_labels_cover_all_cycle13_raw_values(self) -> None:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cycle13 = json.loads(
            (ROOT / config["source_report"]).read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(config["allowed_observed_labels"]),
            set(cycle13["results"][0]["scope_raw_values"]),
        )


if __name__ == "__main__":
    unittest.main()
