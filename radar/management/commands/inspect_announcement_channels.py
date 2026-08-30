import json

from django.core.management.base import BaseCommand, CommandError

from radar.models import RecruitmentAnnouncement
from radar.services.announcements import observed_application_channel_candidates


class Command(BaseCommand):
    help = "列出公告中观察到的外链、邮箱和二维码载荷候选；只读，不创建投递入口。"

    def add_arguments(self, parser):
        parser.add_argument("--announcement-id", type=int, required=True)

    def handle(self, *args, **options):
        try:
            announcement = RecruitmentAnnouncement.objects.get(
                pk=options["announcement_id"]
            )
        except RecruitmentAnnouncement.DoesNotExist as error:
            raise CommandError("announcement not found") from error
        candidates = observed_application_channel_candidates(announcement)
        self.stdout.write(json.dumps({
            "ok": True,
            "announcement_id": announcement.pk,
            "candidates": candidates,
            "automatic_promotion": False,
        }, ensure_ascii=False, indent=2))
