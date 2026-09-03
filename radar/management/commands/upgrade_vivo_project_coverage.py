import hashlib
import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from radar.collectors.registry import AdapterRegistry
from radar.models import (
    AnnouncementFieldEvidence,
    OfficialSource,
    RecruitmentAnnouncement,
    RecruitmentBatch,
)
from radar.services.admission import source_is_admitted, transition_source
from radar.services.project_partitions import (
    VIVO_PORTAL,
    VIVO_PROJECTS,
    VIVO_PROJECT_URLS,
    partitioned_parser_config,
)


COMPANY = "vivo"
PENDING_ERROR = "project coverage update has not completed"
OBSERVED_COUNTS = {"1": 28, "2": 137, "7": 74, "8": 18}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _config_hash(config: dict) -> str:
    return _sha256(
        json.dumps(
            config,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _admit_project(source: OfficialSource, spec: tuple[str, ...]) -> None:
    project_id, label, identity_key, title, recruitment_type, audience = spec
    url = VIVO_PROJECT_URLS[identity_key]
    observed_count = OBSERVED_COUNTS[project_id]
    fingerprint = _sha256(
        f"{project_id}|{label}|{title}|{url}|{observed_count}"
    )
    announcement, _ = RecruitmentAnnouncement.objects.update_or_create(
        organization=source.organization,
        source_kind=RecruitmentAnnouncement.SourceKind.RECRUITING_SYSTEM,
        identity_key=f"official-project:vivo:announcement:{project_id}",
        defaults={
            "source": source,
            "title": title,
            "url": url,
            "last_verified_at": timezone.now(),
            "identity_evidence": (
                "vivo official recruitment portal project checkbox and the "
                "same-host public position API ClassificationOne field agree"
            ),
            "content_sha256": fingerprint,
            "evidence_sha256": fingerprint,
            "verification_status": (
                RecruitmentAnnouncement.VerificationStatus.VERIFIED
            ),
            "verification_method": (
                RecruitmentAnnouncement.VerificationMethod.BROWSER
            ),
        },
    )
    batch, _ = RecruitmentBatch.objects.update_or_create(
        source=source,
        identity_key=identity_key,
        defaults={
            "organization": source.organization,
            "title": title,
            "official_page_url": url,
            "primary_announcement": announcement,
            "announcement_admission": (
                RecruitmentBatch.AnnouncementAdmission.ADMITTED
            ),
            "recruitment_type": recruitment_type,
            "target_audience": audience,
            "status": RecruitmentBatch.Status.ACTIVE,
        },
    )
    type_excerpt = (
        f"招聘项目为{label}，岗位类别为实习生招聘"
        if recruitment_type == RecruitmentBatch.RecruitmentType.INTERNSHIP
        else f"招聘项目为{label}，岗位类别为校园招聘"
    )
    audience_excerpt = (
        "官方实习招聘项目面向在校生"
        if recruitment_type == RecruitmentBatch.RecruitmentType.INTERNSHIP
        else "当前岗位名称明确标注27届"
    )
    field_evidence = {
        "title": (title, label),
        "recruitment_type": (recruitment_type, type_excerpt),
        "target_audience": (audience, audience_excerpt),
        "availability": (
            RecruitmentBatch.Status.ACTIVE,
            f"官方项目筛选和公开岗位接口当前返回{observed_count}个岗位",
        ),
    }
    for field_name, (parsed_value, excerpt) in field_evidence.items():
        AnnouncementFieldEvidence.objects.get_or_create(
            batch=batch,
            announcement=announcement,
            field_name=field_name,
            locator=f"official-project[vivo:{project_id}]/{field_name}",
            parsed_value=parsed_value,
            defaults={"excerpt": excerpt},
        )


def _project_records_are_current(source: OfficialSource) -> bool:
    identities = {spec[2] for spec in VIVO_PROJECTS}
    batches = RecruitmentBatch.objects.filter(
        source=source,
        identity_key__in=identities,
        announcement_admission=RecruitmentBatch.AnnouncementAdmission.ADMITTED,
        primary_announcement__verification_status=(
            RecruitmentAnnouncement.VerificationStatus.VERIFIED
        ),
    )
    return (
        batches.count() == len(identities)
        and AnnouncementFieldEvidence.objects.filter(
            batch__in=batches,
            field_name__in={
                "title",
                "recruitment_type",
                "target_audience",
                "availability",
            },
        ).count()
        == len(identities) * 4
    )


class Command(BaseCommand):
    help = (
        "Upgrade the admitted vivo source from one campus project to exhaustive "
        "official project coverage."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--actor", default="local-owner")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--apply", action="store_true", help="确认写入配置和证据。")
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
                adapter_name="json_api",
            )
        except OfficialSource.DoesNotExist as error:
            raise CommandError("vivo JSON API source is missing") from error
        except OfficialSource.MultipleObjectsReturned as error:
            raise CommandError(
                "expected exactly one vivo JSON API source"
            ) from error
        if source.admission_state not in {
            OfficialSource.AdmissionState.ENABLED,
            OfficialSource.AdmissionState.SUSPENDED,
        }:
            raise CommandError("vivo source must be enabled or suspended")

        try:
            configured = partitioned_parser_config(
                COMPANY,
                source.adapter_name,
                source.parser_config,
            )
            old_hash = _config_hash(source.parser_config)
            new_hash = _config_hash(configured)
            probe = OfficialSource.objects.get(pk=source.pk)
            probe.source_url = VIVO_PORTAL
            probe.official_entrypoint_url = VIVO_PORTAL
            probe.parser_config = configured
            AdapterRegistry.validate_source_config(probe)
        except (ValueError, ValidationError) as error:
            raise CommandError(
                f"vivo project coverage config is invalid: {error}"
            ) from error

        already_current = (
            source.source_url == VIVO_PORTAL
            and source.official_entrypoint_url == VIVO_PORTAL
            and source.parser_config == configured
            and source_is_admitted(source)
            and _project_records_are_current(source)
        )
        if already_current:
            self.stdout.write(
                "already_current=1 projects=4 admission_events_appended=0 "
                "network_requests=0"
            )
            return
        event_count = (
            3
            if source.admission_state == OfficialSource.AdmissionState.ENABLED
            else 2
        )
        if not options["apply"]:
            self.stdout.write(
                "validated=1 would_upgrade_projects=4 "
                f"would_append_events={event_count} network_requests=0 dry_run=true"
            )
            return

        evidence = (
            "2026-09-03 read-only official portal and same-host API review found "
            "four active recruitment projects with 28/137/74/18 positions for "
            "蓝极星计划/秋季校园招聘/日常实习生/暑期实习生; fetch the unfiltered "
            "inventory once and require mutually exclusive exhaustive partitions; "
            f"old_config_sha256={old_hash}; new_config_sha256={new_hash}; "
            "configuration transition itself made no network request"
        )
        try:
            with transaction.atomic():
                if source.admission_state == OfficialSource.AdmissionState.ENABLED:
                    transition_source(
                        source,
                        to_state=OfficialSource.AdmissionState.SUSPENDED,
                        actor_label=actor,
                        reason="suspend incomplete vivo project scope",
                        evidence=evidence,
                    )
                    source.refresh_from_db()
                source.source_url = VIVO_PORTAL
                source.official_entrypoint_url = VIVO_PORTAL
                source.parser_config = configured
                source.last_etag = ""
                source.last_error = PENDING_ERROR
                source.save(
                    update_fields=[
                        "source_url",
                        "official_entrypoint_url",
                        "parser_config",
                        "last_etag",
                        "last_error",
                    ]
                )
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.VERIFIED,
                    actor_label=actor,
                    reason="verify exhaustive vivo project coverage",
                    evidence=evidence,
                )
                source.refresh_from_db()
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.ENABLED,
                    actor_label=actor,
                    reason="enable exhaustive vivo project source",
                    evidence=evidence,
                )
                source.refresh_from_db()
                for spec in VIVO_PROJECTS:
                    _admit_project(source, spec)
                if not source_is_admitted(source):
                    raise CommandError("upgraded vivo source failed admission recheck")
        except ValidationError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            "upgraded=1 projects=4 reverified=1 enabled=1 "
            f"admission_events_appended={event_count} network_requests=0"
        )
