import hashlib
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.collectors.registry import AdapterRegistry
from radar.models import OfficialSource
from radar.services.admission import source_is_admitted, transition_source


COMPANY = "美的集团"
SOURCE_URL = "https://careers.midea.com/schoolOut/post?type=2"
PROBE_PENDING_ERROR = "availability probe has not completed"
SCREENSHOT_HASHES = (
    "0BA2DEC01FE90A3DFAD781ABE8E1BD3DB74D1C644AD6EEE6B1F6EDC594662B99",
    "17D89701F5335911B5722218C84F6B994C23B18E9BE192FA1D7B2F12F3D8AE48",
)
AVAILABILITY_PROBE = {
    "mode": "browser_text",
    "url": SOURCE_URL,
    "timeout_seconds": 30,
    "ready_text_any": ["在招岗位", "现阶段投递已结束"],
    "closed_text_any": ["现阶段投递已结束"],
    "open_text_any": [],
    "position_count_pattern": r"在招岗位\s*[（(]\s*(\d+)\s*[）)]",
}


def _config_hash(config: dict) -> str:
    rendered = json.dumps(
        config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def configured_parser_config(config: dict) -> dict:
    configured = json.loads(json.dumps(config))
    if configured.get("batch_partitions"):
        raise ValueError("Midea internship source unexpectedly has batch partitions")
    batch = configured.get("batch")
    if not isinstance(batch, dict) or batch.get("identity_key") != "phase-02:p17":
        raise ValueError("unexpected Midea internship batch config")
    configured["availability_probe"] = AVAILABILITY_PROBE
    return configured


class Command(BaseCommand):
    help = "Configure the generic availability gate for the Midea internship source."

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
                organization__name=COMPANY,
                source_url=SOURCE_URL,
            )
        except OfficialSource.DoesNotExist as error:
            raise CommandError("Midea internship source is missing") from error
        except OfficialSource.MultipleObjectsReturned as error:
            raise CommandError(
                "expected exactly one Midea internship source"
            ) from error
        if source.admission_state not in {
            OfficialSource.AdmissionState.ENABLED,
            OfficialSource.AdmissionState.SUSPENDED,
        }:
            raise CommandError("Midea internship source must be enabled or suspended")

        try:
            already_configured = (
                isinstance(source.parser_config, dict)
                and source.parser_config.get("availability_probe")
                == AVAILABILITY_PROBE
            )
            configured = configured_parser_config(source.parser_config)
            old_hash = _config_hash(source.parser_config)
            new_hash = _config_hash(configured)
            source.parser_config = configured
            AdapterRegistry.validate_source_config(source)
        except (ValueError, ValidationError) as error:
            raise CommandError(f"availability config is invalid: {error}") from error

        already_enabled = (
            source.admission_state == OfficialSource.AdmissionState.ENABLED
        )
        if already_configured and already_enabled:
            self.stdout.write(
                "already_current=1 admission_events_appended=0 network_requests=0"
            )
            return

        event_count = (
            3
            if source.admission_state == OfficialSource.AdmissionState.ENABLED
            else 2
        )
        if not options["apply"]:
            self.stdout.write(
                "validated=1 would_configure_availability_gate=1 "
                f"would_append_events={event_count} network_requests=0 dry_run=true"
            )
            return

        evidence = (
            "Owner-supplied official-page screenshots showed zero open internship "
            "positions while the job API still returned stale rows; configure an "
            "independent browser-text availability gate; screenshot_sha256="
            + ",".join(SCREENSHOT_HASHES)
            + f"; old_config_sha256={old_hash}; new_config_sha256={new_hash}; "
            "configuration transition itself made no network request"
        )
        try:
            with transaction.atomic():
                if source.admission_state == OfficialSource.AdmissionState.ENABLED:
                    transition_source(
                        source,
                        to_state=OfficialSource.AdmissionState.SUSPENDED,
                        actor_label=actor,
                        reason="suspend Midea source before availability-gate change",
                        evidence=evidence,
                    )
                    source.refresh_from_db()
                source.parser_config = configured
                source.last_etag = ""
                source.last_error = PROBE_PENDING_ERROR
                source.save(
                    update_fields=["parser_config", "last_etag", "last_error"]
                )
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.VERIFIED,
                    actor_label=actor,
                    reason="verify Midea independent availability gate",
                    evidence=evidence,
                )
                source.refresh_from_db()
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.ENABLED,
                    actor_label=actor,
                    reason="enable Midea source behind fail-closed availability gate",
                    evidence=evidence,
                )
                source.refresh_from_db()
                if not source_is_admitted(source):
                    raise CommandError(
                        "configured Midea source failed admission recheck"
                    )
        except ValidationError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            "configured=1 availability_gate=browser_text reverified=1 enabled=1 "
            f"admission_events_appended={event_count} network_requests=0"
        )
