"""User-authorized one-shot follow-up using the existing Playwright reader."""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validate_xiaomi_browser_sample import (
    HOST, JOB_PATH, SEEDS, INTERACTION_GUARD_SCRIPT, detect_page_block,
    job_sample, public_url, sample_verdict,
)

PRIOR = ROOT / "work/company-expansion-xiaomi-mcp-browser-20260907.json"
REPORT = ROOT / "work/company-expansion-xiaomi-browser-followup-20260907.json"
JOB_KEY = HOST + JOB_PATH
DEADLINE_SECONDS = 180
NEXT_SELECTOR = 'li.atsx-pagination-next[title="下一页"]'


class FollowupBudget:
    def __init__(self, prior: dict):
        self.before = Counter()
        for call in prior["calls"]:
            self.before.update(call["result"]["endpoint_requests"]["by_endpoint"])
        if sum(self.before.values()) != 50 or self.before[JOB_KEY] != 1:
            raise ValueError("prior_ledger_changed")
        if prior["historical"]["known_job_requests_before"] != 4:
            raise ValueError("historical_job_ledger_changed")
        self.used = self.before.copy()
        self.events = []
        self.blocked = Counter()
        self.stop_reason = None

    def stop(self, reason):
        if self.stop_reason is None:
            self.stop_reason = reason

    def allow(self, method, url, resource_type):
        if self.stop_reason:
            return False
        parsed = urlsplit(url)
        key = parsed.hostname + parsed.path
        if sum(self.used.values()) >= 200 or self.used[key] >= (8 if key == JOB_KEY else 20):
            self.stop("endpoint_budget_exhausted")
            return False
        self.used[key] += 1
        self.events.append({"method": method, "endpoint": key, "resource_type": resource_type,
                            "approved_round_count": self.used[key]})
        return True

    def summary(self):
        return {"prior_approved_round_requests": sum(self.before.values()),
                "new_requests": len(self.events), "approved_round_requests": sum(self.used.values()),
                "approved_round_limit": 200, "new_job_requests": self.used[JOB_KEY] - self.before[JOB_KEY],
                "known_cumulative_job_requests": 4 + self.used[JOB_KEY], "known_cumulative_job_limit": 12,
                "by_endpoint": dict(self.used), "new_request_events": self.events,
                "blocked_before_send": dict(self.blocked)}


def safe_next(metadata):
    return (metadata.get("tag") == "li" and metadata.get("title") == "下一页"
            and "atsx-pagination-next" in metadata.get("classes", [])
            and not any("jump" in value for value in metadata.get("classes", []))
            and metadata.get("visible") and not metadata.get("disabled")
            and not metadata.get("form") and not metadata.get("unsafe_descendants"))


def summarize_evidence(report):
    """Separate an observed page pair from the stopped experiment's acceptance."""
    stages = {}
    for page in report["pages"]:
        samples = page["job_responses"]
        sample = samples[0] if len(samples) == 1 else None
        stages[page["stage"]] = {
            "http_status": page["http_status"],
            "rows": sample["row_count"] if sample else 0,
            "declared_total": sample["declared_total"] if sample else None,
            "ids": sample["ids"] if sample else [],
            "all_titles_visible": bool(sample and sample["rows"] and all(
                row.get("title") and row["title"] in page["visible_text_excerpt"] for row in sample["rows"])),
            "subject_id_counts": dict(Counter(str(row["job_subject"]["id"]) for row in sample["rows"]
                if isinstance(row.get("job_subject"), dict) and row["job_subject"].get("id"))) if sample else {},
        }
    campus = [stages.get(key, {}) for key in ("campus:first", "campus:next")]
    observed = (report["pagination_clicks"] == 1
                and safe_next(report.get("next_control", {}).get("metadata", {}))
                and sample_verdict(report["pages"], None)["two_distinct_campus_pages"]
                and all(page.get("http_status") == 200 and page.get("all_titles_visible") for page in campus))
    return {"stages": stages, "campus_natural_next_observed": bool(observed),
            "captured_unique_jobs": len({job_id for stage in stages.values() for job_id in stage["ids"]}),
            "whole_experiment_complete": report["state"] == "sample_finished",
            "stop_reason": report["stop_reason"], "full_collection_verified": False,
            "project_coverage_verified": False, "application_availability_verified": False,
            "production_admitted": False}


