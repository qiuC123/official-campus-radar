import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from radar.models import RecruitmentAnnouncement, RecruitmentBatch
from radar.services.announcements import mark_batch_pending_with_announcement


class Command(BaseCommand):
    help = "把已核验公告关联到尚待拆分或补证的招聘批次；该批次不会进入正式页。"

    def add_arguments(self, parser):
        parser.add_argument("--batch-id", type=int, required=True)
        parser.add_argument("--announcement-id", type=int, required=True)

    def handle(self, *args, **options):
        try:
            batch = RecruitmentBatch.objects.get(pk=options["batch_id"])
            announcement = RecruitmentAnnouncement.objects.get(pk=options["announcement_id"])
            mark_batch_pending_with_announcement(batch, announcement)
        except (RecruitmentBatch.DoesNotExist, RecruitmentAnnouncement.DoesNotExist) as error:
            raise CommandError("batch or announcement not found") from error
        except ValidationError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps({
            "ok": True,
            "batch_id": batch.pk,
            "announcement_id": announcement.pk,
            "announcement_admission": "pending",
        }, ensure_ascii=False))
