"""One-shot development experiment; never replays API requests or writes the DB."""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import socket
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.discover_api import INTERACTION_GUARD_SCRIPT, detect_page_block

HOST = "xiaomi.jobs.f.mioffice.cn"
JOB_PATH = "/api/v1/search/job/posts"
JOB_ENDPOINT = f"POST https://{HOST}{JOB_PATH}"
SEEDS = ("campus", "newretailing", "internship")
REPORT = ROOT / "work/company-expansion-xiaomi-browser-sample-20260907.json"
DEADLINE_SECONDS = 180


def endpoint(method: str, url: str) -> str:
    parsed = urlsplit(url)
    return f"{method} {parsed.scheme}://{parsed.hostname}{parsed.path}"


class Budget:
    def __init__(self):
        # Handoff R3 observed one natural job-list request; zero signed replays.
        self.used = Counter({JOB_ENDPOINT: 1})
        self.events = []
        self.stop_reason = None

    def stop(self, reason: str):
        if self.stop_reason is None:
            self.stop_reason = reason

    def allow(self, key: str) -> bool:
        if self.stop_reason:
            return False
        if self.used[key] >= 6:
            self.stop("endpoint_budget_exhausted")
            return False
        self.used[key] += 1
        self.events.append({"endpoint": key, "cumulative_count": self.used[key]})
        return True

    def response_status(self, status: int):
        if status in {401, 403, 412, 429}:
            self.stop(f"access_restricted_http_{status}")


def public_url(url: str, cache: set[str]) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    if parsed.hostname not in cache:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
            return False
        cache.add(parsed.hostname)
    return True