async def experiment(report, budget):
    import psutil
    from playwright.async_api import async_playwright

    process = psutil.Process()
    peak = 0
    async def memory_monitor():
        nonlocal peak
        while True:
            total = 0
            for child in [process, *process.children(recursive=True)]:
                try:
                    total += child.memory_info().rss
                except psutil.Error:
                    pass
            peak = max(peak, total)
            await asyncio.sleep(0.2)

    monitor = asyncio.create_task(memory_monitor())
    cache, tasks = set(), set()
    responses = []
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True, args=["--no-proxy-server"])
            try:
                context = await browser.new_context(ignore_https_errors=False, service_workers="block")
                await context.expose_binding("__officialCampusRadarViolation",
                                             lambda _source, _message: budget.stop("forbidden_interaction"))
                await context.add_init_script(script=INTERACTION_GUARD_SCRIPT)
                page = await context.new_page()
                async def block_popup(popup):
                    budget.stop("popup_blocked")
                    await popup.close()
                context.on("page", block_popup)

                async def route_request(route):
                    request = route.request
                    if budget.stop_reason:
                        await route.abort()
                        return
                    if request.resource_type in {"image", "font", "media"}:
                        budget.blocked[request.resource_type] += 1
                        await route.abort()
                        return
                    try:
                        safe = public_url(request.url, cache)
                    except (ValueError, OSError):
                        safe = False
                    parsed = urlsplit(request.url)
                    if not safe or (request.is_navigation_request() and
                                    (parsed.hostname != HOST or parsed.path not in {f"/{seed}/" for seed in SEEDS})):
                        if request.is_navigation_request():
                            budget.stop("navigation_out_of_scope")
                        budget.blocked["unsafe_url"] += 1
                        await route.abort()
                        return
                    if not budget.allow(request.method, request.url, request.resource_type):
                        await route.abort()
                        return
                    await route.continue_()

                async def record_response(response):
                    if response.status in {401, 403, 412, 429}:
                        budget.stop(f"access_restricted_http_{response.status}")
                    parsed = urlsplit(response.url)
                    if parsed.hostname != HOST or parsed.path != JOB_PATH or response.status != 200:
                        return
                    try:
                        body = await response.body()
                        if len(body) > 2 * 1024 * 1024:
                            raise ValueError("job_response_too_large")
                        sample = job_sample(json.loads(body))
                        sample["body_sha256"] = hashlib.sha256(body).hexdigest()
                        responses.append(sample)
                    except Exception:
                        budget.stop("job_response_unreadable_or_changed")

                def on_response(response):
                    task = asyncio.create_task(record_response(response))
                    tasks.add(task)
                    task.add_done_callback(tasks.discard)

                await context.route("**/*", route_request)
                page.on("response", on_response)

                async def capture(stage, response_start, status):
                    for _ in range(60):
                        if budget.stop_reason:
                            break
                        visible = await page.locator("body").inner_text(timeout=5000)
                        reason = detect_page_block(status, page.url, visible, len(responses))
                        if reason and not reason.startswith("页面无可见内容"):
                            budget.stop("visible_access_block")
                            break
                        if re.search(r"滑块|拖动.{0,10}(?:验证|拼图)|请先登录|登录后.{0,8}(?:查看|浏览)", visible):
                            budget.stop("visible_access_block")
                            break
                        if len(responses) > response_start:
                            break
                        await page.wait_for_timeout(250)
                    if tasks:
                        await asyncio.gather(*list(tasks), return_exceptions=True)
                    # Let the already received JSON render; never click on an uninspected control.
                    if not budget.stop_reason:
                        await page.wait_for_timeout(750)
                    visible = await page.locator("body").inner_text(timeout=5000)
                    if detect_page_block(status, page.url, visible, len(responses)):
                        budget.stop("visible_access_block")
                    samples = responses[response_start:]
                    report["pages"].append({"stage": stage, "url": f"https://{HOST}/{stage.split(':')[0]}/",
                                            "http_status": status, "visible_text_excerpt": visible[:10000],
                                            "job_responses": samples})
                    if len(samples) != 1:
                        budget.stop("expected_one_job_response_per_stage")
                    print(json.dumps({"stage": stage, "job_responses": len(samples),
                                      "counts": [s["row_count"] for s in samples],
                                      "stop_reason": budget.stop_reason}), flush=True)

                for seed in SEEDS:
                    if budget.stop_reason:
                        break
                    start = len(responses)
                    report["navigation_attempts"] += 1
                    navigation = await page.goto(f"https://{HOST}/{seed}/", wait_until="domcontentloaded", timeout=30000)
                    await capture(f"{seed}:first", start, navigation.status if navigation else None)
                    if seed != "campus" or budget.stop_reason:
                        continue
                    first = responses[start]
                    if not first["identity_complete"]:
                        budget.stop("job_identity_missing")
                        break
                    control = page.locator(NEXT_SELECTOR)
                    if await control.count() != 1:
                        budget.stop("unique_next_control_missing")
                        break
                    metadata = await control.evaluate("""e => ({tag:e.tagName.toLowerCase(),
                        title:e.getAttribute('title'), classes:[...e.classList], visible:!!e.getClientRects().length,
                        form:!!e.closest('form'), disabled:!!e.closest('[disabled],[aria-disabled="true"],[class*=disabled]'),
                        unsafe_descendants:!!e.querySelector('form,input,button[type=submit],a[target]:not([target="_self"])')})""")
                    report["next_control"] = {"selector": NEXT_SELECTOR, "metadata": metadata}
                    if not safe_next(metadata):
                        budget.stop("unsafe_or_disabled_next_control")
                        break
                    start = len(responses)
                    report["pagination_clicks"] += 1
                    await control.click(timeout=10000)
                    await capture("campus:next", start, navigation.status if navigation else None)
                    if not sample_verdict(report["pages"], budget.stop_reason)["two_distinct_campus_pages"]:
                        budget.stop("pagination_not_verified")
                await context.close()
            finally:
                await browser.close()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*list(tasks), return_exceptions=True)
        monitor.cancel()
        await asyncio.gather(monitor, return_exceptions=True)
        report["peak_process_tree_rss_mib"] = round(peak / (1024 * 1024), 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live-browser", action="store_true")
    args = parser.parse_args()
    budget = FollowupBudget(json.loads(PRIOR.read_text(encoding="utf-8")))
    plan = {"user_authorization": "尝试一下，不是说一定要mcp", "prior_report": str(PRIOR.relative_to(ROOT)),
            "new_request_limit": 150, "new_job_request_limit": 7, "prior_known_job_requests": 5,
            "logical_page_limit": 4, "navigation_limit": 3, "campus_next_click_limit": 1,
            "deadline_seconds": DEADLINE_SECONDS, "replays": 0, "retries": 0,
            "seed_urls": [f"https://{HOST}/{seed}/" for seed in SEEDS]}
    if not args.allow_live_browser:
        print(json.dumps({"dry_run": True, "plan": plan}, ensure_ascii=True, indent=2))
        return 0
    report = {"schema_version": 1, "plan": plan, "started_at": datetime.now(timezone.utc).isoformat(),
              "state": "started", "pages": [], "navigation_attempts": 0, "pagination_clicks": 0}
    try:
        with REPORT.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=True, indent=2)
    except FileExistsError:
        print("This authorized follow-up already has a record; do not rerun.")
        return 2
    started = time.monotonic()
    try:
        asyncio.run(asyncio.wait_for(experiment(report, budget), DEADLINE_SECONDS))
    except BaseException as error:
        budget.stop("deadline_exceeded" if isinstance(error, TimeoutError) else type(error).__name__)
    report.update({"elapsed_seconds": round(time.monotonic() - started, 2), "budget": budget.summary(),
                   "stop_reason": budget.stop_reason, "state": "stopped" if budget.stop_reason else "sample_finished",
                   "verdict": sample_verdict(report["pages"], budget.stop_reason)})
    REPORT.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "state": report["state"], "stop_reason": budget.stop_reason,
                      "verdict": report["verdict"]}, ensure_ascii=True), flush=True)
    return 1 if budget.stop_reason else 0


if __name__ == "__main__":
    raise SystemExit(main())
