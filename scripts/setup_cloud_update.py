"""First installation on the approved ECS; does not enable the timer or open ports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys

from cloud_update import copy_database, harden_source, promote, timestamp, write_json

ROOT = Path("/var/lib/radar-cloud-update")
SOURCE = Path("/opt/radar-private-preview/source")
SERVICE = """[Unit]
Description=Campus Radar complete official-source collection and atomic snapshot update
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=radar-collector
Group=radar-preview
WorkingDirectory=/opt/radar-private-preview/source
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PLAYWRIGHT_BROWSERS_PATH=/opt/radar-runtime/browsers
Environment=HOME=/var/lib/radar-cloud-update
ExecStart=/opt/radar-runtime/venv/bin/python scripts/cloud_update.py --root /var/lib/radar-cloud-update
TimeoutStartSec=6900
KillMode=control-group
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/radar-cloud-update
UMask=0077
MemoryHigh=768M
MemoryMax=1280M
"""
TIMER = """[Unit]
Description=Campus Radar 12:00 and 20:00 Asia/Shanghai

[Timer]
OnCalendar=*-*-* 12:00:00 Asia/Shanghai
OnCalendar=*-*-* 20:00:00 Asia/Shanghai
Persistent=true
AccuracySec=1min
Unit=radar-cloud-update.service

[Install]
WantedBy=timers.target
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or Path(__file__).resolve().parent.parent != SOURCE:
        raise SystemExit("Run as root in the dedicated ECS deployment")
    harden_source(SOURCE)
    if ROOT.exists() or Path("/etc/systemd/system/radar-cloud-update.service").exists():
        raise SystemExit("Already installed; refusing overwrite")
    if hashlib.sha256(args.seed.read_bytes()).hexdigest() != args.sha256:
        raise SystemExit("Seed hash mismatch")
    try:
        pwd.getpwnam("radar-collector")
    except KeyError:
        subprocess.run(["useradd", "--system", "--no-create-home", "--gid", "radar-preview", "--shell", "/usr/sbin/nologin", "radar-collector"], check=True)
    else:
        raise SystemExit("Collector user already exists")
    user = pwd.getpwnam("radar-collector")
    ROOT.mkdir(mode=0o711)
    (ROOT / "generations").mkdir(mode=0o711)
    seed = ROOT / "generations" / "seed"
    seed.mkdir(mode=0o711)
    copy_database(args.seed.resolve(), seed / "collector.sqlite3")
    display = Path("/var/lib/radar-private-preview/display.sqlite3")
    shutil.copyfile(display, seed / "display.sqlite3")
    (seed / "display.sqlite3").chmod(0o640)
    write_json(seed / "attempt.json", {"status": "seed", "created_at": timestamp()})
    for path in [ROOT, *ROOT.rglob("*")]:
        os.chown(path, user.pw_uid, user.pw_gid)
        if path.is_dir():
            path.chmod(0o711)
        elif path.name != "display.sqlite3":
            path.chmod(0o600)
    promote(ROOT, seed)
    # Preserve original display inode as a root-owned installation rollback copy.
    original = display.with_name("display.before-cloud.sqlite3")
    if original.exists():
        raise SystemExit("Display rollback file already exists")
    os.link(display, original)
    link = display.with_name("display.next")
    link.symlink_to(ROOT / "current" / "display.sqlite3")
    os.replace(link, display)
    for name, content in (("service", SERVICE), ("timer", TIMER)):
        path = Path(f"/etc/systemd/system/radar-cloud-update.{name}")
        path.write_text(content)
        path.chmod(0o644)
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    print(json.dumps({"installed": True, "timer_enabled": False, "root": str(ROOT)}))


if __name__ == "__main__":
    main()
