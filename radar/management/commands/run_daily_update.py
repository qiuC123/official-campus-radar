from django.core.management.base import BaseCommand, CommandError

from radar.services.update_runner import run_update


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:
        parser.add_argument("--trigger", choices=["scheduled", "manual"], required=True)
        parser.add_argument("--source-id", type=int, action="append")

    def handle(self, *args, **options):
        summary = run_update(trigger=options["trigger"], source_ids=options.get("source_id"))
        self.stdout.write(
            f"update_run_id={summary.update_run_id} sources_checked={summary.sources_checked} "
            f"sources_failed={summary.sources_failed} batches_created={summary.batches_created} "
            f"batches_updated={summary.batches_updated} batches_rejected={summary.batches_rejected}"
        )
        if summary.sources_checked == 0 or summary.sources_failed == summary.sources_checked:
            raise CommandError("no active admitted source completed")
