import json
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "targets-phase-02-t3-cycle-05.json"


class Cycle05TargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.targets = cls.payload["targets"]

    def test_three_unique_current_architecture_targets_are_frozen(self) -> None:
        self.assertEqual(len(self.targets), 3)
        self.assertEqual(
            {target["id"] for target in self.targets},
            {"S03-C05", "J01-C05", "P13-C05"},
        )
        self.assertEqual(self.payload["target_page_invocations_planned"], 3)
        self.assertFalse(self.payload["source_admission_claimed"])
        self.assertFalse(self.payload["production_browser_authorized"])

    def test_each_target_allows_one_discovery_invocation_and_six_replays(self) -> None:
        for target in self.targets:
            with self.subTest(target=target["id"]):
                self.assertEqual(target["cycle05_page_invocations"], 1)
                self.assertEqual(target["normalized_endpoint_replay_maximum"], 6)
                self.assertTrue(target["reason"])

    def test_vivo_target_is_the_observed_autumn_campus_list(self) -> None:
        vivo = next(target for target in self.targets if target["id"] == "P13-C05")
        parsed = urlparse(vivo["url"])
        filters = parse_qs(parsed.query)
        self.assertEqual(parsed.hostname, "hr-campus.vivo.com")
        self.assertEqual(parsed.path, "/jobs")
        self.assertIn("秋季校园招聘", filters["1"][0])
        self.assertEqual(vivo["cycle05_route_confirmation_page_views"], 2)

    def test_no_target_requests_login_or_form_interaction(self) -> None:
        for target in self.targets:
            with self.subTest(target=target["id"]):
                self.assertNotIn("click", target)
                self.assertNotIn("login", target["url"].lower())
                self.assertTrue(target["url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
