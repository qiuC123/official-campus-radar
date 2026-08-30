import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from radar.models import RecruitmentAnnouncement
from radar.services.announcements import create_announcement_only_batch


class Command(BaseCommand):
    help = "从已核验公告、岗位方向和邮箱/链接创建没有官网岗位列表的批次。"

    def add_arguments(self, parser):
        parser.add_argument("--announcement-id", type=int, required=True)
        parser.add_argument("--input", required=True, help="人工审阅后的 schema-v1 JSON 文件")

    def handle(self, *args, **options):
        try:
            announcement = RecruitmentAnnouncement.objects.get(pk=options["announcement_id"])
            payload = json.loads(Path(options["input"]).read_text(encoding="utf-8"))
            if payload.get("schema_version") != "1":
                raise ValidationError("unsupported input schema")
            raw_evidence = payload["field_evidence"]
            evidence = {
                name: (value["parsed_value"], value["excerpt"], value["locator"])
                for name, value in raw_evidence.items()
            }
            batch = create_announcement_only_batch(
                announcement,
                identity_key=payload["identity_key"],
                field_evidence=evidence,
                directions=payload["directions"],
                application_evidence=payload["application"]["evidence"],
                application_url=payload["application"].get("url", ""),
                application_email=payload["application"].get("email", ""),
                application_miniprogram_name=payload["application"].get("miniprogram_name", ""),
                application_miniprogram_path=payload["application"].get("miniprogram_path", ""),
                application_instructions=payload["application"].get("instructions", ""),
            )
        except RecruitmentAnnouncement.DoesNotExist as error:
            raise CommandError("announcement not found") from error
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValidationError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps({
            "ok": True,
            "batch_id": batch.pk,
            "directions": batch.positions.count(),
            "announcement_admission": batch.announcement_admission,
        }, ensure_ascii=False))
