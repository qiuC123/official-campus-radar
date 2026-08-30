import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from radar.models import AnnouncementDiscoveryCandidate, Organization
from radar.services.announcement_discovery import (
    DiscoveryContractError,
    discover_official_candidates_bulk_with_codex,
    discover_official_candidates_with_codex,
    known_source_candidate_batch,
    parse_official_candidate_batch,
    probe_official_candidates,
    store_official_candidates,
)


class Command(BaseCommand):
    help = "顺序发现官网招聘公告候选；只保存候选，不直接准入。"

    def add_arguments(self, parser):
        parser.add_argument("--organization")
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--input", help="已生成的 OfficialSiteCandidateBatch JSON")
        parser.add_argument("--allow-live-search", action="store_true")
        parser.add_argument("--allow-live-fetch", action="store_true")
        parser.add_argument("--codex-path", default="codex")

    def handle(self, *args, **options):
        if bool(options["organization"]) == bool(options["all"]):
            raise CommandError("provide exactly one of --organization or --all")
        if options["input"] and options["all"]:
            raise CommandError("--input can only be used with one --organization")
        organizations = (
            Organization.objects.order_by("name")
            if options["all"]
            else Organization.objects.filter(name=options["organization"])
        )
        if not organizations.exists():
            raise CommandError("organization not found")
        results = []
        organization_list = list(organizations)
        for organization in organizations:
            try:
                local_options = dict(options)
                if options["all"]:
                    local_options["allow_live_search"] = False
                results.append(self._discover_one(organization, local_options))
            except (DiscoveryContractError, OSError, RuntimeError) as error:
                results.append({
                    "ok": False,
                    "organization": organization.name,
                    "error": type(error).__name__,
                })
        bulk_error = ""
        bulk_search_used = False
        if options["all"] and options["allow_live_search"]:
            needs_search = [
                organization
                for organization, result in zip(organization_list, results)
                if not result.get("raw_signal_candidates")
            ]
            if needs_search:
                try:
                    batches = discover_official_candidates_bulk_with_codex(
                        needs_search,
                        codex_path=options["codex_path"],
                    )
                    bulk_search_used = True
                    by_organization = {item.pk: index for index, item in enumerate(organization_list)}
                    for organization in needs_search:
                        stored = store_official_candidates(
                            organization,
                            batches[organization.pk],
                        )
                        if options["allow_live_fetch"]:
                            stored = probe_official_candidates(organization, stored)
                        results[by_organization[organization.pk]] = {
                            "ok": True,
                            "route": "codex_bulk_search",
                            "organization": organization.name,
                            "candidates_stored": len(stored),
                            "raw_signal_candidates": sum(item.recruitment_signal_found for item in stored),
                            "semantic_review_required": len(stored),
                            "wechat_fallback_needed": None,
                        }
                except (DiscoveryContractError, OSError, RuntimeError) as error:
                    bulk_error = str(error)
        output = (
            {
                "ok": not bulk_error and all(result.get("ok") for result in results),
                "bulk_search_used": bulk_search_used,
                "bulk_error": bulk_error,
                "results": results,
            }
            if options["all"]
            else results[0]
        )
        self.stdout.write(json.dumps(output, ensure_ascii=False))
        if not output.get("ok"):
            raise CommandError("official announcement discovery did not complete successfully")

    def _discover_one(self, organization, options):
        try:
            if options["input"]:
                batch = parse_official_candidate_batch(
                    Path(options["input"]).read_bytes()
                )
                route = "provided_batch"
                stored = store_official_candidates(organization, batch)
            else:
                batch = known_source_candidate_batch(organization)
                route = "known_sources"
                stored = store_official_candidates(organization, batch)
                if options["allow_live_fetch"]:
                    stored = probe_official_candidates(organization, stored)
                qualified = [
                    item for item in stored
                    if item.recruitment_signal_found
                    or item.state == AnnouncementDiscoveryCandidate.State.VERIFIED
                ]
                if not qualified and options["allow_live_search"]:
                    batch = discover_official_candidates_with_codex(
                        organization,
                        codex_path=options["codex_path"],
                    )
                    route = "codex_search"
                    stored = store_official_candidates(organization, batch)
                    if options["allow_live_fetch"]:
                        stored = probe_official_candidates(organization, stored)
        except (DiscoveryContractError, OSError, RuntimeError):
            raise
        return {
            "ok": True,
            "route": route,
            "organization": organization.name,
            "candidates_stored": len(stored),
            "raw_signal_candidates": sum(item.recruitment_signal_found for item in stored),
            "semantic_review_required": len(stored),
            "wechat_fallback_needed": None,
        }
