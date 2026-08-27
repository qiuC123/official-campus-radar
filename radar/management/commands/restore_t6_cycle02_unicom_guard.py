import copy
import hashlib
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.collectors.registry import AdapterRegistry
from radar.models import OfficialSource
from radar.services.admission import source_is_admitted, transition_source


COMPANY = "中国联合网络通信集团有限公司"
SUCCESS_GUARD = {"path": "code", "expect": 200}


def _config_hash(config: dict) -> str:
    rendered = json.dumps(
        config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


class Command(BaseCommand):
    help = "Restore the China Unicom business-success guard after live diagnosis."

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
        if "success" in source.parser_config:
            raise CommandError("China Unicom success guard is already configured")

        corrected = copy.deepcopy(source.parser_config)
        corrected["success"] = SUCCESS_GUARD
        old_hash = _config_hash(source.parser_config)
        new_hash = _config_hash(corrected)
        source.parser_config = corrected
        try:
            AdapterRegistry.validate_source_config(source)
        except ValueError as error:
            raise CommandError(f"restored config is invalid: {error}") from error

        if options["dry_run"]:
            self.stdout.write(
                "validated=1 would_restore_guard=1 would_append_events=3 "
                "network_requests=0 dry_run=true"
            )
            return

        evidence = (
            "T6 Cycle 02 live diagnosis returned HTTP 200 with business code=500 "
            "and message=服务器出错 for the documented minimal request; "
            f"old_config_sha256={old_hash}; new_config_sha256={new_hash}; "
            "guard restoration itself made no network request"
        )
        try:
            with transaction.atomic():
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.SUSPENDED,
                    actor_label=actor,
                    reason="restore valid China Unicom business-success guard",
                    evidence=evidence,
                )
                source.refresh_from_db()
                source.parser_config = corrected
                source.save(update_fields=["parser_config"])
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.VERIFIED,
                    actor_label=actor,
                    reason="reverify restored China Unicom guard",
                    evidence=evidence,
                )
                source.refresh_from_db()
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.ENABLED,
                    actor_label=actor,
                    reason="re-enable China Unicom with restored guard",
                    evidence=evidence,
                )
                source.refresh_from_db()
                if not source_is_admitted(source):
                    raise CommandError("restored China Unicom source failed admission recheck")
        except ValidationError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            "guard_restored=1 reverified=1 enabled=1 "
            "admission_events_appended=3 network_requests=0"
        )
