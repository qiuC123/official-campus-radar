# Phase 02-02 recruitment API discovery — implementation and live evidence report

Generated on 2026-08-21 (Asia/Shanghai).

Status: **OFFLINE_IMPLEMENTATION_COMPLETE / LIVE_ACCEPTANCE_FAILED**. The tool
and offline tests are complete, and the recorded runs establish useful endpoint
facts. The Ctrip live work does not pass the task's compliance acceptance: one
target was opened five times despite the hard one-page-open limit, and the same
normalized `POST getEmployeeStory` endpoint received 10 cumulative replays
despite the hard limit of six. Tencent's blank recruitment filter and
experienced-role samples also require human review before campus scope is
claimed.

## Recorded implementation and live interactions

- The original Ctrip and Tencent commands ran strictly sequentially. After the
  Ctrip endpoint was absent, work paused until the controller completed three
  low-frequency, read-only diagnostic page opens and authorized one exact CTA
  continuation. That authorization explains the sequence but does not waive
  the task's hard access limits.
- The continuation opened one page, used the required wait/scroll sequence,
  and clicked only the controller-approved, non-form, same-page
  `查看所有职位` CTA through the tool's guarded `--click` path.
- No login, form interaction, credential entry, CAPTCHA bypass, stealth,
  environment proxy, signature reconstruction, path scan, parameter guessing,
  or brute force was used.
- No endpoint was called manually. Replays came only from the tool's fixed
  five-request ladder. The tool enforces `5 / 6` per normalized
  method/endpoint within one discovery invocation, but it does not persist a
  budget across invocations. Consequently, `POST getEmployeeStory` was
  replayed five times in the original Ctrip run and five more in the final CTA
  run: 10 cumulatively, exceeding a cross-invocation reading of the hard limit
  of six.
- The initial missing endpoint was not converted into a guessed request. The
  original prescribed Ctrip command produced an incomplete report because the
  current site gates the job endpoint behind a CTA. The later diagnostics and
  continuation found the endpoint, but exceeded the one-page-open hard limit.

## Runtime

- Interpreter: Python 3.13.14 at
  `C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe`.
- Playwright Python package: 1.62.0.
- Controller-validated browser runtime: Chromium/headless shell v1234,
  browser version 151.0.7922.34.
- Discovery code baseline before the original runs:
  `b4a3b5d03b181c90f059a7e3613ba416da541c11`; report baseline before the CTA
  continuation: `3cf14951ad84c7744a63925b595be133ea5144b1`.

## Commands and ordering

1. Ctrip:

   ```powershell
   C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe tools/discover_api.py --url https://careers.ctrip.com/ --wait 10 --scroll --out work/discovery-ctrip.md
   ```

   Exit code 0 after 23.4 seconds. Output:
   `report: work\discovery-ctrip.md`. The generated report was inspected before
   command 2.

2. Tencent:

   ```powershell
   C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe tools/discover_api.py --url https://careers.tencent.com/search.html --wait 10 --scroll --out work/discovery-tencent.md
   ```

   Exit code 0 after 23.5 seconds. Output:
   `report: work\discovery-tencent.md`.

3. Controller root-cause diagnostics, performed before this continuation:

   - One page at `https://careers.ctrip.com/#/campus`, wait 10, no scroll:
     campus route/content visible; `getJobAd` absent.
   - One page at the same route with three bounded scrolls: `getJobAd` absent.
   - One page at the same route for read-only DOM inventory: the campus page
     exposed a non-form, same-page CTA with text `查看所有职位`; no click occurred.

   These three page opens made no replay or direct endpoint requests. They
   isolated the external-site root cause: job loading is gated behind the CTA,
   not route entry or lazy scrolling.

4. Recorded CTA continuation (controller-authorized, but outside the hard
   page-open limit):

   ```powershell
   C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe tools/discover_api.py --url https://careers.ctrip.com/#/campus --wait 10 --scroll --click "text=查看所有职位" --out work/discovery-ctrip.md
   ```

   Exit code 0 after 42.7 seconds. Output:
   `report: work\discovery-ctrip.md`. This was the only continuation page open;
   the report was inspected in full and no further live access occurred.

## Ctrip evidence outcome — live acceptance failed

- The prescribed root-page command first ended at `https://careers.ctrip.com/#/`
  and captured only `getEmployeeStory`. The controller diagnostics established
  that route entry and scrolling do not load jobs; the explicit CTA does.
