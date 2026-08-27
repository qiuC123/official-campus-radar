import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.collectors.registry import AdapterRegistry
from radar.models import OfficialSource, RecruitmentBatch, RecruitmentPosition
from radar.services.admission import (
    _validated_admission_chain,
    source_is_admitted,
    transition_source,
)
from tools.build_t4_source_catalog import build_rows
from tools.validate_t4_offline import validate_offline


class Command(BaseCommand):
    help = "Enable the verified T4 source batch without running collection."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--report", required=True)
        parser.add_argument("--actor", default="local-owner")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        report_path = Path(options["report"])
        report = self._validated_report(report_path)
        if report != validate_offline():
            raise CommandError(
                "offline report does not match the current saved evidence and catalog"
            )
        actor = str(options["actor"]).strip()
        if not actor:
            raise CommandError("actor is required")
        if RecruitmentBatch.objects.exists() or RecruitmentPosition.objects.exists():
            raise CommandError(
                "T4 Cycle 03 requires empty recruitment batch and position tables"
            )

        catalog = {row["organization_name"]: row for row in build_rows()}
        report_companies = {result["company"] for result in report["results"]}
        if report_companies != set(catalog):
            raise CommandError("report companies do not match the frozen T4 catalog")

        sources = []
        for company, row in catalog.items():
            try:
                source = OfficialSource.objects.select_related("organization").get(
                    organization__name=company,
                    source_url=row["source_url"],
                )
            except OfficialSource.DoesNotExist as error:
                raise CommandError(f"verified source is missing for {company}") from error
            if source.admission_state != OfficialSource.AdmissionState.VERIFIED:
                raise CommandError(f"source is not verified: {company}")
            if not source.is_verified or source.is_active:
                raise CommandError(f"verified flags are inconsistent: {company}")
            if source.adapter_name != row["adapter_name"]:
                raise CommandError(f"adapter does not match the catalog: {company}")
            if source.parser_config != json.loads(row["parser_config"]):
                raise CommandError(f"parser config does not match the catalog: {company}")
            if _validated_admission_chain(source) is None:
                raise CommandError(f"admission chain is invalid: {company}")
            try:
                AdapterRegistry.validate_source_config(source)
            except ValueError as error:
                raise CommandError(f"invalid adapter config for {company}: {error}") from error
            sources.append(source)

        source_count = len(sources)
        if options["dry_run"]:
            self.stdout.write(
                f"validated={source_count} would_enable={source_count} "
                "would_collect=0 dry_run=true"
            )
            return

        evidence_path = str(report_path.resolve())
        with transaction.atomic():
            for source in sources:
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.ENABLED,
                    actor_label=actor,
                    reason="T4 Cycle 03 source batch explicitly approved for enablement",
                    evidence=(
                        f"user confirmation; {evidence_path}; Cycle 02 offline "
                        "validation passed and no collection was run"
                    ),
                )
                source.refresh_from_db()
                if not source_is_admitted(source):
                    raise CommandError(
                        f"enabled source failed admission recheck: {source.organization.name}"
                    )

        self.stdout.write(
            f"enabled={source_count} admitted={source_count} "
            "network_requests=0 batches=0 positions=0"
        )

    @staticmethod
    def _validated_report(path: Path) -> dict:
        if not path.is_file():
            raise CommandError(f"offline report not found: {path}")
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise CommandError("offline report must be valid JSON") from error
        results = report.get("results")
        if (
            report.get("cycle") != "Phase 02 / T4 Cycle 02"
            or report.get("mode") != "offline saved-sample contract validation"
            or report.get("network_requests_made") != 0
            or report.get("database_writes") is not False
            or report.get("source_count") != 25
            or report.get("passed_count") != 25
            or report.get("failed_count") != 0
            or report.get("passed") is not True
            or not isinstance(results, list)
            or len(results) != 25
            or len({result.get("key") for result in results}) != 25
            or len({result.get("company") for result in results}) != 25
            or not all(result.get("passed") is True for result in results)
        ):
            raise CommandError("offline report is not a complete passing Cycle 02 report")
        return report
