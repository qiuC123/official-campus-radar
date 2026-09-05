"""Run once as root on the approved ECS, with a display snapshot and PUBLIC SSH key.

No security group changes, no public listeners, no operational database, no collector.
"""

import argparse
import hashlib
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys


UNIT = """[Unit]
Description=Campus Radar SSH-only display preview
After=network.target

[Service]
User=radar-preview
Group=radar-preview
WorkingDirectory=/opt/radar-private-preview/source
EnvironmentFile=/etc/radar-private-preview.env
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=/opt/radar-runtime/venv/bin/gunicorn --bind 127.0.0.1:8765 --workers 1 --threads 2 --timeout 60 --access-logfile - --error-logfile - campus_radar.preview_wsgi:application
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
UMask=0077
MemoryMax=512M

[Install]
WantedBy=multi-user.target
"""


def run(*args):
    subprocess.run(args, check=True, timeout=30)


def main():
    import grp
    import pwd
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--public-key", required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("Root is required to install the isolated service")
    source = Path("/opt/radar-private-preview/source")
    if Path(__file__).resolve().parent.parent != source:
        raise SystemExit("Run only from the dedicated preview source directory")
    snapshot = Path(args.snapshot)
    if hashlib.sha256(snapshot.read_bytes()).hexdigest() != args.sha256.lower():
        raise SystemExit("Snapshot hash mismatch")
    public_key = Path(args.public_key).read_text().strip()
    if not public_key.startswith("ssh-ed25519 ") or "\n" in public_key or len(public_key.split()) != 3:
        raise SystemExit("Expected one generated Ed25519 public key")
    sys.path.insert(0, str(source))
    os.environ["DJANGO_SETTINGS_MODULE"] = "campus_radar.settings"
    import django
    django.setup()
    from radar.services.public_snapshot import read_snapshot
    _, batches = read_snapshot(snapshot)

    # First-install only: never overwrite an existing service, key, or snapshot.
    destinations = (Path("/etc/radar-private-preview.env"), Path("/etc/systemd/system/radar-private-preview.service"),
                    Path("/var/lib/radar-private-preview/display.sqlite3"))
    if any(path.exists() for path in destinations):
        raise SystemExit("Preview already exists; review an explicit update plan")
    ssh_config = Path("/etc/ssh/sshd_config")
    ssh_backup = Path("/etc/ssh/sshd_config.radar-preview-before")
    if ssh_backup.exists():
        raise SystemExit("SSH backup already exists; review previous installation")
    run("sshd", "-t")
    for name in ("radar-preview", "radar-tunnel"):
        try:
            pwd.getpwnam(name)
        except KeyError:
            pass
        else:
            raise SystemExit("Dedicated service user already exists; do not alter it")
    run("useradd", "--system", "--no-create-home", "--shell", "/usr/sbin/nologin", "radar-preview")
    run("useradd", "--system", "--create-home", "--home-dir", "/var/lib/radar-tunnel", "--shell", "/usr/sbin/nologin", "radar-tunnel")
    # Unusable password, but not a locked account that rejects public-key authentication.
    run("usermod", "--password", "*", "radar-tunnel")
    tunnel_user = pwd.getpwnam("radar-tunnel")
    ssh_dir = Path("/var/lib/radar-tunnel/.ssh")
    ssh_dir.mkdir(mode=0o700)
    os.chown(ssh_dir, tunnel_user.pw_uid, tunnel_user.pw_gid)
    keyfile = ssh_dir / "authorized_keys"
    keyfile.write_text('restrict,port-forwarding,permitopen="127.0.0.1:8765",command="/usr/sbin/nologin" ' + public_key + "\n")
    keyfile.chmod(0o600)
    os.chown(keyfile, tunnel_user.pw_uid, tunnel_user.pw_gid)
    run("restorecon", "-R", "/var/lib/radar-tunnel/.ssh")
    shutil.copy2(ssh_config, ssh_backup)
    with ssh_config.open("a") as stream:
        stream.write("\n# Dedicated preview tunnel; no shell or reverse forwarding.\n"
                     "Match User radar-tunnel\n"
                     "    AllowTcpForwarding local\n"
                     "    PermitOpen 127.0.0.1:8765\n"
                     "    PermitListen none\n"
                     "    PasswordAuthentication no\n"
                     "    PermitTTY no\n"
                     "    X11Forwarding no\n"
                     "    AllowAgentForwarding no\n"
                     "    ForceCommand /usr/sbin/nologin\n")
    try:
        run("sshd", "-t")
    except subprocess.CalledProcessError:
        shutil.copy2(ssh_backup, ssh_config)
        raise
    run("systemctl", "reload", "sshd")

    data_dir = destinations[2].parent
    data_dir.mkdir(mode=0o750)
    preview_gid = grp.getgrnam("radar-preview").gr_gid
    os.chown(data_dir, 0, preview_gid)
    shutil.copyfile(snapshot, destinations[2])
    destinations[2].chmod(0o440)
    os.chown(destinations[2], 0, preview_gid)
    descriptor = os.open(destinations[0], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write("DJANGO_SECRET_KEY=" + secrets.token_urlsafe(64) + "\n"
                     "DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost\n"
                     "RADAR_DATABASE_PATH=/var/lib/radar-private-preview/display.sqlite3\n"
                     "RADAR_SSH_PREVIEW=1\n")
    destinations[1].write_text(UNIT)
    destinations[1].chmod(0o644)
    run("systemctl", "daemon-reload")
    run("systemctl", "enable", "--now", "radar-private-preview.service")
    print(f"Installed SSH-only preview with {len(batches)} display batches")


if __name__ == "__main__":
    main()
