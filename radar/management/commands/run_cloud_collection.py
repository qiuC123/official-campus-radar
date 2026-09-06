"""Worker process: it can only change the unpublished working generation."""
from dataclasses import asdict
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.services.public_snapshot import export_snapshot
from radar.services.update_runner import run_update


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--out", required=True)
        parser.add_argument("--report", required=True)
        parser.add_argument("--trigger", choices=["manual", "scheduled"], required=True)

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "campus_radar.settings_collector":
            raise CommandError("Only the dedicated collector settings may run this worker")
        summary = run_update(trigger=options["trigger"])
        result = asdict(summary)
        Path(options["report"]).write_text(json.dumps(result), encoding="utf-8")
        self.stdout.write(json.dumps(result))
        if summary.status != "success" or not summary.sources_checked or summary.sources_failed or summary.batches_rejected:
            raise CommandError("Incomplete collection: display snapshot not published")
        with transaction.atomic():
            export_snapshot(Path(options["out"]))
