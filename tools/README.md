# Recruitment API discovery tool

## Frozen Xiaomi browser sample — 2026-09-07

`py -3.13 tools/validate_xiaomi_browser_sample.py` prints the frozen plan without
network access. The one authorized live invocation has already completed with
exit code 1; its fixed report is
`work/company-expansion-xiaomi-browser-sample-20260907.json`. Do not delete the
report or rerun this cycle. `--allow-live-browser` requires the report not to
exist and is not permission for a new cycle.

The development-only tool uses fresh Chromium contexts, preserves HTTPS
verification, performs no API replay, reads no request headers or signed query
values, and reserves endpoint request budget before forwarding browser traffic.
It records only a bounded page excerpt and allow-listed job business fields.
The first run consumed three new job-list requests (four including the prior
known request), captured one ten-job sample, and stopped on a telemetry endpoint
budget. It does not certify full collection, application availability or admission.
Optional `psutil` provides local process-tree RSS sampling; absence is reported
as null and does not add a production dependency. See the corresponding handoff
for the one-shot failure, control limitations and remaining budget.

Offline regression checks:

```powershell
py -3.13 -m unittest tools.tests.test_validate_xiaomi_browser_sample -v
```

## General discovery tool

`tools/discover_api.py` is a development-only aid for finding candidate JSON
job-list APIs used by official recruitment pages. It is not part of the
runtime collection path: production collection continues to use `requests`,
and neither `radar/` nor this tool imports the other.

## Install the development dependency

From the repository root on Python 3.13:

```powershell
py -3.13 -m pip install -r requirements-dev.txt
py -3.13 -m playwright install chromium
```

Playwright and Chromium are development-only. They must not be added to
`requirements.txt` or used by the runtime collectors.

## Run discovery

For one target:

```powershell
py -3.13 tools/discover_api.py --url https://careers.example/jobs `
  --wait 8 --scroll --out work/discovery-example.md
