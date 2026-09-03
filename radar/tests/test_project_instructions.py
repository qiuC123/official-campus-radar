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

    def test_availability_gate_decision_is_documented(self):
        root = Path(__file__).resolve().parents[2]
        context = (root / "CONTEXT.md").read_text(encoding="utf-8")
        decision = (
            root / "docs" / "adr" / "0010-independent-application-availability-gate.md"
        ).read_text(encoding="utf-8")

        self.assertIn("**可投递状态**", context)
        self.assertIn("岗位接口返回非空库存只能说明存在岗位记录", context)
        self.assertIn("明确关闭：跳过岗位接口", decision)
        self.assertIn("信号缺失、冲突、页面异常或后续岗位采集失败", decision)
        self.assertIn("不保存页面全文", decision)

    def test_exhaustive_project_coverage_decision_is_documented(self):
        root = Path(__file__).resolve().parents[2]
        context = (root / "CONTEXT.md").read_text(encoding="utf-8")
        decision = (
            root / "docs" / "adr" / "0011-exhaustive-project-partitions.md"
        ).read_text(encoding="utf-8")

        self.assertIn("**项目覆盖**", context)
        self.assertIn("每个保留岗位都且只能归入一个已审核分组", context)
        self.assertIn("一次无项目预筛选的完整抓取", decision)
        self.assertIn("出现未覆盖值或重复归属时", decision)
        self.assertIn("不得自动创建正式批次或归入“其他”", decision)
