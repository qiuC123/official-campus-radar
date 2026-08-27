import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "tools" / "stable-sources-phase-02-t3.json"
POOL = ROOT / "tools" / "targets-phase-02-t3-cycle-01.json"


class StableSourcesLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_ledger_has_exactly_25_unique_frozen_companies(self) -> None:
        sources = self.ledger["sources"]
        keys = [source["key"] for source in sources]
        pool = json.loads(POOL.read_text(encoding="utf-8"))
        pool_keys = {target["id"] for target in pool["targets"]}
        self.assertEqual(self.ledger["stable_count"], 25)
        self.assertEqual(self.ledger["minimum_required"], 25)
        self.assertEqual(len(sources), 25)
        self.assertEqual(len(set(keys)), 25)
        self.assertTrue(set(keys) <= pool_keys)

    def test_every_ledger_entry_points_to_a_passing_evidence_result(self) -> None:
        for source in self.ledger["sources"]:
            with self.subTest(company=source["company"]):
                report = json.loads(
                    (ROOT / source["evidence_file"]).read_text(encoding="utf-8")
                )
                result_key = source["evidence_result_key"]
                if result_key is None:
                    self.assertTrue(report["passed"])
                    continue
                candidates = list(report.get("results", []))
                if isinstance(report.get("result"), dict):
                    candidates.append(report["result"])
                matched = [result for result in candidates if result.get("key") == result_key]
                self.assertEqual(len(matched), 1)
                self.assertTrue(matched[0]["passed"])

    def test_final_mix_is_explicit_and_sums_to_25(self) -> None:
        counts = Counter(source["company_type"] for source in self.ledger["sources"])
        self.assertEqual(
            counts,
            Counter({"民企": 16, "央国企": 3, "外资": 3, "中外合资": 3}),
        )


if __name__ == "__main__":
    unittest.main()
