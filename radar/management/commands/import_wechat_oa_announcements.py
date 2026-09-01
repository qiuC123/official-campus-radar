import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from radar.models import Organization
from radar.services.announcements import import_wechat_oa_announcement
from radar.services.wechat_oa_client import (
    WeChatOAClient,
    WeChatOAError,
    validate_wechat_candidate_batch,
)


class Command(BaseCommand):
    help = "将 wechat-oa Candidate Batch 回读为微信证据并导入公告；不会自动创建正式批次。"

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True)
        parser.add_argument("--input", required=True)
        parser.add_argument("--wechat-oa-path", default="wechat-oa")
        parser.add_argument(
            "--allow-browser",
            action="store_true",
            help="显式授权 wechat-oa 打开其独立可见 Chrome；Candidate Batch 本身不能授权。",
        )

    def handle(self, *args, **options):
        try:
            organization = Organization.objects.get(name=options["organization"])
            payload = validate_wechat_candidate_batch(
                json.loads(Path(options["input"]).read_text(encoding="utf-8"))
            )
            result = WeChatOAClient(options["wechat_oa_path"]).hydrate_candidate_batch(
                payload,
                allow_browser=options["allow_browser"],
            )
            announcements = [
                import_wechat_oa_announcement(organization, candidate)
                for candidate in result.verified_candidates
            ]
        except Organization.DoesNotExist as error:
            raise CommandError("organization not found") from error
        except (OSError, json.JSONDecodeError, WeChatOAError, ValidationError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps({
            "ok": True,
            "verified_articles": len(result.verified_candidates),
            "announcements_imported": len(announcements),
            "partial": result.partial,
        }, ensure_ascii=False))