- Final entry page: `https://careers.ctrip.com/#/campus`; final page:
  `https://careers.ctrip.com/#/campus/jobList`; page status 200 with no login
  wall, CAPTCHA, or HTTP block.
- The guarded CTA run captured three candidate endpoints: `listActiveNews`,
  `getJobAd`, and `getEmployeeStory`. Each received exactly five replays within
  that invocation's endpoint-local `5 / 6` budget. Because `getEmployeeStory`
  had also received five replays in the original run, its cumulative total was
  10.

Observed endpoint facts (not a compliance acceptance):

| Fact | Live observation | Result |
| --- | --- | :---: |
| `POST /api/hrrecruit/getJobAd` captured | Exact endpoint observed | Yes |
| List path `retValue.recruitJobAdList` | Exact path inferred | Yes |
| Total path `retValue.total` | Exact path inferred | Yes |
| Success `retCode="201"` | Exact condition inferred | Yes |
| Body contains `condition`, `pager`, and `head` | All three retained; `category=2`, page 1, size 10 | Yes |
| Minimal headers equivalent; signature unnecessary | All five levels HTTP 200/equivalent | Yes |
| Raw campus discriminator `kindName` retained | `kindName="应届校招生"` in the sample | Yes |

The captured job shape was inferred and rendered correctly. Those facts do not
make the live run compliant: the original prescribed command was incomplete
under the site's current CTA gate, and obtaining the later evidence required
page opens and cumulative replays beyond the task's hard limits. No additional
live run is permitted or needed for this report correction.

## Tencent outcome

- Entry/final page: `https://careers.tencent.com/search.html`.
- Page status: 200; no login wall, CAPTCHA, or HTTP block was reported.
- Endpoint: `GET
  https://careers.tencent.com/tencentcareer/api/post/Query`.
- Captured query summary: `pageIndex=1`, `pageSize=10`, `language=zh-cn`,
  `area=cn`; country/city/business-group/product/category/attribute/keyword
  filters were blank. The report retains the captured timestamp and complete
  observed parameter draft.
- List path: `Data.Posts`.
- Total path: `Data.Count`.
- Success condition: `Code=200`.
- All five replay levels returned HTTP 200 with an equivalent non-empty
  `Data.Posts` list. The minimal compliant headers succeeded, so a signature
  header was unnecessary for this observed endpoint.
- The report includes candidate, replay, configuration, and five sample
  sections. Raw `RequireWorkYearsName` values are retained (for example,
  `五年以上工作经验`, `三年以上工作经验`, and `一年以上工作经验`).

The captured request used blank `attrId`, and the retained samples were
experienced roles rather than campus-specific roles. The run establishes the
listed Tencent endpoint facts, but it does not establish campus scope and does
not rescue the task-level live acceptance failure on Ctrip.

## Access accounting, deviations, and blocks

- Total live page opens: 6. Breakdown: original Ctrip root 1, Tencent 1,
  controller Ctrip diagnostics 3, and CTA-assisted Ctrip continuation 1.
  Ctrip therefore had 5 page opens for one target, violating the hard
  single-page-open constraint.
- Total replay requests: 25. Breakdown: original Ctrip story endpoint 5,
  Tencent query endpoint 5, controller diagnostics 0, and final Ctrip run 15
  (5 each for news, jobs, and employee stories). Each invocation stayed at
  `5 / 6`, but the tool has no cross-invocation budget state: the normalized
  `POST getEmployeeStory` endpoint therefore reached 10 cumulative replays.
  This is a second hard-limit deviation: the stated six-request limit is
  exceeded when requests are counted cumulatively for the normalized endpoint.
- Clicks: 1, exactly the approved `查看所有职位` CTA. Form interactions, logins,
  manual/direct/guessed endpoint requests, and bypass attempts: 0.
- Neither site reported a technical access block. The current Ctrip CTA gate
  made the original prescribed command incomplete; later controller-approved
  diagnostics documented why, but did not make the extra opens compliant.
- The prescribed failure, diagnostic evidence, root cause, and continuation
  ruling are all retained here. No live-driven implementation change was made,
  and this report does not certify the live execution as compliant or accepted.

## Offline parser-config contract correction

After the live runs, an offline review against the T1 adapter contract found
that the T2 draft generator emitted `success.value` instead of
`success.expect`, and emitted fixed POST JSON under `params` instead of
`body`. Tests were changed first and failed on exactly those mismatches; the
generator was then minimally corrected so GET query data remains under
`params`, POST JSON is emitted under `body`, and success checks use `expect`.

