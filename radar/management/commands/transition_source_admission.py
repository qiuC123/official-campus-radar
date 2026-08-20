from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from radar.models import OfficialSource
from radar.services.admission import transition_source


class Command(BaseCommand):
    help = "Append one audited local source-admission state transition."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--source-id", required=True, type=int)
        parser.add_argument(
            "--to-state",
            required=True,
            choices=OfficialSource.AdmissionState.values,
        )
        parser.add_argument("--actor", required=True)
        parser.add_argument("--reason", required=True)
        parser.add_argument("--evidence", required=True)

    def handle(self, *args, **options):
        try:
            source = OfficialSource.objects.get(pk=options["source_id"])
        except OfficialSource.DoesNotExist as error:
            raise CommandError("source does not exist") from error
        try:
            event = transition_source(
                source,
                to_state=options["to_state"],
                actor_label=options["actor"],
                reason=options["reason"],
                evidence=options["evidence"],
            )
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error
        self.stdout.write(
            f"source_id={source.pk} event_id={event.pk} "
            f"transition={event.from_state}->{event.to_state}"
        )
