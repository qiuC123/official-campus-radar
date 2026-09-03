import hashlib
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.collectors.registry import AdapterRegistry
from radar.models import OfficialSource
from radar.services.admission import source_is_admitted, transition_source
from radar.services.project_partitions import (
    PARTITIONED_COMPANIES,
    SOURCE_CONTRACTS,
    partitioned_parser_config,
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
    help = "为已登记的混合招聘接口配置互斥且完整的招聘批次分组；配置阶段不联网。"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--actor", default="local-owner")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--apply", action="store_true", help="确认写入配置和审计事件。")
        mode.add_argument("--dry-run", action="store_true", help="兼容旧调用；现在默认即为预演。")

    def handle(self, *args, **options):
        actor = str(options["actor"]).strip()
        if not actor:
            raise CommandError("actor is required")
        sources = list(
            OfficialSource.objects.filter(
                organization__name__in=PARTITIONED_COMPANIES,
                adapter_name__in={"json_api", "moka_public_api"},
            ).select_related("organization")
        )
        by_company = {source.organization.name: source for source in sources}
        if (
            set(by_company) != set(PARTITIONED_COMPANIES)
            or len(sources) != len(PARTITIONED_COMPANIES)
        ):
            raise CommandError(
                "the expected partition sources are not uniquely present"
            )
        prepared = []
        for company in PARTITIONED_COMPANIES:
            source = by_company[company]
            if not source_is_admitted(source):
                raise CommandError(f"source is not admitted: {company}")
            try:
                configured = partitioned_parser_config(
                    company,
                    source.adapter_name,
                    source.parser_config,
                )
                probe = OfficialSource.objects.get(pk=source.pk)
                probe.parser_config = configured
                AdapterRegistry.validate_source_config(probe)
            except (ValueError, ValidationError) as error:
                raise CommandError(f"invalid partition config for {company}: {error}") from error
            prepared.append((source, configured))
        changed = [item for item in prepared if item[0].parser_config != item[1]]
        report = {
            "ok": True,
            "dry_run": not bool(options["apply"]),
            "network_requests": 0,
            "sources_checked": len(prepared),
            "sources_changed": len(changed),
            "sources": [
                {
                    "company": source.organization.name,
                    "source_id": source.pk,
                    "partition_count": len(configured["batch_partitions"]),
                    "old_config_sha256": _config_hash(source.parser_config),
                    "new_config_sha256": _config_hash(configured),
                }
                for source, configured in prepared
            ],
        }
        if not options["apply"] or not changed:
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
            return
        with transaction.atomic():
            for source, configured in changed:
                company = source.organization.name
                evidence = (
                    "Read-only live API review confirmed mutually exclusive and "
                    "exhaustive project discriminators; "
                    f"contract={SOURCE_CONTRACTS[company]['base_identity']}; "
                    f"old_config_sha256={_config_hash(source.parser_config)}; "
                    f"new_config_sha256={_config_hash(configured)}; "
                    "configuration change made no network request"
                )
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.SUSPENDED,
                    actor_label=actor,
                    reason="configure recruitment project partitions",
                    evidence=evidence,
                )
                source.refresh_from_db()
                source.parser_config = configured
                source.save(update_fields=["parser_config"])
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.VERIFIED,
                    actor_label=actor,
                    reason="verify recruitment project partitions",
                    evidence=evidence,
                )
                source.refresh_from_db()
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.ENABLED,
                    actor_label=actor,
                    reason="enable partitioned recruitment source",
                    evidence=evidence,
                )
                source.refresh_from_db()
                if not source_is_admitted(source):
                    raise CommandError(f"partitioned source failed admission recheck: {company}")
        report["sources_changed"] = len(changed)
        report["admission_events_appended"] = len(changed) * 3
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
