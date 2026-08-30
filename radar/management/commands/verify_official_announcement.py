import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from radar.models import AnnouncementDiscoveryCandidate
from radar.services.announcement_discovery import (
    DiscoveryContractError,
    OfficialSiteCandidate,
    fetch_official_candidate_for_verification,
    snapshot_official_candidate,
)
from radar.services.announcements import verify_official_announcement
from radar.services.announcements import admit_official_domain_announcement_source


class Command(BaseCommand):
    help = "重新读取一个官网候选，经人工提供官方身份依据后生成已核验公告。"

    def add_arguments(self, parser):
        parser.add_argument("--candidate-id", type=int, required=True)
        parser.add_argument("--identity-evidence", required=True)
        parser.add_argument("--actor-label")
        parser.add_argument("--admit-official-domain-source", action="store_true")
        parser.add_argument("--allow-live-fetch", action="store_true")
        parser.add_argument(
            "--allow-browser",
            action="store_true",
            help="显式允许一次隔离无痕浏览器渲染；不读取或保存日常浏览器 Cookie。",
        )
        parser.add_argument(
            "--force-browser",
            action="store_true",
            help="动态页的原始 HTML 虽有通用招聘词，但缺少项目正文时，显式强制隔离浏览器回读。",
        )
        parser.add_argument("--snapshot-file")
        parser.add_argument("--snapshot-title")
        parser.add_argument("--human-confirmed-signal", action="store_true")

    def handle(self, *args, **options):
        if bool(options["allow_live_fetch"]) == bool(options["snapshot_file"]):
            raise CommandError("provide exactly one of --allow-live-fetch or --snapshot-file")
        if options["allow_browser"] and not options["allow_live_fetch"]:
            raise CommandError("--allow-browser requires --allow-live-fetch")
        if options["force_browser"] and not options["allow_browser"]:
            raise CommandError("--force-browser requires --allow-browser")
        try:
            candidate = AnnouncementDiscoveryCandidate.objects.select_related("organization").get(
                pk=options["candidate_id"]
            )
            discovery_candidate = OfficialSiteCandidate(
                url=candidate.url,
                title_hint=candidate.title_hint,
                provider=candidate.provider,
                rank=1,
                result_id=candidate.provider_result_id,
            )
            if options["snapshot_file"]:
                refetched = snapshot_official_candidate(
                    candidate.organization,
                    discovery_candidate,
                    snapshot_bytes=Path(options["snapshot_file"]).read_bytes(),
                    snapshot_title=options["snapshot_title"] or candidate.title_hint,
                    human_confirmed_signal=options["human_confirmed_signal"],
                )
            else:
                refetched = fetch_official_candidate_for_verification(
                    candidate.organization,
                    discovery_candidate,
                    allow_browser=options["allow_browser"],
                    force_browser=options["force_browser"],
                )
            if options["admit_official_domain_source"]:
                if not options["actor_label"]:
                    raise CommandError("--actor-label is required when admitting a source")
                admit_official_domain_announcement_source(
                    candidate.organization,
                    refetched.url,
                    actor_label=options["actor_label"],
                    identity_evidence=options["identity_evidence"],
                )
            announcement = verify_official_announcement(
                candidate,
                refetched,
                identity_evidence=options["identity_evidence"],
            )
        except AnnouncementDiscoveryCandidate.DoesNotExist as error:
            raise CommandError("candidate not found") from error
        except (DiscoveryContractError, ValidationError, OSError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(json.dumps({
            "ok": True,
            "announcement_id": announcement.pk,
            "verification_status": announcement.verification_status,
        }, ensure_ascii=False))
