from pathlib import Path

from django.test import SimpleTestCase


class ProjectInstructionTests(SimpleTestCase):
    def test_production_sources_are_official_website_and_ats_only(self):
        instructions = (
            Path(__file__).resolve().parents[2] / "AGENTS.md"
        ).read_text(encoding="utf-8")

        self.assertIn("只采用已准入的企业官网和官方招聘系统数据", instructions)
        self.assertIn("不调用 `wechat-oa`", instructions)
        self.assertIn("历史微信模型字段只为迁移兼容而保留", instructions)
