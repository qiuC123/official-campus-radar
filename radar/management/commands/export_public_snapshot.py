import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from radar.services.public_snapshot import export_snapshot


class Command(BaseCommand):
    help = "Export only admitted display fields; never copy the operational database."

    def add_arguments(self, parser):
        parser.add_argument("--out", required=True)

    def handle(self, *args, **options):
        original = connection.cursor().execute("PRAGMA query_only").fetchone()[0]
        try:
            connection.cursor().execute("PRAGMA query_only=ON")
            with transaction.atomic():
                result = export_snapshot(Path(options["out"]))
            self.stdout.write(json.dumps(result))
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        finally:
            connection.cursor().execute(f"PRAGMA query_only={int(original)}")
