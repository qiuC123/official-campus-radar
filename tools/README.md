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

For a batch:

```powershell
py -3.13 tools/discover_api.py --targets tools/targets.json --out work/api-discovery.md
```

The targets file can be a JSON list, or an object containing a `targets` list.
Each item is either a URL string or an object whose `wait`, `scroll`, and
`click` values override the command-line defaults:

```json
{
  "targets": [
    "https://careers.example/jobs",
    {
      "url": "https://careers.example/campus",
      "wait": 10,
      "scroll": true,
      "click": ".next-page"
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
up to 2 MiB, ranks arrays that look like job records, infers total/success and
pagination paths, proposes a field map, and samples up to five raw records.
Capture omissions (including oversized, malformed, or unreadable JSON) appear
in the report. Recruitment-discriminator values such as `kindName` and
`RequireWorkYearsName` remain in samples for human review.

Pagination-only observations are collapsed, while materially different query
or body filters remain as separate candidates. Within the shared six-request
budget for an endpoint, one preferred safe variant receives the full five-step
replay ladder: captured headers, removal of signature-like headers, Cookie,
both groups, and finally only `accept`, `content-type`, and the transparent
low-frequency user agent. Other material variants remain visible and are
marked as not replayed. Only a non-empty equivalent result under the minimal
compliant headers is labeled `可接入`.

Query or nested body keys matching signature/credential indicators such as
`sign`, `token`, `payload`, `nonce`, `trace`, or `w-` are reported by path.
Their values are redacted from URLs and configuration drafts, and that request
variant is conservatively marked non-integrable without replay, field removal,
or reverse engineering. Human review must still confirm campus scope and add
the adapter's notice metadata.

Discovery is deliberately low-frequency and non-evasive:

- Each target opens one headless Chromium page once.
- Targets run serially with at least three seconds between them; the tool never
  performs same-domain concurrency.
- Pagination observations are de-duplicated without discarding material filter
  variants; one full five-request ladder stays within the endpoint-wide hard
  limit of six replay requests.
- The tool does not log in, accept credentials, submit forms, bypass CAPTCHA,
  use stealth or proxies, scan paths, brute-force parameters, or reproduce
  frontend signatures. A login wall, CAPTCHA, abnormal status, or empty blocked
  page is reported and skipped.

Run the offline tests without installing or launching a browser:

```powershell
py -3.13 -m pytest tools/tests -v
```
