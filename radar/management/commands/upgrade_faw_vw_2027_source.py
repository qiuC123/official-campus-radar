import hashlib
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.collectors.registry import AdapterRegistry
from radar.models import OfficialSource
from radar.services.admission import source_is_admitted, transition_source


COMPANY = "一汽-大众汽车有限公司"
ENDPOINT = (
    "https://faw-zhaopin.hotjob.cn/wecruit/positionInfo/listPosition/"
    "SU64bb3226bef57c7e364a7a2c?iSaJAx=isAjax&request_locale=zh_CN"
)
OLD_BATCH_IDENTITY = "phase-02:j02"
NEW_BATCH_IDENTITY = "phase-02:j02:2027-campus"
OLD_AUDIENCE = "2026届"
NEW_AUDIENCE = "2027届"
OLD_ROW_FILTERS = [{"path": "projectName", "equals_any": ["2026校园招聘"]}]
NEW_ROW_FILTERS = [{"path": "projectName", "equals_any": ["2027校园招聘"]}]


def _config_hash(config: dict) -> str:
    rendered = json.dumps(
        config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _source_generation(config: dict) -> str:
    batch = config.get("batch")
    if not isinstance(batch, dict):
        raise ValueError("unexpected FAW-VW batch config")
    state = (
        batch.get("identity_key"),
        batch.get("target_audience"),
        config.get("row_filters"),
    )
    if state == (OLD_BATCH_IDENTITY, OLD_AUDIENCE, OLD_ROW_FILTERS):
        return "2026"
    if state == (NEW_BATCH_IDENTITY, NEW_AUDIENCE, NEW_ROW_FILTERS):
        return "2027"
    raise ValueError("unexpected FAW-VW campaign config")


def upgraded_parser_config(config: dict) -> dict:
    upgraded = json.loads(json.dumps(config))
    if upgraded.get("endpoint") != ENDPOINT:
        raise ValueError("unexpected FAW-VW endpoint")
    generation = _source_generation(upgraded)
    if generation == "2027":
        return upgraded
    upgraded["batch"]["identity_key"] = NEW_BATCH_IDENTITY
    upgraded["batch"]["target_audience"] = NEW_AUDIENCE
    upgraded["row_filters"] = NEW_ROW_FILTERS
    return upgraded


class Command(BaseCommand):
    help = (
        "Upgrade the admitted FAW-VW campus source from the 2026 to 2027 campaign."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--actor", default="local-owner")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--apply", action="store_true", help="确认写入配置和审计事件。")
        mode.add_argument(
            "--dry-run",
            action="store_true",
            help="兼容显式预演；默认即为预演。",
        )

    def handle(self, *args, **options):
        actor = str(options["actor"]).strip()
        if not actor:
            raise CommandError("actor is required")
        try:
            source = OfficialSource.objects.select_related("organization").get(
                organization__name=COMPANY
            )
        except OfficialSource.DoesNotExist as error:
            raise CommandError("FAW-VW source is missing") from error
        except OfficialSource.MultipleObjectsReturned as error:
            raise CommandError("expected exactly one FAW-VW source") from error
        if not source_is_admitted(source):
            raise CommandError("FAW-VW source is not enabled and admitted")

        try:
            generation = _source_generation(source.parser_config)
            upgraded = upgraded_parser_config(source.parser_config)
            old_hash = _config_hash(source.parser_config)
            new_hash = _config_hash(upgraded)
            source.parser_config = upgraded
            AdapterRegistry.validate_source_config(source)
        except (ValueError, ValidationError) as error:
            raise CommandError(f"upgraded config is invalid: {error}") from error

        if generation == "2027":
            self.stdout.write(
                "already_current=1 campaign=2027 admission_events_appended=0 "
                "network_requests=0"
            )
            return
        if not options["apply"]:
            self.stdout.write(
                "validated=1 would_upgrade=2026->2027 would_append_events=3 "
                "network_requests=0 dry_run=true"
            )
            return

        evidence = (
            "2026-09-03 read-only live validation returned 16 unique rows and all "
            "reported projectName=2027校园招聘; the previous filter required "
            "2026校园招聘; the new batch identity preserves the historical 2026 batch; "
            f"old_config_sha256={old_hash}; new_config_sha256={new_hash}; "
            "configuration transition itself made no network request"
        )
        try:
            with transaction.atomic():
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.SUSPENDED,
                    actor_label=actor,
                    reason="suspend stale FAW-VW 2026 campaign config",
                    evidence=evidence,
                )
                source.refresh_from_db()
                source.parser_config = upgraded
                source.last_etag = ""
                source.save(update_fields=["parser_config", "last_etag"])
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.VERIFIED,
                    actor_label=actor,
                    reason="verify FAW-VW 2027 campaign config",
                    evidence=evidence,
                )
                source.refresh_from_db()
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.ENABLED,
                    actor_label=actor,
                    reason="enable FAW-VW 2027 campaign source",
                    evidence=evidence,
                )
                source.refresh_from_db()
                if not source_is_admitted(source):
                    raise CommandError("upgraded FAW-VW source failed admission recheck")
        except ValidationError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            "upgraded=1 campaign=2027 reverified=1 enabled=1 "
            "admission_events_appended=3 network_requests=0"
        )
