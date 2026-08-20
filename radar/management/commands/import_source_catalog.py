import csv
import json
from pathlib import Path
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.models import (
    OfficialSource,
    Organization,
    OrganizationAlias,
    SourceAdmissionEvent,
)
from radar.services.normalization import normalize_identity_text


REQUIRED_HEADER = ["organization_name", "company_type", "industry", "official_domain", "source_type", "source_url", "admission_evidence", "adapter_name", "parser_config", "is_active"]
ALLOWED_ADAPTERS = {"html_selector"}


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:
        parser.add_argument("--path", required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        rows = self._validated_rows(Path(options["path"]))
        if options["dry_run"]:
            self.stdout.write(f"validated_rows={len(rows)} dry_run=true")
            return
        with transaction.atomic():
            for row in rows:
                organization = self._resolve_organization(row["organization_name"])
                if organization is None:
                    organization = Organization.objects.create(
                        name=row["organization_name"], company_type=row["company_type"],
                        industry=row["industry"], official_domain=row["official_domain"],
                    )
                source, created = OfficialSource.objects.get_or_create(
                    organization=organization,
                    source_url=row["source_url"],
                    defaults={
                        "source_type": row["source_type"], "admission_evidence": row["admission_evidence"],
                        "adapter_name": row["adapter_name"], "parser_config": row["parser_config"],
                        "is_active": False, "is_verified": False,
                        "admission_state": OfficialSource.AdmissionState.CANDIDATE,
                    },
                )
                if not created and source.admission_state != OfficialSource.AdmissionState.CANDIDATE:
                    raise CommandError("catalog import cannot rewrite an admitted source")
                if created:
                    SourceAdmissionEvent.objects.create(
                        source=source,
                        from_state="",
                        to_state=OfficialSource.AdmissionState.CANDIDATE,
                        actor_label="catalog-import",
                        reason="candidate imported from local catalog",
                        evidence=row["admission_evidence"],
                    )
        self.stdout.write(f"imported_rows={len(rows)}")

    def _validated_rows(self, path: Path) -> list[dict]:
        if not path.is_file():
            raise CommandError(f"catalog file not found: {path}")
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != REQUIRED_HEADER:
                raise CommandError("catalog header does not match the required schema")
            rows = []
            for line_number, row in enumerate(reader, start=2):
                try:
                    parsed_config = json.loads(row["parser_config"])
                except (json.JSONDecodeError, TypeError) as error:
                    raise CommandError(f"line {line_number}: parser_config must be JSON") from error
                if not isinstance(parsed_config, dict):
                    raise CommandError(f"line {line_number}: parser_config must be a JSON object")
                if not row["organization_name"].strip() or not row["industry"].strip() or not row["admission_evidence"].strip():
                    raise CommandError(f"line {line_number}: organization, industry, and admission evidence are required")
                if row["company_type"] not in Organization.CompanyType.values:
                    raise CommandError(f"line {line_number}: unknown company_type")
                if row["source_type"] not in OfficialSource.SourceType.values:
                    raise CommandError(f"line {line_number}: unknown source_type")
                if row["adapter_name"] not in ALLOWED_ADAPTERS:
                    raise CommandError(f"line {line_number}: unknown adapter_name")
                if urlparse(row["source_url"]).scheme != "https":
                    raise CommandError(f"line {line_number}: source_url must use HTTPS")
                active = row["is_active"].strip().lower()
                if active not in {"true", "false"}:
                    raise CommandError(f"line {line_number}: is_active must be true or false")
                rows.append({**row, "parser_config": parsed_config, "is_active": active == "true"})
        return rows

    @staticmethod
    def _resolve_organization(name: str) -> Organization | None:
        normalized = normalize_identity_text(name)
        matches: dict[int, Organization] = {}
        for organization in Organization.objects.all():
            if normalize_identity_text(organization.name) == normalized:
                matches[organization.pk] = organization
            if any(normalize_identity_text(alias) == normalized for alias in organization.aliases):
                matches[organization.pk] = organization
        for alias in OrganizationAlias.objects.filter(
            normalized_alias=normalized
        ).select_related("organization"):
            matches[alias.organization_id] = alias.organization
        if len(matches) > 1:
            raise CommandError(f"organization alias conflict for {name!r}")
        return next(iter(matches.values()), None)