The configuration blocks in both discovery reports were corrected from their
already captured request/response evidence. All Ctrip POST candidate configs
now use `body`; the Tencent GET config retains `params`; and every success
block uses `expect`. Endpoint observations, request values, response facts,
replay results, inferred paths and fields, and raw samples are unchanged. No
browser, network, replay, page, or endpoint request was made for this
correction, preserving the recorded total of 25 replay requests.

These generated `body` and `success.expect` drafts require the Phase 02 T1
JSON API supplement to be integrated before the runtime collector can consume
them. T2 intentionally cannot change or import `radar/` under its hard scope.
A combined T1+T2 contract test is therefore deferred to the integration branch
where both supplements are present.

## Offline final-review corrections

Further offline review produced bounded implementation corrections:

- Semantic unique identifiers (`jobId`, `postId`, and `positionId`) now outrank
  a generic unique `id`, even when only the generic value has a recognized
  numeric/UUID shape. The retained live Ctrip artifact remains
  `position_key="id"` because no live artifact was regenerated during this
  offline correction. Its persisted sample is field-selected and therefore
  does not establish whether the original response row contained `jobId`;
  that must be rechecked in any separately authorized live acceptance rerun.
- Candidate identity now includes `list_path`, retaining every qualifying
  array for a request variant. One five-call replay ladder is captured once and
  re-evaluated independently for all retained paths without extra requests.
- `offset` and `pageOffset` are no longer treated as page indexes. Offset/size
  pairs remain non-executable candidates with an explicit unsupported/manual
  review note because T1 supports only `page_index`; a complete true page-index
  pair takes precedence if offset metadata also exists.
- Candidate presentation now sorts by confidence descending, with campus
  filter score used only as a tie-breaker. The existing Ctrip candidate
  sections were mechanically reordered to confidence `50`, `20`, then `15`;
  their captured facts, configs, replay rows, and samples are unchanged.
- Target URLs containing userinfo are rejected without echoing credentials.
  Captured request URLs containing userinfo are stripped in retained capture
  facts, reports, and configs; safe and credential-bearing observations remain
  distinct during deduplication. Unsafe candidates are marked non-integrable
  and refused at the replay boundary before a session is created.
- Captured `Authorization`, `Proxy-Authorization`, and `X-API-Key` values are
  redacted from retained results and reported by `header.*` path. Such
  candidates receive zero replay calls; credential headers are defensively
  absent from all five replay profiles and refused by the requester before
  session creation. Anonymous Cookie and signature-header ladder behavior is
  unchanged.

Each behavior was reproduced with a focused failing offline test before its
minimal production fix. No live artifact was regenerated, and no browser,
network, page, replay, or endpoint request occurred during these corrections;
the recorded five Ctrip page opens, 25 total replays, and 10 cumulative
`getEmployeeStory` replays remain unchanged.

## Artifacts

- `work/discovery-ctrip.md` — final CTA-assisted Ctrip evidence report; it
  supersedes the earlier incomplete root-page artifact, with only its config
  schema and candidate-section presentation order corrected offline as
  documented above.
- `work/discovery-tencent.md` — Tencent discovery evidence report, with only
  its success config key corrected offline as documented above.
- `work/phase-02-02-api-discovery-tool-report.md` — this assessment.

## Final offline verification

- Focused adapter-contract RED: 4 selected tests failed on the expected
  `value`/`expect` and missing POST `body` mismatches before production code
  changed; focused GREEN after the minimal fix: 4 passed.
- Fix Round 4 focused RED/GREEN cases cover semantic identity precedence,
  multi-array replay reuse and its five-call bound, offset pagination safety,
  confidence-first ordering, URL-userinfo refusal and deduplication safety, and
  credential-header redaction/refusal at analysis, profile, and requester
  boundaries.
- All final commands below used the verified Python 3.13.14 interpreter at
  `C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe`.
- `python.exe -m pytest tools/tests -v`: 50 passed, 10 subtests passed.
- `python.exe manage.py test radar.tests`: 131 passed; 0 failures.
- `python.exe manage.py check`: 0 issues.
- `python.exe manage.py makemigrations --check --dry-run`: No changes detected.
- `python.exe -m compileall -q tools`: exit 0.
- `python.exe tools/discover_api.py --help`: exit 0 with the expected CLI and
  compliance notice.
- An earlier unqualified `python.exe` attempt resolved to the unrelated
  Python 3.11 installation at `D:\python\python3.11\python.exe`, which does not
  have Django installed. That was an environment-only interpreter-selection
  failure; the entire gate was rerun from the beginning with the verified
  interpreter above.
