import os
from pathlib import Path
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


class ProjectConfigurationTests(SimpleTestCase):
    def test_project_uses_china_time_zone(self) -> None:
        self.assertEqual(settings.TIME_ZONE, "Asia/Shanghai")
        self.assertTrue(settings.USE_TZ)

    def test_production_settings_require_an_environment_secret_key(self) -> None:
        environment = os.environ.copy()
        environment.pop("DJANGO_SECRET_KEY", None)
        environment["DJANGO_DEBUG"] = "false"
        project_root = Path(__file__).resolve().parents[2]

        result = subprocess.run(
            [sys.executable, "-c", "import campus_radar.settings"],
            cwd=project_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)
