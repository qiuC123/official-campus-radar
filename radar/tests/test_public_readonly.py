import os
from contextlib import closing
from pathlib import Path
import runpy
import sqlite3
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from radar.models import ApplicationProgress
from radar.tests.helpers import create_enabled_source, publish_formal_notice


@override_settings(RADAR_PUBLIC_READONLY=True)
class PublicReadOnlyTests(TestCase):
    def setUp(self):
        source = create_enabled_source(name="公开企业", host="public.test")
        self.batch = publish_formal_notice(source, identity_key="public", hash_character="a")
        self.old = publish_formal_notice(source, identity_key="old", status="expired", hash_character="b")
        for batch in (self.batch, self.old):
            ApplicationProgress.objects.create(batch=batch, status="interviewed")

    def test_public_pages_neither_fetch_nor_render_personal_progress(self):
        for path in ("/", "/history/"):
            with self.subTest(path=path), CaptureQueriesContext(connection) as queries:
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "我的进度")
                self.assertNotContains(response, "投递进度")
                self.assertNotContains(response, "data-save-url")
                self.assertFalse(response.context["show_operations"])
                self.assertEqual(response.context["summary"].applications_in_progress, 0)
                for batch in response.context["batches"]:
                    self.assertEqual(batch.progress_value, "")
                    self.assertEqual(batch.progress_label, "")
                self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertFalse(any("radar_applicationprogress" in query["sql"].lower() for query in queries))

    def test_progress_filter_cannot_be_used_to_infer_owner_state(self):
        for path in ("/", "/history/"):
            baseline = self.client.get(path).content
            self.assertEqual(self.client.get(path + "?progress=not_applied").content, baseline)
            self.assertEqual(self.client.get(path + "?progress=interviewed").content, baseline)

    def test_public_allowlist_blocks_private_routes_even_for_superuser(self):
        admin = get_user_model().objects.create_superuser("owner", password="test-secret")
        self.client.force_login(admin)
        for path in ("/admin/", "/admin/login/", "/applications/", "/preview/phase-02/", "/not-a-route/"):
            self.assertEqual(self.client.get(path).status_code, 404, path)
        response = self.client.get("/")
        self.assertFalse(response.context["show_operations"])

    def test_direct_write_and_non_read_methods_cannot_mutate_progress(self):
        response = self.client.post(f"/batches/{self.batch.pk}/progress/", {"status": "applied"})
        self.assertEqual(response.status_code, 404)
        for method in ("post", "put", "delete", "patch"):
            self.assertEqual(getattr(self.client, method)("/").status_code, 405)
        self.assertEqual(ApplicationProgress.objects.get(batch=self.batch).status, "interviewed")

    def test_position_details_and_head_remain_available(self):
        self.assertEqual(self.client.get(f"/batches/{self.batch.pk}/positions/").status_code, 200)
        self.assertEqual(self.client.head("/").status_code, 200)

    @override_settings(RADAR_PUBLIC_READONLY=False)
    def test_local_owner_workflow_is_preserved(self):
        self.assertContains(self.client.get("/"), "我的进度")
        self.assertEqual(self.client.get("/applications/").status_code, 200)
        self.assertEqual(self.client.post(f"/batches/{self.batch.pk}/progress/", {"status": "applied"}).status_code, 200)


class PublicSettingsTests(SimpleTestCase):
    def test_deployment_document_preserves_public_and_private_boundary(self):
        root = Path(__file__).resolve().parents[2]
        document = (root / "docs/deployment-trial.md").read_text(encoding="utf-8")
        state = (root / "DEV_STATE.md").read_text(encoding="utf-8")
        for contract in ("campus_radar.settings_public", "mode=ro", "不读取 ApplicationProgress", "0035_exa_first_discovery_records", "不接管 Windows 计划任务"):
            self.assertIn(contract, document)
        self.assertIn("docs/deployment-trial.md", state)
        self.assertIn("低预算试运行先使用 SQLite", state)
        self.assertIn("gunicorn==26.2.0", (root / "requirements-server.txt").read_text())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "public snapshot.sqlite3"
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("CREATE TABLE sample (id INTEGER)")
            db.commit()
        self.env = {
            "DJANGO_SECRET_KEY": "0123456789abcdefghij" * 4,
            "DJANGO_ALLOWED_HOSTS": "radar.example.test,127.0.0.1",
            "RADAR_DATABASE_PATH": str(self.db),
        }

    def load(self, **changes):
        with patch.dict(os.environ, {**self.env, **changes}, clear=True):
            return runpy.run_module("campus_radar.settings_public")

    def test_public_settings_are_fail_closed_and_database_is_read_only(self):
        config = self.load(DJANGO_DEBUG="true")
        self.assertFalse(config["DEBUG"])
        self.assertTrue(config["RADAR_PUBLIC_READONLY"])
        self.assertTrue(config["SESSION_COOKIE_SECURE"])
        self.assertTrue(config["CSRF_COOKIE_SECURE"])
        self.assertTrue(config["SECURE_SSL_REDIRECT"])
        database = config["DATABASES"]["default"]
        db = sqlite3.connect(database["NAME"], uri=database["OPTIONS"]["uri"])
        try:
            self.assertEqual(db.execute("SELECT count(*) FROM sample").fetchone()[0], 0)
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("INSERT INTO sample VALUES (1)")
        finally:
            db.close()

    def test_required_configuration_cannot_be_omitted_or_broadened(self):
        for values in (
            {"DJANGO_SECRET_KEY": ""}, {"DJANGO_SECRET_KEY": "a" * 60},
            {"DJANGO_ALLOWED_HOSTS": ""}, {"DJANGO_ALLOWED_HOSTS": "*"},
            {"DJANGO_ALLOWED_HOSTS": ".example.test"},
            {"RADAR_DATABASE_PATH": "db.sqlite3"},
            {"RADAR_DATABASE_PATH": str(self.db.parent / "missing.sqlite3")},
            {"RADAR_STATIC_ROOT": str(self.db.parent)},
            {"RADAR_STATIC_ROOT": "relative-static"},
        ):
            with self.subTest(values=values), self.assertRaises(ImproperlyConfigured):
                self.load(**values)

    def test_forwarded_https_is_only_trusted_when_explicitly_enabled(self):
        self.assertNotIn("SECURE_PROXY_SSL_HEADER", self.load())
        self.assertEqual(self.load(RADAR_TRUST_PROXY_HTTPS="1")["SECURE_PROXY_SSL_HEADER"], ("HTTP_X_FORWARDED_PROTO", "https"))
