import json

from django.core.management.base import BaseCommand

from radar.services.announcements import (
    migration_preview_digest,
    migration_preview_payload,
    record_migration_preview,
)


class Command(BaseCommand):
    help = "生成公告门控预演；默认只读，--record 才保存供后续确认的摘要。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--record",
            action="store_true",
            help="保存本次摘要，作为 activate_announcement_gate 的确认前置。",
        )

    def handle(self, *args, **options):
        if options["record"]:
            payload, digest = record_migration_preview()
        else:
            payload = migration_preview_payload()
            digest = migration_preview_digest(payload)
        self.stdout.write(json.dumps({
            "ok": True,
            "recorded": bool(options["record"]),
            "preview_digest": digest,
            **payload,
        }, ensure_ascii=False, indent=2))
