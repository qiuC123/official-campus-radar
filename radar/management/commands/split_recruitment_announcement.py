import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from radar.models import RecruitmentAnnouncement
from radar.services.announcements import split_verified_announcement_project


class Command(BaseCommand):
    help = "经人工确认后，将一个多项目公告页面拆成一个独立项目公告身份。"

    def add_arguments(self, parser):
        parser.add_argument("--announcement-id", type=int, required=True)
        parser.add_argument("--project-key", required=True)
        parser.add_argument("--project-title", required=True)
        parser.add_argument("--project-evidence", required=True)

    def handle(self, *args, **options):
        try:
            announcement = RecruitmentAnnouncement.objects.get(
                pk=options["announcement_id"]
            )
            project = split_verified_announcement_project(
                announcement,
                project_key=options["project_key"],
                project_title=options["project_title"],
                project_evidence=options["project_evidence"],
            )
        except RecruitmentAnnouncement.DoesNotExist as error:
            raise CommandError("announcement not found") from error
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error
        self.stdout.write(json.dumps({
            "ok": True,
            "announcement_id": project.pk,
            "project_title": project.title,
            "source_url": project.url,
        }, ensure_ascii=False))