```

`--click "<CSS selector>"` may click one visible navigation/filter control.
The tool rejects every control inside a form and links whose explicit or
inherited target could open another page. Guards installed before navigation
also block programmatic form submission, `window.open`, and popups. It never
fills a field or submits a form.

For an acceptance cycle, each target must be invoked exactly once. That
invocation creates one browser context and one page instance, performs one
initial navigation, and never reloads or calls `goto` again. The optional
single safe click may navigate within that same page instance. Do not run a
second diagnostic invocation when a target produces no candidate; record the
cycle as failed instead.

For a batch:

```powershell
py -3.13 tools/discover_api.py --targets tools/targets.json --out work/api-discovery.md
```

The targets file can be a JSON list, or an object containing a `targets` list.
Each item is either a URL string or an object whose `wait`, `scroll`, and
`click` values override the command-line defaults. T3 target files may also
carry `id`, `company`, `company_type`, and `official_evidence_url` so every
visit remains attributable to the frozen company pool:

```json
{
  "targets": [
    "https://careers.example/jobs",
    {
      "url": "https://careers.example/campus",
      "wait": 10,
      "scroll": true,
      "click": ".next-page",
      "id": "P01-01",
      "company": "Example Company",
      "company_type": "Private",
      "official_evidence_url": "https://www.example.com/careers"
    }
  ]
}
```

Without `--out`, the Markdown report is written to standard output. Exit code
`0` means every target produced at least one candidate endpoint; `1` means a
target was blocked, failed, or produced no candidate; `2` means the command,
target file, dependency, or output path was invalid. Expected failures are
reported without a Python traceback.

## What the report means

The tool records request/response metadata, retains JSON response bodies only
up to 2 MiB, ranks arrays that look like job records, displays candidates by
confidence descending (using campus-filter evidence only as a tie-breaker),
infers total/success and pagination paths, proposes a field map, and samples up
to five raw records. Capture omissions (including oversized, malformed, or
unreadable JSON) appear in the report. Recruitment-discriminator values such
as `kindName` and `RequireWorkYearsName` remain in samples for human review.

Pagination-only observations are collapsed, while materially different query
or body filters and every qualifying list path remain as separate candidates.
Within one invocation's shared six-request budget for an endpoint, one
preferred safe request variant receives the full five-step replay ladder:
captured non-credential headers, removal of signature-like headers, Cookie,
both groups, and finally only `accept`, `content-type`, and the transparent
low-frequency user agent. The same five bounded responses are evaluated
independently for every retained list path of that request variant without
additional requests. Other material variants remain visible and are marked as
not replayed. Only a non-empty equivalent result under the minimal compliant
headers is labeled `可接入`.

The ladder stops immediately on HTTP 401, 403, 412, or 429. Remaining
endpoints and later targets for the same company in that invocation are not
requested; other companies can continue. An interrupted ladder cannot qualify
an endpoint. Keep the same company label across that company's target entries.
Across separate invocations, the operator must preserve both the stop decision
and the cumulative endpoint budget.

Offset-style pairs such as `offset`/`limit` or `pageOffset`/`pageSize` are
retained as `pagination_candidates` with an unsupported/manual-review note;
they are not emitted as executable `page_index` pagination. A complete true
`pageIndex`/`pageSize` pair remains executable even when offset metadata also
appears.

Query or nested body keys matching signature/credential indicators such as
`sign`, `token`, `csrf`, `xsrf`, `payload`, `nonce`, `trace`, or `w-` are reported by path.
Their values are redacted from URLs and configuration drafts, and that request
variant is conservatively marked non-integrable without replay, field removal,
or reverse engineering. Human review must still confirm campus scope and add
the adapter's batch metadata, including `official_page_url`.

Captured `Authorization`, `Proxy-Authorization`, and `X-API-Key` headers are
credential-bearing inputs, not replay-ladder signature evidence. Their values
are redacted in retained results, their `header.*` paths are reported, and the
candidate is marked non-integrable without replay. Credential headers are also
removed defensively from every generated header profile, and the requester
refuses them before creating a session. This does not change the anonymous
Cookie baseline or the prescribed signature-header ladder.

Target URLs containing URL userinfo are rejected without echoing the embedded
username or password. If userinfo appears in a captured request URL, it is
removed from retained capture facts, the candidate URL, and configuration; the
candidate is marked non-integrable, and the replay boundary refuses it before
creating a session. Safe and userinfo-bearing observations remain distinct so
deduplication cannot discard the unsafe marker.

## Phase 02 integration boundary

Generated POST drafts place fixed JSON under `body`, and generated success
checks use `success.expect`. The Phase 02 T1 JSON API supplement and this T2
tool are now integrated on `main`. The Cycle 02 acceptance audit parsed the
fresh Ctrip and Tencent drafts, supplemented only the human-owned batch
metadata and a positive delay, and confirmed that both pass the T1 adapter
validator. T2 still intentionally neither changes nor imports `radar/`; the
discovery tool remains separate from production application code.

Discovery is deliberately low-frequency and non-evasive:

- Each target creates one browser context and one headless Chromium page
  instance, performs one initial navigation, and uses zero reloads or second
  `goto` calls. At most one guarded click may continue within that page;
  new-page and popup attempts are blocked.
- Targets run serially with at least three seconds between them; the tool never
  performs same-domain concurrency.
- Pagination observations are de-duplicated without discarding material filter
  variants or qualifying list paths; one full five-request ladder stays within
  the per-invocation endpoint budget of six replay requests. A formal
  acceptance cycle must also keep the same normalized endpoint at or below six
  cumulative replays across all invocations; rerunning a target does not reset
  that audit budget.
- The tool does not log in, accept credentials, submit forms, bypass CAPTCHA,
  use stealth or proxies, scan paths, brute-force parameters, or reproduce
  frontend signatures. A login wall, CAPTCHA, abnormal status, or empty blocked
  page is reported and skipped.

### T3 prospective-cycle interpretation

The historical T2 Cycle 01/02 rule and evidence remain unchanged. Starting
with T3 Cycle 01, the phrase "one visit per target" is a per-target safety
boundary, not a permanent one-page limit for a company. A frozen company may
have more than one target entry only when a distinct official entry page is
needed and the additional visit is recorded with its own target ID and reason.
Targets remain serialized and low-frequency. Re-running a failed target merely
to improve its result is prohibited; a new attempt belongs to a later cycle.

T3 Cycle 02 groups frozen targets by recruitment-platform fingerprints before
selecting representative pages. The machine-readable baseline is
`tools/recruitment-platform-families-cycle-02.json`. A shared family only means
that an adapter strategy may be reusable; tenant configuration, campus scope,
job fields, location fields and pagination still require per-company evidence.
The file does not authorize production browser collection or T4 admission.

The second Cycle 02 stage records offline-only parser drafts in
`tools/recruitment-family-parser-drafts-cycle-02.json`. Validate a saved fixture
without opening a browser or making a request:

```powershell
py -3.13 tools/family_parser_drafts.py `
  --config tools/recruitment-family-parser-drafts-cycle-02.json `
  --family beisen_zhiye `
  --fixture tools/tests/fixtures/family_beisen.html
```

