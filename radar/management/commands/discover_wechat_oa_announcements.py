import json
import re
from collections import Counter
from datetime import date

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from radar.models import Organization
from radar.services.announcements import import_wechat_oa_announcement
from radar.services.wechat_oa_client import WeChatOAClient, WeChatOAError


_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?key|cookie|authorization|password|secret|token)\s*[:=]"
)


def _parse_date(value: str | None, label: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise CommandError(f"{label} must use YYYY-MM-DD") from error


def _candidate_summary(candidate: dict) -> dict:
    provenance = (
        candidate.get("search_provenance")
        if isinstance(candidate.get("search_provenance"), dict)
        else {}
    )
    hydration_attempt = (
        candidate.get("hydration_attempt")
        if isinstance(candidate.get("hydration_attempt"), dict)
        else {}
    )
    return {
        "fetch_url": candidate.get("fetch_url"),
        "article_identity": candidate.get("article_identity"),
        "title_hint": candidate.get("title_hint"),
        "account_hint": candidate.get("account_hint"),
        "backend_date_hint": candidate.get("backend_date_hint"),
        "verification_status": candidate.get("verification_status"),
        "provider": provenance.get("provider"),
        "rank": provenance.get("rank"),
        "result_id": provenance.get("result_id"),
        "hydration_error_code": hydration_attempt.get("error_code"),
        "has_article_evidence": isinstance(candidate.get("evidence"), dict),
    }


class Command(BaseCommand):
    help = (
        "通过 wechat-oa 0.7 的 Exa Provider 发现并回读微信公众号公告；"
        "默认只预演，--record 才导入数据库。"
    )

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True)
        parser.add_argument("--query", required=True)
        parser.add_argument("--published-after")
        parser.add_argument("--published-before")
        parser.add_argument("--allow-live-search", action="store_true")
        parser.add_argument("--record", action="store_true")
        parser.add_argument("--wechat-oa-path", default="wechat-oa")

    def handle(self, *args, **options):
        if options["record"] and not options["allow_live_search"]:
            raise CommandError("--record requires --allow-live-search")
        query = str(options.get("query") or "").strip()
        if (
            not query
            or len(query) > 500
            or any(ord(character) < 32 or ord(character) == 127 for character in query)
            or _CREDENTIAL_ASSIGNMENT.search(query)
        ):
            raise CommandError("--query contains invalid or credential-like text")
        published_after = _parse_date(options.get("published_after"), "--published-after")
        published_before = _parse_date(options.get("published_before"), "--published-before")
        if published_after and published_before and published_after > published_before:
            raise CommandError("--published-after must not be after --published-before")
        try:
            organization = Organization.objects.get(name=options["organization"])
        except Organization.DoesNotExist as error:
            raise CommandError("organization not found") from error
        identities = [
            item
            for item in (
                organization.wechat_account_identities.filter(
                    is_verified=True,
                    verified_at__isnull=False,
                )
                .exclude(identity_evidence="")
                .order_by("display_name")
            )
            if item.identity_evidence.strip()
        ]
        if not identities:
            raise CommandError("organization has no verified WeChat account identity")

        base = {
            "schema_version": "1",
            "provider": "exa",
            "company": organization.name,
            "query": query,
            "published_after": published_after.isoformat() if published_after else None,
            "published_before": published_before.isoformat() if published_before else None,
            "account_names": [item.display_name for item in identities],
        }
        if not options["allow_live_search"]:
            self.stdout.write(json.dumps({
                **base,
                "ok": True,
                "status": "preview",
                "recorded": False,
                "candidate_count": 0,
                "verified_articles": 0,
                "announcements_imported": 0,
            }, ensure_ascii=False))
            return

        try:
            result = WeChatOAClient(options["wechat_oa_path"]).search_articles_with_exa(
                query=query,
                company=organization.name,
                account_names=tuple(item.display_name for item in identities),
                published_after=published_after,
                published_before=published_before,
            )
            announcements = []
            if options["record"]:
                with transaction.atomic():
                    announcements = [
                        import_wechat_oa_announcement(organization, candidate)
                        for candidate in result.verified_candidates
                    ]
        except WeChatOAError as error:
            self.stdout.write(json.dumps({
                **base,
                "ok": False,
                "status": "failed",
                "recorded": False,
                "error": {
                    "code": error.code,
                    "provider": error.provider or None,
                    "reason": error.reason or None,
                },
            }, ensure_ascii=False))
            raise CommandError(error.code) from error
        except ValidationError as error:
            raise CommandError(str(error)) from error

        candidates = result.data["candidates"]
        statuses = Counter(
            str(item.get("verification_status") or "unknown")
            for item in candidates
        )
        self.stdout.write(json.dumps({
            **base,
            "ok": True,
            "status": "partial" if result.partial else "complete",
            "recorded": bool(options["record"]),
            "candidate_count": len(candidates),
            "verified_articles": len(result.verified_candidates),
            "announcements_imported": len(announcements),
            "verification_statuses": dict(sorted(statuses.items())),
            "candidates": [_candidate_summary(item) for item in candidates],
        }, ensure_ascii=False))
