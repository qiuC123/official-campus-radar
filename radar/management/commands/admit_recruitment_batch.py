import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from radar.models import RecruitmentAnnouncement, RecruitmentBatch
from radar.services.announcements import admit_batch_with_announcement


class Command(BaseCommand):
    help = "经人工审阅后，用一个已核验主要公告准入招聘批次。"

    def add_arguments(self, parser):
        parser.add_argument("--batch-id", type=int, required=True)
        parser.add_argument("--announcement-id", type=int, required=True)
        parser.add_argument(
            "--evidence",
            required=True,
            help="JSON 文件；title/recruitment_type/target_audience/availability 各为 parsed_value/excerpt/locator。",
        )

    def handle(self, *args, **options):
        try:
            batch = RecruitmentBatch.objects.get(pk=options["batch_id"])
            announcement = RecruitmentAnnouncement.objects.get(pk=options["announcement_id"])
            raw = json.loads(Path(options["evidence"]).read_text(encoding="utf-8"))
            evidence = {
                name: (value["parsed_value"], value["excerpt"], value["locator"])
                for name, value in raw.items()
            }
            admit_batch_with_announcement(batch, announcement, field_evidence=evidence)
        except (RecruitmentBatch.DoesNotExist, RecruitmentAnnouncement.DoesNotExist) as error:
            raise CommandError("batch or announcement not found") from error
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValidationError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps({
            "ok": True,
            "batch_id": batch.pk,
            "announcement_id": announcement.pk,
            "announcement_admission": "admitted",
        }, ensure_ascii=False))