`direct_html` means the observed page can be parsed as returned HTML.
`json_api_candidate` still requires pagination and campus-scope acceptance.
`rendered_dom_dev_only` is evidence from a development browser and is
explicitly blocked from production while runtime browser collection remains
unauthorized.

### T3 Cycle 03 two-page API acceptance

`tools/validate_live_api_cycle03.py` is a narrower read-only validator for the
three frozen targets that already have explicit API evidence. It sends exactly
page 1 and page 2 with minimal headers, no Cookie and no retry, then stores only
allow-listed samples. Its JSON, query and form transports are acceptance-only;
they do not silently add form support to the production adapter.

Run its offline safety tests before the one permitted live invocation:

```powershell
py -3.13 -m unittest tools.tests.test_validate_live_api_cycle03 -v
py -3.13 tools/validate_live_api_cycle03.py
```

Do not run the live command again inside Cycle 03. The report records that the
earlier China Railway Rolling Stock request-body diagnosis already spent three
of that endpoint's six-request budget.

### T3 Cycle 04 family revalidation

Cycle 04 deliberately treats a platform-family label as a hypothesis, not an
integration fact. The six frozen entries live in
`tools/targets-phase-02-t3-cycle-04.json`; four distinct follow-up resources
derived offline from those entries live in the separate follow-up file. Run
the offline tests before either network stage:

```powershell
py -3.13 -m unittest tools.tests.test_validate_family_cycle04 -v
py -3.13 tools/validate_family_cycle04.py
py -3.13 tools/validate_family_cycle04.py --stage followup
```

Both network commands are one-shot Cycle 04 evidence commands and must not be
rerun. Raw HTML/JavaScript stays in the system temporary directory; committed
reports retain only hashes, small position samples, form field names and short
candidate strings. A redirect, timeout, size-limit failure or missing position
list remains a recorded failure instead of triggering a retry.

### T3 Cycle 05 current-architecture XHR discovery

Cycle 05 freezes exactly three current pages in
`tools/targets-phase-02-t3-cycle-05.json`: China Telecom, SAIC Volkswagen and
vivo. The vivo URL was selected from the visible autumn-campus link on its
official recruitment site; no route guessing is allowed. Validate the frozen
budget before the single live invocation:

```powershell
py -3.13 -m unittest tools.tests.test_cycle05_targets tools.tests.test_discover_api -v
py -3.13 tools/discover_api.py `
  --targets tools/targets-phase-02-t3-cycle-05.json `
  --out work/phase-02-t3-discovery-cycle-05.md
```

The live command is one-shot evidence and must not be rerun in Cycle 05. A
minimal-header replay verdict only proves anonymous JSON access. It does not
prove campus scope, title/location fields or pagination, and therefore does not
by itself increase the H3 stable-source count. In particular, website menu
arrays must not be accepted as job arrays even when their object keys happen to
match generic discovery heuristics.

### T3 Cycle 06 Beisen and China Telecom acceptance

Cycle 06 first corrects field evidence: `JobAdId` is identity rather than a
title, `JobAdName` is the title, `LocNames` is an array location, and
`Category` is a recruitment discriminator. Nested object paths are supported.
Discovery reports created after this correction also retain the observed list
length and the actual inferred total value; older reports must not be treated
as if they contained those values.

