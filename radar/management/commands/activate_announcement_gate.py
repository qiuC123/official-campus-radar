import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from radar.services.announcements import activate_announcement_gate


class Command(BaseCommand):
    help = "使用人工确认的最新预演摘要开启公告门控。"

    def add_arguments(self, parser):
        parser.add_argument("--confirm-digest", required=True)
        parser.add_argument("--actor", default="local-owner")

    def handle(self, *args, **options):
        try:
            policy = activate_announcement_gate(
                options["confirm_digest"],
                actor_label=options["actor"],
            )
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error
        self.stdout.write(json.dumps({
            "ok": True,
            "announcement_gate_enforced": policy.announcement_gate_enforced,
            "activated_at": policy.activated_at.isoformat(),
        }, ensure_ascii=False))
