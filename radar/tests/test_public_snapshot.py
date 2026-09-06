from contextlib import closing
import json
from pathlib import Path
import runpy
import sqlite3
import tempfile
from unittest.mock import patch

from django.core.management import call_command
from django.db import connection
from django.http import QueryDict
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from radar.models import ApplicationProgress, Organization
from radar.services.dashboard_data import build_orm_dashboard
from radar.services.public_snapshot import export_snapshot, read_snapshot, build_snapshot_dashboard
from radar.tests.helpers import create_enabled_source, publish_formal_notice


class PublicSnapshotTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "snapshot.sqlite3"
        source = create_enabled_source(name="公开企业", host="public.test")
        self.batch = publish_formal_notice(source, identity_key="public", hash_character="a")
        self.old = publish_formal_notice(source, identity_key="old", status="expired", hash_character="b")
        ApplicationProgress.objects.create(batch=self.batch, status="interviewed")
        Organization.objects.create(name="未准入私有测试", company_type="private", industry="SECRET_INTERNAL")

    def test_export_has_only_display_tables_and_never_reads_progress(self):
        with CaptureQueriesContext(connection) as queries:
            result = export_snapshot(self.path)
        self.assertEqual(result, {"batches": 2, "active_batches": 1})
        self.assertFalse(any("applicationprogress" in query["sql"].lower() for query in queries))
        with closing(sqlite3.connect(self.path)) as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertEqual(tables, {"snapshot_meta", "public_batch"})
            rows = [json.loads(row[0]) for row in db.execute("SELECT data FROM public_batch")]
            self.assertTrue(all("progress_value" not in row and "progress_label" not in row for row in rows))
        self.assertNotIn(b"SECRET_INTERNAL", self.path.read_bytes())
        self.assertEqual(ApplicationProgress.objects.get(batch=self.batch).status, "interviewed")

    def test_export_does_not_overwrite_existing_files_or_operational_database(self):
        self.path.write_bytes(b"do not touch")
        with self.assertRaises(FileExistsError):
            export_snapshot(self.path)
        self.assertEqual(self.path.read_bytes(), b"do not touch")

    def test_snapshot_filters_and_pagination_match_live_public_projection(self):
        export_snapshot(self.path)
        for historical in (False, True):
            for query in ("", "company=公开", "company=missing", "progress=applied", "page=999", "position=工程", "city=北京", "audience=2027届", "recruitment_type=internship", "company_type=private"):
                params = QueryDict(query)
                live = build_orm_dashboard(params, history=historical, include_progress=False)
                snap = build_snapshot_dashboard(params, path=self.path, history=historical)
                self.assertEqual(list(live[0].object_list), list(snap[0].object_list), query)
                self.assertEqual(live[1:], snap[1:], query)

    def test_snapshot_routes_work_without_operational_database_queries(self):
        export_snapshot(self.path)
        with override_settings(RADAR_PUBLIC_READONLY=True, RADAR_DISPLAY_SNAPSHOT=str(self.path)):
            with self.assertNumQueries(0):
                self.assertContains(self.client.get("/"), "内部预览")
                self.assertContains(self.client.get("/"), "快照生成：")
                self.assertNotContains(self.client.get("/"), "尚未启用云端自动更新")
                self.assertEqual(self.client.get("/history/").status_code, 200)
                self.assertEqual(self.client.get(f"/batches/{self.batch.pk}/positions/").status_code, 200)
                self.assertEqual(self.client.get("/batches/999999/positions/").status_code, 404)
                self.assertEqual(self.client.get("/admin/").status_code, 404)
                self.assertEqual(self.client.post("/").status_code, 405)

    def test_full_database_unknown_fields_and_bad_versions_are_rejected(self):
        export_snapshot(self.path)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TABLE auth_user (password TEXT)")
            db.commit()
        with self.assertRaises(ValueError):
            read_snapshot(self.path)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DROP TABLE auth_user")
            data = json.loads(db.execute("SELECT data FROM public_batch LIMIT 1").fetchone()[0])
            data["parser_config"] = {}
            db.execute("UPDATE public_batch SET data=?", (json.dumps(data),))
            db.commit()
        with self.assertRaises(ValueError):
            read_snapshot(self.path)

    def test_credential_like_content_fails_before_output_creation(self):
        from dataclasses import replace
        from radar.services.public_snapshot import _encode
        page, *_ = build_orm_dashboard(QueryDict(), include_progress=False)
        batch = page.object_list[0]
        for changed in (
            replace(batch, progress_value="applied"),
            replace(batch, official_page_url="https://public.test/?api_key=secret"),
            replace(batch, official_page_url="https://user:secret@public.test/"),
            replace(batch, title="EXA_API_KEY=secret"),
            replace(batch, official_page_url="https://mp.weixin.qq.com/s/abc"),
        ):
            with self.assertRaises(ValueError):
                _encode(changed)

    def test_export_command_restores_connection_read_only_flag(self):
        before = connection.cursor().execute("PRAGMA query_only").fetchone()[0]
        call_command("export_public_snapshot", out=str(self.path))
        self.assertEqual(connection.cursor().execute("PRAGMA query_only").fetchone()[0], before)

    def test_preview_config_requires_opt_in_and_loopback(self):
        import os
        import sys
        import types
        from django.core.exceptions import ImproperlyConfigured
        export_snapshot(self.path)
        env = {"DJANGO_SECRET_KEY": "0123456789abcdef" * 4, "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost", "RADAR_DATABASE_PATH": str(self.path)}
        with patch.dict(os.environ, env, clear=True):
            module = types.ModuleType("campus_radar.settings_public")
            module.__dict__.update(runpy.run_module("campus_radar.settings_public"))
            with patch.dict(sys.modules, {"campus_radar.settings_public": module}):
                with self.assertRaises(ImproperlyConfigured):
                    runpy.run_module("campus_radar.settings_private_preview")
                with patch.dict(os.environ, {"RADAR_SSH_PREVIEW": "1"}):
                    config = runpy.run_module("campus_radar.settings_private_preview")
                    self.assertFalse(config["DEBUG"])
                    self.assertTrue(config["RADAR_PUBLIC_READONLY"])
                    self.assertFalse(config["SECURE_SSL_REDIRECT"])
                    self.assertEqual(config["RADAR_DISPLAY_SNAPSHOT"], str(self.path))
                    module.ALLOWED_HOSTS = ["public.example.test"]
                    with self.assertRaises(ImproperlyConfigured):
                        runpy.run_module("campus_radar.settings_private_preview")
                self.assertTrue(module.SECURE_SSL_REDIRECT)

    def test_deployment_launcher_constrains_network_user_and_files(self):
        root = Path(__file__).resolve().parents[2]
        config = runpy.run_path(str(root / "scripts/setup_private_preview.py"))
        unit = config["UNIT"]
        for item in ("User=radar-preview", "--bind 127.0.0.1:8765", "--workers 1", "ProtectSystem=strict", "NoNewPrivileges=true"):
            self.assertIn(item, unit)
        script = (root / "scripts/setup_private_preview.py").read_text()
        for item in ("AllowTcpForwarding local", "PermitListen none", "PermitOpen 127.0.0.1:8765", "read_snapshot(snapshot)", "sshd_config.radar-preview-before"):
            self.assertIn(item, script)
        tunnel = (root / "scripts/open_private_preview.ps1").read_text()
        self.assertIn("127.0.0.1:18765:127.0.0.1:8765", tunnel)
        self.assertIn("StrictHostKeyChecking=yes", tunnel)

    def test_preview_wsgi_boots_with_display_only_database(self):
        import os
        import subprocess
        import sys
        export_snapshot(self.path)
        result = subprocess.run(
            [sys.executable, "-c", "from campus_radar.preview_wsgi import application; print(type(application).__name__)"],
            cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=20,
            env={**os.environ, "DJANGO_SECRET_KEY": "0123456789abcdef" * 4,
                 "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost", "RADAR_DATABASE_PATH": str(self.path),
                 "RADAR_SSH_PREVIEW": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("StaticFilesHandler", result.stdout)