The vivo acceptance configuration and validator are:

```powershell
py -3.13 -m unittest tools.tests.test_validate_live_beisen_cycle06 -v
py -3.13 tools/validate_live_beisen_cycle06.py
```

They send exactly Beisen pages 0 and 1 with minimal JSON headers and no Cookie.
The live command is one-shot Cycle 06 evidence and must not be rerun. SAIC
Volkswagen is recorded as skipped because its visible official campus section
currently contains zero positions.

The China Telecom target uses one visible, non-form list-item click to trigger
the previously identified position endpoint:

```powershell
py -3.13 -m unittest tools.tests.test_cycle06_telecom_target tools.tests.test_discover_api -v
py -3.13 tools/discover_api.py `
  --targets tools/targets-phase-02-t3-cycle-06-telecom.json `
  --out work/phase-02-t3-discovery-cycle-06-telecom.md
```

This live command is also one-shot. Its historical report was generated before
the row-count enhancement, so the presence of `data.rowCount` does not prove
that the captured `data.details` array was complete.

Run the offline tests without installing or launching a browser:

```powershell
py -3.13 -m unittest tools.tests.test_discover_api
```

### T3 Cycle 07 completeness and next-group evidence

Cycle 07 first sends one empty-body request to the already observed China
Telecom endpoint. The result is 10 rows against `data.rowCount = 2935`, so it
proves the response is incomplete but does not guess an unobserved page field.
The next-group discovery then opens OPPO, Meituan, Amazon China and ICBC once.

Meituan's discovery report records page 1 and spends five of six endpoint
requests on the fixed replay ladder. Its separate validator is allowed only
the sixth request, with the observed nested `page.pageNo = 2` shape. Both live
commands are one-shot evidence and must not be rerun:

```powershell
py -3.13 -m unittest tools.tests.test_validate_telecom_cycle07 -v
py -3.13 tools/validate_telecom_cycle07.py
py -3.13 -m unittest tools.tests.test_cycle07_next_group_targets tools.tests.test_discover_api -v
py -3.13 tools/discover_api.py `
  --targets tools/targets-phase-02-t3-cycle-07-next-group.json `
  --out work/phase-02-t3-discovery-cycle-07-next-group.md
py -3.13 -m unittest tools.tests.test_validate_meituan_cycle07 -v
py -3.13 tools/validate_meituan_cycle07.py
```

The OPPO candidate is not replayed because the captured request contains an
authorization header. Amazon's inferred facet count is not a valid job total,
and ICBC announcement rows are not position rows. These remain recorded
failures rather than integration claims.

### Xiaomi original-browser follow-up (2026-09-07)

`validate_xiaomi_browser_followup.py` is a one-shot development experiment
authorized after the MCP sample stopped. It reuses the original Playwright
reader and job parser, inherits the MCP ledger, and allows only the unspent
150 total requests / 7 job requests, three navigations and one natural next
click within 180 seconds. Every forwarded resource request counts. Images,
fonts and media blocked before sending are recorded separately.

The default command only displays its frozen plan:

```powershell
py -3.13 tools/validate_xiaomi_browser_followup.py
py -3.13 -m unittest tools.tests.test_validate_xiaomi_browser_followup -v
```

The authorized live invocation has already run and its report must not be
deleted or rerun. Read `work/company-expansion-xiaomi-browser-followup-20260907.json`
and the separate `company-expansion-xiaomi-browser-followup-analysis-20260907.json`
in the same directory. `summarize_evidence(report)` deterministically separates
the observed campus next-page pair from whole-experiment acceptance. The
internship stage stopped at the total budget; no production adapter or database
changes are part of this tool.

The same natural-response method is now exposed as `observe_browser_json` in
the separate Web-Crawler-Agent MCP project. See
`docs/handoffs/browser-natural-json-mcp-20260907.md` for the ownership boundary,
scalar field projection contract, frozen offline reference and a zero-budget
protocol-check example. Packaging the reader does not authorize another live
Xiaomi run or replace recruitment admission checks.
