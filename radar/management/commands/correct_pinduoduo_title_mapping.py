import hashlib
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.collectors.registry import AdapterRegistry
from radar.models import OfficialSource
from radar.services.admission import source_is_admitted, transition_source


COMPANY = "拼多多"
ENDPOINT = "https://careers.pddglobalhr.com/api/careers/api/recruit/position/list"


def _config_hash(config: dict) -> str:
    rendered = json.dumps(
        config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def corrected_parser_config(config: dict) -> dict:
    corrected = json.loads(json.dumps(config))
    if corrected.get("endpoint") != ENDPOINT:
        raise ValueError("unexpected Pinduoduo endpoint")
    field_map = corrected.get("field_map")
    if not isinstance(field_map, dict) or field_map.get("title") not in {"jobName", "name"}:
        raise ValueError("unexpected Pinduoduo title mapping")
    field_map["title"] = "name"
    return corrected


class Command(BaseCommand):
    help = "Correct Pinduoduo position title mapping from category jobName to position name."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--actor", default="local-owner")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--apply", action="store_true", help="确认写入配置和审计事件。")
        mode.add_argument("--dry-run", action="store_true", help="兼容旧调用；现在默认即为预演。")

    def handle(self, *args, **options):
        actor = str(options["actor"]).strip()
        if not actor:
            raise CommandError("actor is required")
        try:
            source = OfficialSource.objects.select_related("organization").get(
                organization__name=COMPANY
            )
        except OfficialSource.DoesNotExist as error:
            raise CommandError("Pinduoduo source is missing") from error
        if not source_is_admitted(source):
            raise CommandError("Pinduoduo source is not enabled and admitted")
        current_field_map = source.parser_config.get("field_map")
        already_correct = (
            isinstance(current_field_map, dict)
            and current_field_map.get("title") == "name"
        )
        try:
            corrected = corrected_parser_config(source.parser_config)
            old_hash = _config_hash(source.parser_config)
            new_hash = _config_hash(corrected)
            source.parser_config = corrected
            AdapterRegistry.validate_source_config(source)
        except (ValueError, ValidationError) as error:
            raise CommandError(f"corrected config is invalid: {error}") from error
        if already_correct:
            self.stdout.write(
                "already_correct=1 title_path=name "
                "admission_events_appended=0 network_requests=0"
            )
            return
        if not options["apply"]:
            self.stdout.write(
                "validated=1 would_change_title_path=jobName->name "
                "would_append_events=3 network_requests=0 dry_run=true"
            )
            return
        evidence = (
            "Official Pinduoduo API response exposes position name in `name` and "
            "category in `jobName`; live read-only sample confirmed graduationYear=2027; "
            f"old_config_sha256={old_hash}; new_config_sha256={new_hash}; "
            "configuration transition itself made no network request"
        )
        try:
            with transaction.atomic():
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.SUSPENDED,
                    actor_label=actor,
                    reason="correct Pinduoduo position title field",
                    evidence=evidence,
                )
                source.refresh_from_db()
                source.parser_config = corrected
                source.save(update_fields=["parser_config"])
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.VERIFIED,
                    actor_label=actor,
                    reason="verify corrected Pinduoduo title field",
                    evidence=evidence,
                )
                source.refresh_from_db()
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.ENABLED,
                    actor_label=actor,
                    reason="enable corrected Pinduoduo source for scoped retry",
                    evidence=evidence,
                )
                source.refresh_from_db()
                if not source_is_admitted(source):
                    raise CommandError("corrected Pinduoduo source failed admission recheck")
        except ValidationError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            "corrected=1 reverified=1 enabled=1 "
            "admission_events_appended=3 network_requests=0"
        )