def business_value(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value[:300] if isinstance(value, str) else value
    if isinstance(value, list):
        return [business_value(item) for item in value[:30]]
    if isinstance(value, dict):
        return {key: business_value(value[key]) for key in ("id", "name", "code", "parent") if key in value}
    return None


def job_sample(payload: dict) -> dict:
    data = payload.get("data", {})
    rows = data.get("job_post_list")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("job_list_shape_changed")
    allowed = ("id", "title", "job_id", "job_post_id", "job_category", "job_category_id",
               "recruit_type", "job_type", "city_info", "work_location_list", "project_id",
               "project_name", "recruitment_project", "recruitment_type")
    retained = [{key: business_value(row[key]) for key in allowed if key in row} for row in rows]
    ids = [str(row.get("id") or row.get("job_post_id") or "") for row in rows]
    return {"declared_total": data.get("count"), "row_count": len(rows), "ids": ids,
            "identity_complete": bool(rows) and all(ids) and len(ids) == len(set(ids)),
            "row_field_names": sorted({key for row in rows for key in row}), "rows": retained}


def sample_verdict(pages: list[dict], stop_reason: str | None) -> dict:
    by_stage = {page["stage"]: page for page in pages}
    first = by_stage.get("campus:first", {}).get("job_responses", [])
    second = by_stage.get("campus:next", {}).get("job_responses", [])
    two_pages = False
    if len(first) == len(second) == 1:
        a, b = first[0], second[0]
        two_pages = (a["identity_complete"] and b["identity_complete"]
                     and a["declared_total"] == b["declared_total"]
                     and not (set(a["ids"]) & set(b["ids"])))
    return {"two_distinct_campus_pages": bool(two_pages and not stop_reason),
            "full_collection_verified": False, "project_coverage_verified": False,
            "application_availability_verified": False, "production_admitted": False}


async def experiment(report: dict, budget: Budget):
    from playwright.async_api import async_playwright
    try:
        import psutil
    except ImportError:
        psutil = None

    process = psutil.Process() if psutil else None
    peak = 0
    async def memory_monitor():
        nonlocal peak
        while True:
            if process is None:
                return
            total = 0
            for item in [process, *process.children(recursive=True)]:
                try:
                    total += item.memory_info().rss
                except psutil.Error:
                    pass
            peak = max(peak, total)
            await asyncio.sleep(0.2)

    monitor = asyncio.create_task(memory_monitor())
    cache = set()
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True, args=["--no-proxy-server"])
            try:
                for seed in SEEDS:
                    if budget.stop_reason:
                        break
                    context = await browser.new_context(ignore_https_errors=False, service_workers="block")
                    tasks = set()
                    try:
                        await context.expose_binding("__officialCampusRadarViolation",
                                                     lambda _source, _message: budget.stop("forbidden_interaction"))
                        await context.add_init_script(script=INTERACTION_GUARD_SCRIPT)
                        page = await context.new_page()
                        async def block_popup(new_page):
                            budget.stop("popup_blocked")
                            await new_page.close()
                        context.on("page", block_popup)
                        responses = []
                        async def route_request(route):
                            request = route.request
                            if budget.stop_reason:
                                await route.abort()
                                return
                            try:
                                safe = public_url(request.url, cache)
                            except (ValueError, OSError):
                                safe = False
                            parsed = urlsplit(request.url)
                            if not safe or (request.is_navigation_request() and parsed.hostname != HOST):
                                if request.is_navigation_request():
                                    budget.stop("navigation_out_of_scope")
                                await route.abort()
                                return
                            if request.resource_type in {"image", "font", "media"}:
                                await route.abort()
                                return
                            if request.resource_type in {"xhr", "fetch"}:
                                if not budget.allow(endpoint(request.method, request.url)):
                                    await route.abort()
                                    return
                            await route.continue_()

                        async def record_response(response):
                            request = response.request
                            if request.resource_type in {"document", "xhr", "fetch"}:
                                budget.response_status(response.status)
                            if urlsplit(response.url).hostname != HOST or urlsplit(response.url).path != JOB_PATH:
                                return
                            if response.status != 200:
                                return
                            try:
                                body = await response.body()
                                if len(body) > 2 * 1024 * 1024:
                                    raise ValueError("job_response_too_large")
                                captured = job_sample(json.loads(body))
                                captured["body_sha256"] = hashlib.sha256(body).hexdigest()
                                responses.append(captured)
                            except Exception:
                                budget.stop("job_response_unreadable_or_changed")

                        def on_response(response):
                            task = asyncio.create_task(record_response(response))
                            tasks.add(task)
                            task.add_done_callback(tasks.discard)

                        await context.route("**/*", route_request)
                        page.on("response", on_response)
                        navigation = await page.goto(f"https://{HOST}/{seed}/", wait_until="domcontentloaded", timeout=30000)

                        async def capture(stage: str, response_start: int):
                            for _ in range(40):
                                if budget.stop_reason or len(responses) > response_start:
                                    break
                                await page.wait_for_timeout(250)
                            await page.wait_for_timeout(1000)
                            if tasks:
                                await asyncio.gather(*list(tasks), return_exceptions=True)
                            visible = await page.locator("body").inner_text(timeout=5000)
                            reason = detect_page_block(navigation.status if navigation else None, page.url,
                                                       visible, len(responses))
                            if re.search(r"滑块|拖动.{0,10}(?:验证|拼图)|请先登录|登录后.{0,8}(?:查看|浏览)", visible):
                                reason = "challenge_or_login_required"
                            if reason:
                                budget.stop("visible_access_block")
                            controls = await page.locator("a,button,[role=button],li").evaluate_all("""elements => elements.map((e,i) => ({
                                tag:e.tagName.toLowerCase(), text:(e.innerText||'').trim().slice(0,80),
                                title:e.getAttribute('title')||'', aria:e.getAttribute('aria-label')||'',
                                className:typeof e.className==='string'?e.className:'', rel:e.getAttribute('rel')||'',
                                form:!!e.closest('form'), type:e.getAttribute('type')||'',
                                target:e.getAttribute('target')||'', visible:!!e.getClientRects().length,
                                disabled:!!e.closest('[disabled],[aria-disabled="true"],.disabled,[class*=disabled]'), index:i
                            })).filter(e => e.visible && /next|下一页|下页|›|»/i.test([e.text,e.title,e.aria,e.className,e.rel].join(' ')))""")
                            report["pages"].append({"stage": stage, "url": f"https://{HOST}/{seed}/",
                                                    "http_status": navigation.status if navigation else None,
                                                    "visible_text_excerpt": visible[:6000], "next_controls": controls[:10],
                                                    "job_responses": responses[response_start:]})
                            print(json.dumps({"stage": stage, "job_responses": len(responses)-response_start,
                                              "next_control_count": len(controls), "stop_reason": budget.stop_reason}), flush=True)
                            return controls

                        controls = await capture(f"{seed}:first", 0)
                        if seed == "campus" and not budget.stop_reason:
                            safe_controls = [item for item in controls if item["tag"] in {"a", "button"}
                                             and not item["form"] and item["type"] not in {"submit", "image"}
                                             and item["target"] in {"", "_self"} and not item["disabled"]]
                            if len(safe_controls) == 1:
                                response_start = len(responses)
                                await page.wait_for_timeout(1500)
                                await page.locator("a,button,[role=button],li").nth(safe_controls[0]["index"]).click(timeout=10000)
                                await capture("campus:next", response_start)
                            else:
                                report["pagination_note"] = "unique_safe_next_control_not_identified"
                    finally:
                        if tasks:
                            await asyncio.gather(*list(tasks), return_exceptions=True)
                        await context.close()
                    if not budget.stop_reason:
                        await asyncio.sleep(3)
            finally:
                await browser.close()
    finally:
        monitor.cancel()
        await asyncio.gather(monitor, return_exceptions=True)
        report["peak_process_tree_rss_mib"] = round(peak / (1024 * 1024), 1) if process else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live-browser", action="store_true")
    args = parser.parse_args()
    plan = {"seeds": [f"https://{HOST}/{seed}/" for seed in SEEDS], "navigation_limit": 3,
            "campus_next_click_limit": 1, "endpoint_cumulative_limit": 6,
            "job_endpoint_previous_requests": 1, "job_endpoint_new_request_limit": 5,
            "deadline_seconds": DEADLINE_SECONDS, "replays": 0, "retries": 0}
    if not args.allow_live_browser:
        print(json.dumps({"dry_run": True, "plan": plan}, ensure_ascii=True, indent=2))
        return 0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = REPORT.open("x", encoding="utf-8")
    except FileExistsError:
        print("This experiment already has a run record; do not rerun.")
        return 2
    budget = Budget()
    report = {"schema_version": 1, "started_at": datetime.now(timezone.utc).isoformat(),
              "plan": plan, "pages": [], "state": "started"}
    handle.write(json.dumps(report, ensure_ascii=True, indent=2))
    handle.close()
    started = time.monotonic()
    try:
        asyncio.run(asyncio.wait_for(experiment(report, budget), timeout=DEADLINE_SECONDS))
    except BaseException as error:
        budget.stop("deadline_exceeded" if isinstance(error, TimeoutError) else type(error).__name__)
    report.update({"elapsed_seconds": round(time.monotonic()-started, 2),
                   "endpoint_request_events": budget.events, "cumulative_endpoint_counts": dict(budget.used),
                   "stop_reason": budget.stop_reason, "state": "stopped" if budget.stop_reason else "sample_finished",
                   "verdict": sample_verdict(report["pages"], budget.stop_reason)})
    REPORT.write_text(json.dumps(report, ensure_ascii=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "state": report["state"], "stop_reason": budget.stop_reason,
                      "verdict": report["verdict"]}, ensure_ascii=True), flush=True)
    return 1 if budget.stop_reason else 0


if __name__ == "__main__":
    raise SystemExit(main())
