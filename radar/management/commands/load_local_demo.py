import hashlib
import json
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from radar.collectors.base import FieldEvidenceValue, RecruitmentBatchCandidate, PositionCandidate
from radar.models import (
    ApprovedApplicationHost,
    ApplicationLink,
    ApplicationProgress,
    Evidence,
    FetchRun,
    RecruitmentPosition,
    OfficialSource,
    Organization,
    OrganizationAlias,
    PublicationEvent,
    RecruitmentBatch,
    SourceAdmissionEvent,
    SourceVersion,
    UpdateRun,
)
from radar.services.admission import transition_source
from radar.services.publication import publish_candidates


LOCAL_DEMO_KEY = "phase01-local-demo"


class Command(BaseCommand):
    help = "Load or remove isolated offline demo data from data/local_demo.json."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--remove", action="store_true")

    def handle(self, *args, **options):
        if options["remove"]:
            self._remove()
            self.stdout.write("local_demo_removed=true")
            return
        self._load()
        self.stdout.write("local_demo_loaded=true batches=3 fixture=data/local_demo.json")

    @staticmethod
    def _evidence(raw: str, locator: str, parsed: str | None = None):
        return FieldEvidenceValue(raw, locator, raw if parsed is None else parsed)

    def _candidate(self, row: dict) -> RecruitmentBatchCandidate:
        identity = row["identity_key"]
        city = row["city"]
        official_page_url = f"https://demo.invalid/batches/{identity}"
        return RecruitmentBatchCandidate(
            title=row["title"],
            official_page_url=official_page_url,
            recruitment_type="校园招聘",
            target_audience="本地演示对象",
            published_on=date(2026, 8, 1),
            deadline=date(2026, 12, 31),
            withdrawn=False,
            evidence_excerpt="仅用于本地演示",
            positions=(
                PositionCandidate(
                    title="演示岗位",
                    location_text=city,
                    raw_text=f"演示岗位 {city}",
                    application_url=None,
                    position_key=f"{identity}-position",
                    field_evidence={
                        "position_title": self._evidence("演示岗位", f"#{identity} .position"),
                        "location": self._evidence(city, f"#{identity} .location"),
                    },
                ),
            ),
            identity_key=identity,
            field_evidence={
                "title": self._evidence(row["title"], f"#{identity} h2"),
                "recruitment_type": self._evidence("校园招聘", f"#{identity} .type", "campus_recruitment"),
                "target_audience": self._evidence("本地演示对象", f"#{identity} .audience"),
                "published_on": self._evidence("2026-08-01", f"#{identity} .published"),
                "deadline": self._evidence("2026-12-31", f"#{identity} .deadline"),
                "official_page_url": self._evidence(official_page_url, f"#{identity} a.notice@href"),
            },
            positions_complete=True,
        )

    @transaction.atomic
    def _load(self) -> None:
        self._remove()
        fixture_path = Path(settings.BASE_DIR) / "data" / "local_demo.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        organization = Organization.objects.create(
            name=fixture["organization_name"],
            company_type="internet",
            industry="演示数据",
            official_domain="demo.invalid",
        )
        source = OfficialSource.objects.create(
            organization=organization,
            source_type="website",
            source_url="https://demo.invalid/careers",
            admission_evidence="离线 demo fixture，不代表真实来源准入",
            adapter_name="local_demo_disabled",
            local_demo_key=LOCAL_DEMO_KEY,
        )
        transition_source(
            source,
            to_state="verified",
            actor_label="local-demo-command",
            reason="reserved demo.invalid fixture",
            evidence="data/local_demo.json is local and non-live",
        )
        transition_source(
            source,
            to_state="enabled",
            actor_label="local-demo-command",
            reason="enable only for local formal-list walkthrough",
            evidence="adapter local_demo_disabled cannot access a live source",
        )
        source.refresh_from_db()
        for row in fixture["batches"]:
            candidate = self._candidate(row)
            version = SourceVersion.objects.create(
                source=source,
                canonical_url=source.source_url,
                content_hash=hashlib.sha256(row["identity_key"].encode()).hexdigest(),
                is_applied=True,
                applied_at=timezone.now(),
            )
            result = publish_candidates(source, [candidate], version)[0]
            batch = RecruitmentBatch.objects.get(pk=result.batch_id)
            if row["status"] == "expired":
                batch.status = RecruitmentBatch.Status.EXPIRED
                batch.save(update_fields=["status"])
            elif row["status"] == "withdrawn":
                withdrawal_version = SourceVersion.objects.create(
                    source=source,
                    canonical_url=source.source_url,
                    content_hash=hashlib.sha256(f"{row['identity_key']}-withdrawn".encode()).hexdigest(),
                    is_applied=True,
                    applied_at=timezone.now(),
                )
                publish_candidates(
                    source,
                    [replace(candidate, withdrawn=True, positions=(), field_evidence={})],
                    withdrawal_version,
                )
            if row.get("progress"):
                ApplicationProgress.objects.create(
                    batch=batch, status=row["progress"]
                )
        UpdateRun.objects.create(
            trigger="scheduled",
            scheduled_for_date=timezone.localdate() - timedelta(days=2),
            status="success",
            error_message="local_demo",
            local_demo_key=LOCAL_DEMO_KEY,
        )

    @transaction.atomic
    def _remove(self) -> None:
        sources = OfficialSource.objects.filter(local_demo_key=LOCAL_DEMO_KEY)
        organizations = list(
            Organization.objects.filter(official_sources__in=sources).distinct()
        )
        if not organizations:
            UpdateRun.objects.filter(local_demo_key=LOCAL_DEMO_KEY).delete()
            return
        batches = RecruitmentBatch.objects.filter(organization__in=organizations)
        versions = SourceVersion.objects.filter(source__in=sources)
        batches.update(latest_publication_event=None)
        Evidence.objects.filter(batch__in=batches).delete()
        ApplicationProgress.objects.filter(batch__in=batches).delete()
        ApplicationLink.objects.filter(batch__in=batches).delete()
        RecruitmentPosition.objects.filter(batch__in=batches).delete()
        PublicationEvent.objects.filter(source_version__in=versions).delete()
        batches.delete()
        versions.delete()
        FetchRun.objects.filter(source__in=sources).delete()
        UpdateRun.objects.filter(local_demo_key=LOCAL_DEMO_KEY).delete()
        ApprovedApplicationHost.objects.filter(source__in=sources).delete()
        SourceAdmissionEvent.objects.filter(source__in=sources).delete()
        sources.delete()
        OrganizationAlias.objects.filter(organization__in=organizations).delete()
        Organization.objects.filter(pk__in=[item.pk for item in organizations]).delete()
