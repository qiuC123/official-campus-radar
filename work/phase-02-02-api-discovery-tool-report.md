# Phase 02-02 recruitment API discovery — live report

Generated on 2026-08-21 (Asia/Shanghai).

Status: **DONE_WITH_CONCERNS**. The final CTA-assisted Ctrip run and the Tencent
run both passed their technical endpoint/replay acceptance facts. Tencent's
blank recruitment filter and experienced-role samples still require human
review before campus scope is claimed.

## Implementation and interaction rules

- The original Ctrip and Tencent commands ran strictly sequentially. After the
  Ctrip endpoint was absent, work paused until the controller completed three
  low-frequency, read-only diagnostic page opens and authorized one exact CTA
  continuation.
- The continuation opened one page, used the required wait/scroll sequence,
  and clicked only the controller-approved, non-form, same-page
  `查看所有职位` CTA through the tool's guarded `--click` path.
- No login, form interaction, credential entry, CAPTCHA bypass, stealth,
  environment proxy, signature reconstruction, path scan, parameter guessing,
  or brute force was used.
- No endpoint was called manually. Replays came only from the tool's fixed
  five-request ladder, below the hard limit of six per normalized
  method/endpoint.
- The initial missing endpoint was not converted into a guessed request. The
  final deviation followed the controller's DOM evidence and explicit ruling.

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

4. Controller-authorized CTA continuation:

   ```powershell
   C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe tools/discover_api.py --url https://careers.ctrip.com/#/campus --wait 10 --scroll --click "text=查看所有职位" --out work/discovery-ctrip.md
   ```

   Exit code 0 after 42.7 seconds. Output:
   `report: work\discovery-ctrip.md`. This was the only continuation page open;
   the report was inspected in full and no further live access occurred.

## Ctrip outcome

- The prescribed root-page command first ended at `https://careers.ctrip.com/#/`
  and captured only `getEmployeeStory`. The controller diagnostics established
  that route entry and scrolling do not load jobs; the explicit CTA does.
- Final entry page: `https://careers.ctrip.com/#/campus`; final page:
  `https://careers.ctrip.com/#/campus/jobList`; page status 200 with no login
  wall, CAPTCHA, or HTTP block.
- The guarded CTA run captured three candidate endpoints: `listActiveNews`,
  `getJobAd`, and `getEmployeeStory`. Each received exactly five replays within
  its endpoint-local `5 / 6` budget.

Required acceptance facts:

| Fact | Live observation | Result |
| --- | --- | :---: |
| `POST /api/hrrecruit/getJobAd` captured | Exact endpoint observed | Yes |
| List path `retValue.recruitJobAdList` | Exact path inferred | Yes |
| Total path `retValue.total` | Exact path inferred | Yes |
| Success `retCode="201"` | Exact condition inferred | Yes |
| Body contains `condition`, `pager`, and `head` | All three retained; `category=2`, page 1, size 10 | Yes |
| Minimal headers equivalent; signature unnecessary | All five levels HTTP 200/equivalent | Yes |
| Raw campus discriminator `kindName` retained | `kindName="应届校招生"` in the sample | Yes |

The captured job shape was inferred and rendered correctly, so this was not a
tool bug and no code/test change or additional Ctrip run was needed.

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
experienced roles rather than campus-specific roles. The technical API
baseline therefore passes, but human review must not infer campus scope from
this run alone.

## Access accounting, deviations, and blocks

- Total live page opens: 6. Breakdown: original Ctrip root 1, Tencent 1,
  controller Ctrip diagnostics 3, and CTA-assisted Ctrip continuation 1.
- Total replay requests: 25. Breakdown: original Ctrip story endpoint 5,
  Tencent query endpoint 5, controller diagnostics 0, and final Ctrip run 15
  (5 each for news, jobs, and employee stories). Every endpoint stayed at
  `5 / 6` within its individual discovery invocation.
- Clicks: 1, exactly the approved `查看所有职位` CTA. Form interactions, logins,
  manual/direct/guessed endpoint requests, and bypass attempts: 0.
- Neither site reported a technical access block. The deviation from the
  original no-click command was controller-approved only after three read-only
  diagnostics proved the current site gates job loading behind the CTA.
- The prescribed failure, diagnostic evidence, root cause, and continuation
  ruling are all retained here. No live-driven implementation change was made.

## Artifacts

- `work/discovery-ctrip.md` — exact final CTA-assisted Ctrip report; it
  supersedes the earlier incomplete root-page artifact.
- `work/discovery-tencent.md` — exact generated Tencent discovery report.
- `work/phase-02-02-api-discovery-tool-report.md` — this assessment.

## Final offline verification

- `python.exe -m pytest tools/tests -v`: 36 passed, 2 subtests passed.
- `python.exe manage.py test radar.tests`: 131 passed; 0 failures.
- `python.exe manage.py check`: 0 issues.
- `python.exe manage.py makemigrations --check --dry-run`: No changes detected.
- `python.exe -m compileall -q tools`: exit 0.
- `python.exe tools/discover_api.py --help`: exit 0 with the expected CLI and
  compliance notice.
