from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from radar.models import (
    ApplicationLink,
    OfficialSource,
    RecruitmentBatch,
    RecruitmentPosition,
)
from radar.services.admission import source_is_admitted, transition_source


COMPANY = "美的集团"
SOURCE_URL = "https://careers.midea.com/schoolOut/post?type=2"
BATCH_IDENTITY = "phase-02:p17"
SCREENSHOT_HASHES = (
    "0BA2DEC01FE90A3DFAD781ABE8E1BD3DB74D1C644AD6EEE6B1F6EDC594662B99",
    "17D89701F5335911B5722218C84F6B994C23B18E9BE192FA1D7B2F12F3D8AE48",
)


def _is_fully_retired(source: OfficialSource, batch: RecruitmentBatch) -> bool:
    return (
        source.admission_state == OfficialSource.AdmissionState.SUSPENDED
        and not source.is_active
        and batch.status == RecruitmentBatch.Status.EXPIRED
        and not batch.positions.filter(is_current=True).exists()
        and not batch.application_links.filter(is_current=True).exists()
    )


class Command(BaseCommand):
    help = (
        "Retire the closed Midea internship batch using owner-supplied "
        "official-page evidence."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--actor", default="local-owner")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--apply", action="store_true", help="确认写入状态和审计事件。")
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
            batch = RecruitmentBatch.objects.get(
                source=source,
                identity_key=BATCH_IDENTITY,
            )
        except OfficialSource.DoesNotExist as error:
            raise CommandError("Midea internship source is missing") from error
        except OfficialSource.MultipleObjectsReturned as error:
            raise CommandError(
                "expected exactly one Midea internship source"
            ) from error
        except RecruitmentBatch.DoesNotExist as error:
            raise CommandError("Midea internship batch is missing") from error
        except RecruitmentBatch.MultipleObjectsReturned as error:
            raise CommandError(
                "expected exactly one Midea internship batch"
            ) from error

        if _is_fully_retired(source, batch):
            self.stdout.write(
                "already_retired=1 admission_events_appended=0 network_requests=0"
            )
            return
        if not source_is_admitted(source):
            raise CommandError("Midea internship source is not enabled and admitted")
        if batch.status != RecruitmentBatch.Status.ACTIVE:
            raise CommandError("Midea internship batch is not active")
        if batch.target_audience.strip() not in {"实习生", "在校生"}:
            raise CommandError("unexpected Midea internship target audience")

        current_positions = batch.positions.filter(is_current=True).count()
        current_links = batch.application_links.filter(is_current=True).count()
        if not options["apply"]:
            self.stdout.write(
                f"validated=1 would_suspend_source=1 would_expire_batch=1 "
                f"would_retire_positions={current_positions} "
                f"would_retire_links={current_links} network_requests=0 dry_run=true"
            )
            return

        evidence = (
            "Owner-supplied screenshots of the official Midea campus recruitment page "
            "show both internship choices with zero open positions; the page states "
            "现阶段投递已结束; screenshot_sha256="
            + ",".join(SCREENSHOT_HASHES)
            + "; no network request was made by this state transition"
        )
        retired_at = timezone.now()
        try:
            with transaction.atomic():
                transition_source(
                    source,
                    to_state=OfficialSource.AdmissionState.SUSPENDED,
                    actor_label=actor,
                    reason="Midea official page shows internship recruitment closed",
                    evidence=evidence,
                )
                batch = RecruitmentBatch.objects.select_for_update().get(pk=batch.pk)
                batch.status = RecruitmentBatch.Status.EXPIRED
                batch.last_verified_at = retired_at
                batch.save(update_fields=["status", "last_verified_at"])
                retired_positions = RecruitmentPosition.objects.filter(
                    batch=batch,
                    is_current=True,
                ).update(
                    is_current=False,
                    removed_at=retired_at,
                    content_changed_at=retired_at,
                )
                retired_links = ApplicationLink.objects.filter(
                    batch=batch,
                    is_current=True,
                ).update(
                    is_current=False,
                    removed_at=retired_at,
                )
        except ValidationError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            f"suspended_source=1 expired_batch=1 "
            f"retired_positions={retired_positions} retired_links={retired_links} "
            "admission_events_appended=1 network_requests=0"
        )
