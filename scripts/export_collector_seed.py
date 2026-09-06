"""Export business configuration/evidence to a NEW private SQLite, never personal data."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3

TABLES = frozenset("""django_migrations radar_organization radar_organizationalias
radar_officialsource radar_recruitmentannouncement radar_recruitmentpolicy
radar_recruitmentpolicyevent radar_sourceadmissionevent radar_approvedapplicationhost
radar_sourceversion radar_recruitmentbatch radar_announcementfieldevidence
radar_publicationevent radar_recruitmentposition radar_applicationlink radar_evidence""".split())
SECRET_KEY = re.compile(r"(?i)^(authorization|cookie|password|secret|api[-_]?key|access[-_]?token|accesskey.*)$")


def check_config(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if SECRET_KEY.match(key) and item:
                raise ValueError("Credential-like source configuration; export refused")
            check_config(item)
    elif isinstance(value, list):
        for item in value:
            check_config(item)
    elif isinstance(value, str):
        if re.search(r"(?i)([?&](?:token|api_key|apikey|secret|password|access_token)=|https?://[^/\s]+@|BEGIN .*PRIVATE KEY)", value):
            raise ValueError("Credential-like value; export refused")


def export_seed(source, destination):
    source, destination = Path(source).resolve(strict=True), Path(destination)
    if not destination.is_absolute():
        raise ValueError("Absolute destination required")
    destination.open("xb").close()
    counts = {}
    try:
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src, closing(sqlite3.connect(destination)) as dst:
            src.execute("BEGIN")
            schema = src.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY type DESC").fetchall()
            # Empty schemas retain Django compatibility; only the explicit business rows are copied.
            for kind, name, sql in schema:
                if kind == "table":
                    dst.execute(sql)
            for table in sorted(TABLES):
                columns = [row[1] for row in src.execute(f'PRAGMA table_info("{table}")')]
                if not columns:
                    raise ValueError("Missing required business table: " + table)
                rows = src.execute(f'SELECT * FROM "{table}"')
                count = 0
                for raw in rows:
                    row = dict(zip(columns, raw))
                    if table == "radar_officialsource":
                        if row["source_type"] not in {"api", "ats", "website", "announcement"}:
                            raise ValueError("Non-official source; export refused")
                        check_config(json.loads(row["parser_config"]))
                        check_config(row["source_url"])
                        row["last_error"] = ""
                    if table == "radar_recruitmentannouncement" and row["source_kind"] not in {"website", "recruiting_system"}:
                        raise ValueError("Non-official announcement; export refused")
                    if table == "radar_sourceversion":
                        row["fetch_run_id"] = None  # Old execution logs are deliberately not exported.
                    dst.execute(f'INSERT INTO "{table}" VALUES ({",".join("?" for _ in columns)})', tuple(row.values()))
                    count += 1
                counts[table] = count
            for kind, name, sql in schema:
                if kind == "index":
                    dst.execute(sql)
            if dst.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Export has broken business references")
            dst.commit()
            if dst.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("Export integrity check failed")
        destination.chmod(0o600)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    print(json.dumps(export_seed(args.source, args.out), sort_keys=True))
