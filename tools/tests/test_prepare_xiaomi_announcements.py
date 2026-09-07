import copy
import hashlib
import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.prepare_xiaomi_announcements import SOURCE, OUTPUT, build_candidates, main


class XiaomiAnnouncementEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_numeric_notice_identity_overrides_stale_link_hints(self):
        result = build_candidates(self.evidence)
        notices = {row["notice_id"]: row for row in result["notices"]}
        self.assertTrue(notices[2]["legacy_api_link_hint"].endswith("#id=retail"))
        self.assertTrue(notices[2]["official_url"].endswith("#id=2"))
        self.assertTrue(notices[13]["official_url"].endswith("#id=13"))
        self.assertEqual(len({row["official_url"] for row in notices.values()}), 7)
        # A changed detail-page identity contract cannot silently produce authoritative URLs.
        self.evidence["rendering_evidence"]["notice_detail"] = "different renderer"
        with self.assertRaisesRegex(ValueError, "unverified_notice_rendering_identity"):
            build_candidates(self.evidence)

    def test_internship_does_not_inherit_graduate_cohort_or_infer_open_status(self):
        notices = {row["notice_id"]: row for row in build_candidates(self.evidence)["notices"]}
        internship = notices[3]
        text = json.dumps(internship["audience_evidence"], ensure_ascii=False)
        self.assertIn("海内外高校全体在校大学生", text)
        self.assertNotIn("2027", text)
        self.assertIn("全年招聘", json.dumps(internship["application_window_evidence"], ensure_ascii=False))
        self.assertFalse(internship["current_application_availability_verified"])
        self.assertEqual(notices[6]["audience_evidence"], [])  # FAQ is not another cohort announcement.
        self.assertIn("2027", json.dumps(notices[13]["audience_evidence"], ensure_ascii=False))

    def test_missing_identity_body_or_success_cannot_be_promoted(self):
        for defect in ("duplicate_id", "empty_body", "http_error", "api_error", "inactive"):
            evidence = copy.deepcopy(self.evidence)
            rows = evidence["announcements"]["rows"]
            if defect == "duplicate_id":
                rows[1]["id"] = rows[0]["id"]
            elif defect == "empty_body":
                rows[0]["body"] = ""
            elif defect == "http_error":
                evidence["requests"][1]["http_status"] = 403
            elif defect == "api_error":
                evidence["announcements"]["success"] = False
            else:
                rows[0]["isDel"] = True
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                build_candidates(evidence)

    def test_program_and_notice_ids_do_not_become_ats_project_ids(self):
        result = build_candidates(self.evidence)
        self.assertEqual(result["notice_count"], 7)
        self.assertEqual(result["official_navigation_program_count"], 3)
        for row in result["notices"] + result["program_navigation"]:
            self.assertIsNone(row["ats_subject_id"])
        overseas = [button for row in result["program_navigation"] for button in row["buttons"]
                    if button["label"] == "查看海外岗位"]
        self.assertEqual({button["url"] for button in overseas}, {"https://career.mi.com/career"})
        self.assertFalse(result["production_admitted"])
        self.assertIn("exhaustive_project_coverage_including_overseas", result["gaps"])

    def test_offline_regeneration_matches_frozen_projection_without_default_writes(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "candidate.json"
            with patch("tools.prepare_xiaomi_announcements.OUTPUT", output), redirect_stdout(StringIO()):
                self.assertEqual(main([]), 0)
                self.assertFalse(output.exists())
                self.assertEqual(main(["--write"]), 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                             json.loads(OUTPUT.read_text(encoding="utf-8")))
        candidate = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(candidate["source"]["sha256"],
                         hashlib.sha256(SOURCE.read_bytes().replace(b"\r\n", b"\n")).hexdigest())


if __name__ == "__main__":
    unittest.main()
