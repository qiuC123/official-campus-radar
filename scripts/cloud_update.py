"""Linux generation-based collection, atomic publication, and bounded local backups."""
import argparse
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import uuid


def harden_source(source):
    """Normalize Windows tar modes before Linux service users can access code."""
    paths = [source, *source.rglob("*")]
    if any(path.is_symlink() for path in paths):
        raise ValueError("Unexpected source symlink; permissions were not changed")
    for path in paths:
        path.chmod(0o755 if path.is_dir() else 0o644)


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def copy_database(source, destination):
    destination.open("xb").close()
    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src, closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)
        if dst.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("Backup integrity failed")
    destination.chmod(0o600)


def validate_generation(generation):
    for name in ("collector.sqlite3", "display.sqlite3"):
        with closing(sqlite3.connect((generation / name).as_uri() + "?mode=ro", uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("Generation integrity failed")
    with closing(sqlite3.connect((generation / "display.sqlite3").as_uri() + "?mode=ro", uri=True)) as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables != {"snapshot_meta", "public_batch"} or db.execute("SELECT count(*) FROM public_batch").fetchone()[0] == 0:
            raise ValueError("Not a non-empty display-only snapshot")


def promote(root, generation):
    if generation.resolve().parent != (root / "generations").resolve():
        raise ValueError("Generation is outside the managed directory")
    validate_generation(generation)
    temporary = root / "current.next"
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(Path("generations") / generation.name, target_is_directory=True)
    os.replace(temporary, root / "current")  # Both databases switch at one commit point.
    descriptor = os.open(root, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@contextmanager
def exclusive_lock(root):
    import fcntl  # Deliberately Linux-only; do not silently run without a lock.
    with (root / "update.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def prune(root, keep=7):
    current = (root / "current").resolve()
    managed = root / "generations"
    generations = sorted((p for p in managed.iterdir() if p.is_dir() and not p.is_symlink()), reverse=True)
    retained_success = retained_failure = 0
    for old in generations:
        if old == current or not old.name.startswith("run-") or not (old / "attempt.json").is_file():
            continue
        status = json.loads((old / "attempt.json").read_text())["status"]
        if status == "success":
            retained_success += 1
            remove = retained_success > keep
        else:
            retained_failure += 1
            remove = retained_failure > 1
        if remove and old.resolve().parent == managed.resolve():
            shutil.rmtree(old)


def run_once(root, source, trigger):
    with exclusive_lock(root):
        generation = root / "generations" / ("run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
        generation.mkdir(mode=0o711)
        generation.chmod(0o711)
        report = {"started_at": timestamp(), "status": "running", "generation": generation.name, "trigger": trigger}
        write_json(generation / "attempt.json", report)
        write_json(root / "latest.json", report)
        try:
            copy_database((root / "current" / "collector.sqlite3").resolve(), generation / "collector.sqlite3")
            env = {key: value for key, value in os.environ.items() if key not in {"EXA_API_KEY", "OPENAI_API_KEY", "DJANGO_SETTINGS_MODULE"}}
            env.update(DJANGO_SETTINGS_MODULE="campus_radar.settings_collector", RADAR_COLLECTOR_DATABASE=str(generation / "collector.sqlite3"), PYTHONUNBUFFERED="1")
            with (generation / "worker.log").open("w", encoding="utf-8") as log:
                process = subprocess.run([sys.executable, str(source / "manage.py"), "run_cloud_collection", "--trigger", trigger,
                                          "--out", str(generation / "display.sqlite3"), "--report", str(generation / "summary.json")],
                                         cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=6600)
            summary_file = generation / "summary.json"
            summary = json.loads(summary_file.read_text()) if summary_file.exists() else {}
            report["summary"] = summary
            if process.returncode or summary.get("status") != "success" or not summary.get("sources_checked") or summary.get("sources_failed") or summary.get("batches_rejected"):
                raise RuntimeError("Collection did not meet complete-success publication gate")
            (generation / "display.sqlite3").chmod(0o640)
            promote(root, generation)
            report["status"] = "success"
        except Exception as exc:
            # No provider body, credentials, or traceback in the status file.
            # If the rename committed but directory fsync failed, do not falsely report rollback.
            committed = (root / "current").resolve() == generation.resolve()
            report.update(status="success" if committed else "failed", error_type=type(exc).__name__)
        report["completed_at"] = timestamp()
        write_json(generation / "attempt.json", report)
        write_json(root / "latest.json", report)
        prune(root)
        return report


def inspect_status(root):
    report = json.loads((root / "latest.json").read_text())
    generation = root / "generations" / report["generation"]
    database = generation / "collector.sqlite3"
    if database.is_file():
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as db:
            report["completed_sources"] = db.execute("SELECT count(*) FROM radar_fetchrun WHERE update_run_id=(SELECT max(id) FROM radar_updaterun)").fetchone()[0]
            report["failures"] = db.execute("SELECT source_id,error_message FROM radar_fetchrun WHERE status='failed' AND update_run_id=(SELECT max(id) FROM radar_updaterun)").fetchall()
            report["rejection_reasons"] = db.execute("SELECT reason_codes FROM radar_publicationevent WHERE event_type='rejected' AND source_version_id IN (SELECT id FROM radar_sourceversion WHERE fetch_run_id IN (SELECT id FROM radar_fetchrun WHERE update_run_id=(SELECT max(id) FROM radar_updaterun)))").fetchall()
    report["current_generation"] = (root / "current").resolve().name
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--trigger", choices=["manual", "scheduled"], default="scheduled")
    parser.add_argument("--restore", help="Exact retained successful generation name")
    parser.add_argument("--status", action="store_true", help="Read latest attempt and current generation; systemd reports interrupted processes")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if args.status:
        print(json.dumps(inspect_status(root)))
    elif args.restore:
        if Path(args.restore).name != args.restore:
            raise SystemExit("An exact generation name is required")
        with exclusive_lock(root):
            target = root / "generations" / args.restore
            attempt = json.loads((target / "attempt.json").read_text())
            if attempt["status"] not in {"success", "seed"}:
                raise SystemExit("Only a successful generation may be restored")
            promote(root, target)
            write_json(root / "restore.json", {"restored_at": timestamp(), "generation": args.restore})
        print("Restored " + args.restore)
    else:
        report = run_once(root, args.source.resolve(strict=True), args.trigger)
        print(json.dumps(report))
        raise SystemExit(0 if report["status"] == "success" else 1)


if __name__ == "__main__":
    main()
