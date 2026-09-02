from pathlib import Path

from django.test import SimpleTestCase


class ProjectInstructionTests(SimpleTestCase):
    def test_wechat_oa_functionality_stays_in_wechat_oa_project(self):
        instructions = (
            Path(__file__).resolve().parents[2] / "AGENTS.md"
        ).read_text(encoding="utf-8")

        self.assertIn("必须交由 `wechat-oa` 项目修复", instructions)
        self.assertIn("招聘雷达不得复制、绕过或补丁实现这些功能", instructions)
        self.assertIn("招聘雷达自身的调用、校验、导入或领域解释错误", instructions)
