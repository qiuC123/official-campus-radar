from contextlib import closing, nullcontext
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from unittest import skipUnless

from django.test import SimpleTestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from scripts import cloud_update, export_collector_seed


class CollectorSeedTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.sqlite3"
        self.output = self.root / "seed.sqlite3"
        with closing(sqlite3.connect(self.source)) as db:
            db.executescript('''CREATE TABLE radar_officialsource (id INTEGER PRIMARY KEY, source_type TEXT, parser_config TEXT, source_url TEXT, last_error TEXT);
                INSERT INTO radar_officialsource VALUES (1,'api','{}','https://official.test/jobs','old error');
                CREATE TABLE auth_user (password TEXT); INSERT INTO auth_user VALUES ('NEVER_EXPORT_PASSWORD');
                CREATE TABLE radar_applicationprogress (note TEXT); INSERT INTO radar_applicationprogress VALUES ('NEVER_EXPORT_PROGRESS');''')
        self.guard = patch.object(export_collector_seed, "TABLES", {"radar_officialsource"})
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def test_explicit_export_keeps_empty_private_schemas_and_source_unchanged(self):
        before = self.source.read_bytes()
        export_collector_seed.export_seed(self.source, self.output)
        self.assertEqual(before, self.source.read_bytes())
        self.assertNotIn(b"NEVER_EXPORT", self.output.read_bytes())
        with closing(sqlite3.connect(self.output)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM auth_user").fetchone(), (0,))
            self.assertEqual(db.execute("SELECT last_error FROM radar_officialsource").fetchone(), ("",))
        with self.assertRaises(FileExistsError):
            export_collector_seed.export_seed(self.source, self.output)

    def test_nonofficial_or_credentials_refused_without_leaving_export(self):
        for kind, config in (("wechat", "{}"), ("api", '{"headers":{"Cookie":"private"}}')):
            with closing(sqlite3.connect(self.source)) as db:
                db.execute("UPDATE radar_officialsource SET source_type=?,parser_config=?", (kind, config))
                db.commit()
            with self.assertRaises(ValueError):
                export_collector_seed.export_seed(self.source, self.output)
            self.assertFalse(self.output.exists())


class CloudUpdateTests(SimpleTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "generations").mkdir()
        # A directory also models the current target on Windows without symlink privilege.
        (self.root / "current").mkdir()
        with closing(sqlite3.connect(self.root / "current" / "collector.sqlite3")) as db:
            db.execute("CREATE TABLE original (value TEXT)")
            db.commit()
        (self.root / "current" / "display.sqlite3").write_bytes(b"previous display")

    def worker(self, status, returncode=0, failed=0, rejected=0):
        def execute(argv, **kwargs):
            Path(argv[argv.index("--report") + 1]).write_text(json.dumps({"status": status, "sources_checked": 29, "sources_failed": failed, "batches_rejected": rejected}))
            Path(argv[argv.index("--out") + 1]).write_bytes(b"new snapshot")
            self.assertEqual(kwargs["env"]["DJANGO_SETTINGS_MODULE"], "campus_radar.settings_collector")
            self.assertNotIn("EXA_API_KEY", kwargs["env"])
            return SimpleNamespace(returncode=returncode)
        return execute

    def test_partial_failure_never_promotes_even_with_zero_exit(self):
        before = (self.root / "current" / "collector.sqlite3").read_bytes()
        with patch.object(cloud_update, "exclusive_lock", return_value=nullcontext()), patch.object(cloud_update.subprocess, "run", side_effect=self.worker("partial_failure", failed=1)), patch.object(cloud_update, "promote") as promote:
            result = cloud_update.run_once(self.root, self.root, "manual")
        self.assertEqual(result["status"], "failed")
        promote.assert_not_called()
        self.assertEqual(before, (self.root / "current" / "collector.sqlite3").read_bytes())
        self.assertEqual((self.root / "current" / "display.sqlite3").read_bytes(), b"previous display")

    def test_complete_success_is_only_promotion_path(self):
        with patch.object(cloud_update, "exclusive_lock", return_value=nullcontext()), patch.object(cloud_update.subprocess, "run", side_effect=self.worker("success")), patch.object(cloud_update, "promote") as promote:
            result = cloud_update.run_once(self.root, self.root, "scheduled")
        self.assertEqual(result["status"], "success")
        promote.assert_called_once()
        self.assertEqual(json.loads((self.root / "latest.json").read_text())["status"], "success")

    def test_timeout_preserves_previous_generation_and_records_failure(self):
        with patch.object(cloud_update, "exclusive_lock", return_value=nullcontext()), patch.object(cloud_update.subprocess, "run", side_effect=TimeoutError), patch.object(cloud_update, "promote") as promote:
            result = cloud_update.run_once(self.root, self.root, "scheduled")
        self.assertEqual(result["error_type"], "TimeoutError")
        promote.assert_not_called()

    def test_backup_copy_is_independent_and_checks_integrity(self):
        target = self.root / "backup.sqlite3"
        cloud_update.copy_database((self.root / "current" / "collector.sqlite3").resolve(), target)
        with closing(sqlite3.connect(target)) as db:
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            db.execute("INSERT INTO original VALUES ('backup-only')")
            db.commit()
        with closing(sqlite3.connect(self.root / "current" / "collector.sqlite3")) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM original").fetchone(), (0,))

    @skipUnless(os.name == "posix", "Linux atomic symlink and flock integration")
    def test_linux_atomic_publication_rollback_and_lock(self):
        # Use a separate root because the portable tests model current as a directory.
        root = self.root / "linux"
        (root / "generations").mkdir(parents=True)
        for name in ("seed", "run-next"):
            generation = root / "generations" / name
            generation.mkdir()
            cloud_update.copy_database((self.root / "current" / "collector.sqlite3").resolve(), generation / "collector.sqlite3")
            with closing(sqlite3.connect(generation / "display.sqlite3")) as db:
                db.executescript("CREATE TABLE snapshot_meta (schema_version INTEGER); CREATE TABLE public_batch (id INTEGER); INSERT INTO public_batch VALUES (1);")
        cloud_update.promote(root, root / "generations" / "seed")
        cloud_update.promote(root, root / "generations" / "run-next")
        self.assertEqual((root / "current").resolve().name, "run-next")
        cloud_update.promote(root, root / "generations" / "seed")
        self.assertEqual((root / "current").resolve().name, "seed")
        with cloud_update.exclusive_lock(root):
            with self.assertRaises(BlockingIOError):
                with cloud_update.exclusive_lock(root):
                    self.fail("Concurrent writer acquired lock")

    @skipUnless(os.name == "posix", "Linux source permission integration")
    def test_source_archive_permissions_are_not_inherited_from_windows(self):
        source = self.root / "code"
        source.mkdir(mode=0o777)
        script = source / "worker.py"
        script.write_text("pass")
        source.chmod(0o777)
        script.chmod(0o666)
        cloud_update.harden_source(source)
        self.assertEqual(source.stat().st_mode & 0o777, 0o755)
        self.assertEqual(script.stat().st_mode & 0o777, 0o644)
        script.chmod(0o666)
        (source / "unexpected-link").symlink_to(script)
        with self.assertRaises(ValueError):
            cloud_update.harden_source(source)
        self.assertEqual(script.stat().st_mode & 0o777, 0o666)

    def test_status_counts_only_latest_run(self):
        generation = self.root / "generations" / "run-latest"
        generation.mkdir()
        cloud_update.write_json(self.root / "latest.json", {"generation": generation.name, "status": "running"})
        with closing(sqlite3.connect(generation / "collector.sqlite3")) as db:
            db.executescript("""CREATE TABLE radar_updaterun (id INTEGER);
                INSERT INTO radar_updaterun VALUES (1),(2);
                CREATE TABLE radar_fetchrun (id INTEGER, update_run_id INTEGER, source_id INTEGER, status TEXT, error_message TEXT);
                INSERT INTO radar_fetchrun VALUES (1,1,1,'failed','old failure'),(2,2,1,'success','');
                CREATE TABLE radar_sourceversion (id INTEGER, fetch_run_id INTEGER);
                CREATE TABLE radar_publicationevent (event_type TEXT, reason_codes TEXT, source_version_id INTEGER);""")
        result = cloud_update.inspect_status(self.root)
        self.assertEqual(result["completed_sources"], 1)
        self.assertEqual(result["failures"], [])

    def test_pruning_keeps_successful_backups_despite_many_failures(self):
        for number in range(12):
            generation = self.root / "generations" / f"run-{number:02}"
            generation.mkdir()
            cloud_update.write_json(generation / "attempt.json", {"status": "success" if number < 3 else "failed"})
        cloud_update.prune(self.root)
        self.assertEqual(len(list((self.root / "generations").iterdir())), 4)

    def test_worker_refuses_normal_or_public_settings_before_collection(self):
        with patch("radar.management.commands.run_cloud_collection.run_update") as run:
            with self.assertRaises(CommandError):
                call_command("run_cloud_collection", out="unused", report="unused", trigger="scheduled")
        run.assert_not_called()

    def test_units_keep_private_scope_and_twice_daily_timezone(self):
        content = (Path(__file__).resolve().parents[2] / "scripts/setup_cloud_update.py").read_text()
        for expected in ("12:00:00 Asia/Shanghai", "20:00:00 Asia/Shanghai", "Persistent=true", "KillMode=control-group", "User=radar-collector", "MemoryMax=1280M", "TimeoutStartSec=6900"):
            self.assertIn(expected, content)
        self.assertNotIn("0.0.0.0", content)

    def test_collector_settings_require_existing_explicit_database(self):
        import runpy
        with patch.dict("os.environ", {"RADAR_COLLECTOR_DATABASE": "relative.sqlite3"}):
            from django.core.exceptions import ImproperlyConfigured
            with self.assertRaises(ImproperlyConfigured):
                runpy.run_module("campus_radar.settings_collector")
