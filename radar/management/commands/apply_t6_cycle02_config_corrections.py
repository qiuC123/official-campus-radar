import hashlib
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.collectors.registry import AdapterRegistry
from radar.models import OfficialSource
from radar.services.admission import source_is_admitted, transition_source
from tools.t6_cycle02_config_corrections import (
    CORRECTED_COMPANIES,
    corrected_parser_config,
)


def _config_hash(config: dict) -> str:
    payload = json.dumps(
        config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class Command(BaseCommand):
    help = "Apply the three audited parser corrections for T6 Cycle 02."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--actor", default="local-owner")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        actor = str(options["actor"]).strip()
        if not actor:
            raise CommandError("actor is required")
        sources = list(
            OfficialSource.objects.filter(
                organization__name__in=CORRECTED_COMPANIES
            )
            .select_related("organization")
            .order_by("pk")
        )
        if {source.organization.name for source in sources} != set(
            CORRECTED_COMPANIES
        ) or len(sources) != len(CORRECTED_COMPANIES):
            raise CommandError("the three exact T6 Cycle 02 sources are required")

        corrections: list[tuple[OfficialSource, dict, str, str]] = []
        for source in sources:
            if not source_is_admitted(source):
                raise CommandError(
                    f"source is not currently enabled and admitted: {source.organization.name}"
                )
            try:
                corrected = corrected_parser_config(
                    source.organization.name,
                    source.parser_config,
                )
                source.parser_config = corrected
                AdapterRegistry.validate_source_config(source)
            except (ValueError, ValidationError) as error:
                raise CommandError(
                    f"invalid correction for {source.organization.name}: {error}"
                ) from error
            corrections.append(
                (
                    source,
                    corrected,
                    _config_hash(
                        OfficialSource.objects.get(pk=source.pk).parser_config
                    ),
                    _config_hash(corrected),
                )
            )

        if options["dry_run"]:
            self.stdout.write(
                "validated=3 would_suspend=3 would_update=3 "
                "would_reverify=3 would_enable=3 network_requests=0 dry_run=true"
            )
            return

        try:
            with transaction.atomic():
                for source, corrected, old_hash, new_hash in corrections:
                    evidence = (
                        "user confirmed T6 Cycle 02 correction; "
                        f"old_config_sha256={old_hash}; new_config_sha256={new_hash}; "
                        "no network request during configuration transition"
                    )
                    transition_source(
                        source,
                        to_state=OfficialSource.AdmissionState.SUSPENDED,
                        actor_label=actor,
                        reason="T6 Cycle 02 parser correction",
                        evidence=evidence,
                    )
                    source.refresh_from_db()
                    source.parser_config = corrected
                    source.save(update_fields=["parser_config"])
                    transition_source(
                        source,
                        to_state=OfficialSource.AdmissionState.VERIFIED,
                        actor_label=actor,
                        reason="T6 Cycle 02 corrected parser verified",
                        evidence=evidence,
                    )
                    source.refresh_from_db()
                    transition_source(
                        source,
                        to_state=OfficialSource.AdmissionState.ENABLED,
                        actor_label=actor,
                        reason="T6 Cycle 02 corrected parser enabled for scoped retry",
                        evidence=evidence,
                    )
                    source.refresh_from_db()
                    if not source_is_admitted(source):
                        raise CommandError(
                            f"corrected source failed admission recheck: {source.organization.name}"
                        )
        except ValidationError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            "corrected=3 suspended=3 reverified=3 enabled=3 "
            "admission_events_appended=9 network_requests=0"
        )
