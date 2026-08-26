# Recruitment API discovery tool

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

Offset-style pairs such as `offset`/`limit` or `pageOffset`/`pageSize` are
retained as `pagination_candidates` with an unsupported/manual-review note;
they are not emitted as executable `page_index` pagination. A complete true
`pageIndex`/`pageSize` pair remains executable even when offset metadata also
appears.

Query or nested body keys matching signature/credential indicators such as
`sign`, `token`, `payload`, `nonce`, `trace`, or `w-` are reported by path.
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

Run the offline tests without installing or launching a browser:

```powershell
py -3.13 -m unittest tools.tests.test_discover_api
```
