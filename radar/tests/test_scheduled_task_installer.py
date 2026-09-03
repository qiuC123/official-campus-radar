from pathlib import Path

from django.test import SimpleTestCase


class ScheduledTaskInstallerTests(SimpleTestCase):
    def test_installer_registers_two_safe_non_overlapping_triggers(self) -> None:
        root = Path(__file__).resolve().parents[2]
        script = (root / "scripts" / "install_daily_task.ps1").read_text(
            encoding="utf-8"
        )

        self.assertIn("@('12:00', '20:00')", script)
        self.assertIn("-StartWhenAvailable", script)
        self.assertIn("-MultipleInstances IgnoreNew", script)
        self.assertIn("-ExecutionTimeLimit (New-TimeSpan -Hours 2)", script)
        self.assertIn("Get-Command 'py.exe' -ErrorAction Stop", script)
        self.assertIn("-Trigger $triggers", script)
        self.assertIn("if (-not $Apply)", script)
        self.assertIn("run_daily_update --trigger scheduled", script)
        self.assertNotIn("discover_official_announcements", script)

        runbook = (
            root / "docs" / "runbooks" / "windows-scheduled-task.md"
        ).read_text(encoding="utf-8")
        specification = (
            root / "docs" / "PROJECT_DEVELOPMENT_SPEC.md"
        ).read_text(encoding="utf-8")
        self.assertIn("每日 12:00、20:00", runbook)
        self.assertIn("新的触发会被忽略", runbook)
        self.assertIn("不会调用 Exa、Codex 或 `wechat-oa`", runbook)
        self.assertIn("每日 12:00 和 20:00 更新", specification)
