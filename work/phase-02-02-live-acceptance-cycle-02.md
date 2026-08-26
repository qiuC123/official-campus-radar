# Phase 02-02 live acceptance — Cycle 02

Date: 2026-08-21 (Asia/Shanghai)

Status: **LIVE_ACCEPTANCE_PASSED_FOR_TOOL_BASELINE**.

This result applies only to the T2 discovery-tool baseline. It does not erase
Cycle 01, imply runtime integration, or establish that every observed response
contains campus-recruitment data.

## Prospective rule revision

Before any Cycle 02 network access, the acceptance rule was changed to the
following auditable lifecycle:

- one tool invocation, one browser context, one page instance, and one initial
  navigation per target;
- scrolling within that page is allowed;
- at most one guarded click may continue in the same page instance;
- reloads, second `goto` calls, new pages, popups, and diagnostic reruns are
  prohibited;
- each normalized endpoint may receive at most six cumulative replays in the
  cycle; the fixed ladder uses five.

The normative protocol is
`docs/handoffs/phase-02-02-live-acceptance-cycle-02.md`. Cycle 01 remains
historically failed for five Ctrip page opens and ten cumulative
`getEmployeeStory` replays.

## Execution ledger

Exactly two live commands were executed, serially, with no diagnostic or
follow-up target run:

| Target | Invocations | Contexts | Page instances | Initial navigations | Safe clicks | Reloads / second `goto` | New page / popup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ctrip | 1 | 1 | 1 | 1 | 1 (`查看所有职位`) | 0 | 0 |
| Tencent | 1 | 1 | 1 | 1 | 0 | 0 | 0 |

The Ctrip page remained the same page instance while its URL changed from
`#/campus` to `#/campus/jobList`. The Tencent entry and final URLs were both
`/search.html`. Neither report recorded an error, block, popup, new-page guard
violation, login wall, or CAPTCHA.

The reports were generated at `17:53:58+08:00` and `17:54:48+08:00`, a
50-second separation, and the commands were not run concurrently. The tool's
single-target path contains one `new_context`, one guarded `new_page`, and one
`page.goto`; it exposes no reload action and accepts at most one `--click`
selector per target.

## Replay-budget audit

| Target | Normalized endpoint | Replays | Limit | Result |
| --- | --- | ---: | ---: | --- |
| Ctrip | `POST /api/hrrecruit/getJobAd` | 5 | 6 | Pass |
| Ctrip | `POST /api/hrrecruit/listActiveNews` | 5 | 6 | Pass |
| Ctrip | `POST /api/hrrecruit/getEmployeeStory` | 5 | 6 | Pass |
| Tencent | `GET /tencentcareer/api/post/Query` | 5 | 6 | Pass |

Cycle 02 issued 20 replay requests in total. No normalized endpoint appeared in
more than one Cycle 02 invocation, so no endpoint budget was reset or exceeded.
All four candidates reported no suspicious URL, credential-header, query, or
body paths.

## Ctrip baseline

- Entry/final page: `https://careers.ctrip.com/#/campus` →
  `https://careers.ctrip.com/#/campus/jobList`; HTTP 200.
- Required endpoint: `POST https://careers.ctrip.com/api/hrrecruit/getJobAd`.
- List/total paths: `retValue.recruitJobAdList` / `retValue.total`.
- Business success condition: `retCode="201"`.
- All five replay profiles returned HTTP 200 with an equivalent non-empty
  list. The minimal compliant headers passed, so the signature-like header was
  not required.
- The corrected identity inference selected `position_key="jobId"` and
  retained a UUID value.
- The retained discriminator was `kindName="应届校招生"`. The only retained job
  sample was titled `测试职位（请勿投递）(MJ036531)`, so this is campus-type
  evidence but not a production-worthy vacancy claim.

Result: **Ctrip tool baseline passed**. Source admission still requires human
notice metadata and normal admission-chain review.

## Tencent baseline

- Entry/final page: `https://careers.tencent.com/search.html`; HTTP 200.
- Required endpoint:
  `GET https://careers.tencent.com/tencentcareer/api/post/Query`.
- List/total paths: `Data.Posts` / `Data.Count`.
- Business success condition: `Code=200`.
- All five replay profiles returned HTTP 200 with an equivalent non-empty
  list; the minimal compliant headers passed.
- Identity inference selected `position_key="PostId"`.
- The captured request had `attrId=""`. The five retained
  `RequireWorkYearsName` values required two, three, or five years of
  experience.

Result: **Tencent tool baseline passed, campus scope not established**. This
response must not be admitted as a campus source until T3 identifies and
manually verifies an explicit campus filter.

## T1 configuration-contract audit

The primary Ctrip and Tencent JSON configuration drafts were parsed from the
new reports, supplemented only with the human-owned notice metadata and a
positive request delay, and passed
`JsonApiSourceAdapter.validate_source_config`.

The audit also verified:

- Ctrip uses POST `body`, `retValue.recruitJobAdList`,
  `success.expect="201"`, and `position_key="jobId"`;
- Tencent uses GET `params`, `Data.Posts`, `success.expect=200`, and
  `position_key="PostId"`;
- every Cycle 02 endpoint is unique after query normalization and every replay
  budget is exactly `5 / 6`;
- the retained campus discriminator fields are present.

Offline audit result: **PASS**.

## Evidence artifacts

- `work/discovery-ctrip-cycle-02.md`
  - SHA-256: `24a61a4f6bd26047ed15d52123d5718883797a54cb8d3f248b0697a0f3ffd66d`
- `work/discovery-tencent-cycle-02.md`
  - SHA-256: `fdc27a212393c244fa95840b63923d5a207f64e94bf9d610a11d900f969faa05`

No live access occurred after the two authorized commands. All subsequent
inspection, contract validation, and report generation were offline.
