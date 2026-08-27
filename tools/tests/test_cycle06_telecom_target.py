import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools" / "targets-phase-02-t3-cycle-06-telecom.json"


class Cycle06TelecomTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.target = cls.payload["targets"][0]

    def test_one_current_campus_target_is_frozen_without_admission(self) -> None:
        self.assertEqual(self.payload["cycle"], "phase-02-t3-cycle-06-telecom")
        self.assertEqual(self.target["id"], "S03-C06")
        self.assertFalse(self.payload["source_admission_claimed"])
        self.assertFalse(self.payload["production_browser_authorized"])

    def test_exactly_one_page_and_one_safe_company_click_are_allowed(self) -> None:
        self.assertEqual(self.payload["control_confirmation_page_views"], 1)
        self.assertEqual(self.target["cycle06_page_invocations"], 1)
        self.assertEqual(self.target["cycle06_safe_clicks"], 1)
        self.assertEqual(self.target["normalized_endpoint_replay_maximum"], 6)
        self.assertEqual(
            self.target["click"],
            'li:has-text("中国电信北京公司")',
        )

    def test_target_does_not_request_login_form_or_scrolling(self) -> None:
        self.assertFalse(self.target["scroll"])
        self.assertNotIn("login", self.target["url"].lower())
        self.assertNotIn("form", self.target["click"].lower())
        self.assertTrue(self.target["url"].startswith("https://"))
        self.assertIn("招聘单位(44)", self.target["reason"])


if __name__ == "__main__":
    unittest.main()
