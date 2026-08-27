import hashlib
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.collectors.registry import AdapterRegistry
from radar.models import OfficialSource
from radar.services.admission import source_is_admitted, transition_source
from tools.t6_cycle05_unicom_browser_config import (
    COMPANY,
    EXPECTED_ADAPTER,
    NEW_ADAPTER,
    browser_parser_config,
)


def _config_hash(config: dict) -> str:
    rendered = json.dumps(
        config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


class Command(BaseCommand):
    help = "Apply the approved China Unicom isolated-browser config for T6 Cycle 05."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--actor", default="local-owner")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        actor = str(options["actor"]).strip()
        if not actor:
            raise CommandError("actor is required")
        try:
            source = OfficialSource.objects.select_related("organization").get(
                organization__name=COMPANY
            )
        except OfficialSource.DoesNotExist as error:
            raise CommandError("China Unicom source is missing") from error
        if not source_is_admitted(source):
            raise CommandError("China Unicom source is not enabled and admitted")
        if source.adapter_name != EXPECTED_ADAPTER:
            raise CommandError("China Unicom adapter baseline is unexpected")

        try:
            corrected = browser_parser_config(source.parser_config)
            old_hash = _config_hash(source.parser_config)
            new_hash = _config_hash(corrected)
            source.adapter_name = NEW_ADAPTER
            source.parser_config = corrected
            AdapterRegistry.validate_source_config(source)
        except (ValueError, ValidationError) as error:
            raise CommandError(f"browser config is invalid: {error}") from error

        if options["dry_run"]:
            self.stdout.write(
                "validated=1 would_change_adapter=1 would_append_events=3 "
                "network_requests=0 dry_run=true"
            )
            return

        evidence = (
            "T6 Cycle 04 confirmed the public China Unicom page paginates correctly "
            "in a clean ephemeral Chromium context without an imported profile, "
            "storage state, Cookie, proxy or login; the owner approved the narrow "
            "production-browser exception on 2026-08-27; "
            f"old_config_sha256={old_hash}; new_config_sha256={new_hash}; "
            "configuration transition itself made no network request"
        )
        try:
            with transaction.atomic():
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.SUSPENDED,
                    actor_label=actor,
                    reason="T6 Cycle 05 isolate China Unicom browser transport",
                    evidence=evidence,
                )
                source.refresh_from_db()
                source.adapter_name = NEW_ADAPTER
                source.parser_config = corrected
                source.save(update_fields=["adapter_name", "parser_config"])
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.VERIFIED,
                    actor_label=actor,
                    reason="T6 Cycle 05 isolated browser contract verified",
                    evidence=evidence,
                )
                source.refresh_from_db()
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.ENABLED,
                    actor_label=actor,
                    reason="T6 Cycle 05 enable approved China Unicom collector",
                    evidence=evidence,
                )
                source.refresh_from_db()
                if not source_is_admitted(source):
                    raise CommandError("China Unicom source failed admission recheck")
        except ValidationError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            "adapter_changed=1 reverified=1 enabled=1 "
            "admission_events_appended=3 network_requests=0"
        )
