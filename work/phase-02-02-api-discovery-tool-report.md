# Phase 02-02 recruitment API discovery — live report

Generated on 2026-08-21 (Asia/Shanghai).

Status: **DONE_WITH_CONCERNS**. The Tencent technical baseline passed. The
prescribed Ctrip landing-page run did not capture the required job endpoint, so
the Ctrip baseline remains unverified without any guessed navigation or direct
endpoint request.

## Implementation and interaction rules

- The two authorized commands ran strictly sequentially: Ctrip exited and its
  report was fully inspected before Tencent began.
- Each target opened one headless Chromium page. Both used the required
  10-second wait and three bounded scrolls; neither used `--click`.
- No login, form interaction, credential entry, CAPTCHA bypass, stealth,
  environment proxy, signature reconstruction, path scan, parameter guessing,
  or brute force was used.
- No endpoint was called manually. Replays came only from the tool's fixed
  five-request ladder, below the hard limit of six per normalized
  method/endpoint.
- A missing captured endpoint was treated as a factual live limitation. It was
  not converted into a guessed request or an unsupported integration claim.

## Runtime

- Interpreter: Python 3.13.14 at
  `C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe`.
- Playwright Python package: 1.62.0.
- Controller-validated browser runtime: Chromium/headless shell v1234,
  browser version 151.0.7922.34.
- Discovery branch baseline before the runs:
  `b4a3b5d03b181c90f059a7e3613ba416da541c11`.

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

## Ctrip outcome

- Entry page: `https://careers.ctrip.com/`.
- Final page: `https://careers.ctrip.com/#/`.
- Page status: 200; no login wall, CAPTCHA, or HTTP block was reported.
- Captured candidate: `POST
  https://careers.ctrip.com/api/hrrecruit/getEmployeeStory`, with list path
  `retValue`. This is an employee-story feed, not the required job feed.
- Its five replay levels all returned HTTP 200 with equivalent non-empty
  `retValue`; this result applies only to `getEmployeeStory` and is not evidence
  about `getJobAd`.

Required acceptance facts:

| Fact | Live observation | Result |
| --- | --- | :---: |
| `POST /api/hrrecruit/getJobAd` captured | Not observed | No |
| List path `retValue.recruitJobAdList` | Not available because the endpoint was not captured | Unverified |
| Total path `retValue.total` | Not available | Unverified |
| Success `retCode="201"` | Seen only on the unrelated employee-story response | Unverified for jobs |
| Body contains `condition`, `pager`, and `head` | Captured story body contained only `head` | No |
| Minimal headers equivalent; signature unnecessary | True only for the story endpoint | Unverified for jobs |
| Raw campus discriminator `kindName` retained | No job sample was captured | No |

The known endpoint was not present in captured traffic, so this was not an
eligible captured-shape inference bug. The command was not repeated; there was
no direct `getJobAd` request, click, guessed route, or offline code change.

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

- Authorized page opens: 2. Actual page opens: 2. Extra page opens: 0.
- Ctrip replay requests: 5 for the observed employee-story endpoint.
- Tencent replay requests: 5 for the observed job-query endpoint.
- Manual or guessed requests: 0. Clicks/forms/logins: 0.
- Neither site reported a technical access block. The Ctrip deviation is that
  the exact landing-page interaction sequence did not emit the required job
  endpoint. Low-frequency rules prohibited exploratory navigation or a direct
  request, so the limitation was recorded rather than bypassed.
- No target was repeated and no live-driven implementation change was made.

## Artifacts

- `work/discovery-ctrip.md` — exact generated Ctrip discovery report.
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
