# Local Campus Recruitment Radar V0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-local, private campus-recruitment radar that automatically refreshes verified official sources at 22:00 Asia/Shanghai, publishes eligible Beijing/Shanghai/Guangzhou/Shenzhen notices, and preserves the owner's application progress.

**Architecture:** Build one Django application around a SQLite database. Keep official-source admission, page collection, parsing, publication, query UI, and personal application progress in separate services. Windows Task Scheduler invokes one management command; the local browser UI displays data and warns when the 22:00 scheduled run is missing.

**Tech Stack:** CPython 3.13, Django `>=5.2.8,<5.3`, SQLite, Requests, Beautiful Soup 4, standard Django test runner, and PowerShell for local launch and scheduled-task registration.

## Global Constraints

- Use `py -3.13`; local inspection verified that Python 3.13 is installed and Django 5.2 officially supports it.
- Store all application data in the project-local SQLite file; do not store resumes, cookies, passwords, access tokens, or application-account data.
- Read only public sources at low frequency. Do not log in, evade bot checks, use proxy pools, or activate a source without recorded official-source evidence.
- A source failure may create a failed run record but must never delete or automatically expire existing notices.
- Auto-publish only when verified-source, official-URL, recruitment-content, target-location, and duplicate checks all pass.
- `application_progress` is user-owned data. Collection and publication code must never rewrite it.
- Do not install dependencies, create Windows scheduled tasks, access real corporate sources, initialize Git, or create a commit until the user explicitly authorizes implementation and the relevant external/local action.
- The directory is not a Git repository. This phase has no commit steps; if Git is later initialized with user approval, preserve task checkpoints as intentional commits.

---

## Planned File Structure

```text
requirements.txt
manage.py
campus_radar/
  settings.py
  urls.py
  asgi.py
  wsgi.py
radar/
  admin.py
  apps.py
  models.py
  urls.py
  views.py
  forms.py
  collectors/
    base.py
    html.py
    registry.py
  services/
    admission.py
    locations.py
    normalization.py
    publication.py
    update_runner.py
    update_status.py
  management/commands/
    run_daily_update.py
    import_source_catalog.py
  templates/radar/
    dashboard.html
    notice_table.html
  static/radar/
    dashboard.js
    dashboard.css
  tests/
    fixtures/
      official_notice.html
    test_project.py
    test_models.py
    test_admission.py
    test_locations.py
    test_publication.py
    test_collection.py
    test_update_runner.py
    test_update_status.py
    test_views.py
    test_source_catalog.py
scripts/
  run_local.ps1
  install_daily_task.ps1
docs/
  runbooks/windows-scheduled-task.md
  source-onboarding.md
data/
  source_catalog.csv
```

## Cross-Task Interfaces

The following interfaces are fixed before implementation. Later tasks consume these exact names and contracts.

```python
# radar/collectors/base.py
@dataclass(frozen=True)
class FetchedPage:
    canonical_url: str
    body: str
    content_hash: str
    http_status: int
    etag: str | None
    not_modified: bool = False

@dataclass(frozen=True)
class PositionCandidate:
    title: str
    location_text: str
    raw_text: str
    application_url: str | None

@dataclass(frozen=True)
class NoticeCandidate:
    title: str
    official_notice_url: str
    recruitment_type: str
    target_audience: str
    published_on: date | None
    deadline: date | None
    withdrawn: bool
    evidence_excerpt: str
    positions: tuple[PositionCandidate, ...]

class SourceAdapter(Protocol):
    def fetch(self, source: OfficialSource) -> FetchedPage: ...
    def extract(self, source: OfficialSource, page: FetchedPage) -> list[NoticeCandidate]: ...

# radar/services/publication.py
@dataclass(frozen=True)
class PublicationResult:
    action: Literal["created", "updated", "rejected", "unchanged"]
    notice_id: int | None
    reasons: tuple[str, ...]

def publish_candidate(source: OfficialSource, candidate: NoticeCandidate, version: SourceVersion) -> PublicationResult: ...

# radar/services/update_runner.py
@dataclass(frozen=True)
class UpdateSummary:
    update_run_id: int
    sources_checked: int
    sources_failed: int
    notices_created: int
    notices_updated: int
    notices_rejected: int

def run_update(*, trigger: str, now: datetime | None = None, source_ids: Iterable[int] | None = None) -> UpdateSummary: ...

# radar/services/update_status.py
def scheduled_run_is_missing(now: datetime) -> bool: ...
def latest_successful_update() -> UpdateRun | None: ...
```

### Task 1: Bootstrap a Django Project with a Reproducible Local Test Baseline

**Files:**

- Create: `requirements.txt`
- Create: `manage.py`
- Create: `campus_radar/__init__.py`
- Create: `campus_radar/settings.py`
- Create: `campus_radar/urls.py`
- Create: `campus_radar/asgi.py`
- Create: `campus_radar/wsgi.py`
- Create: `radar/__init__.py`
- Create: `radar/apps.py`
- Create: `radar/tests/__init__.py`
- Create: `radar/tests/test_project.py`

**Interfaces:**

- Produces a Django project named `campus_radar`, with installed app `radar`, project-local `db.sqlite3`, `Asia/Shanghai` time zone, and a deterministic Django test command.
- Later tasks depend on `python manage.py test radar.tests` and Django migrations being available.

- [ ] **Step 1: Create the minimal project files and pin the initial dependency range**

Create `requirements.txt` with exactly these first V0 runtime dependencies:

```text
Django>=5.2.8,<5.3
requests>=2.32,<3
beautifulsoup4>=4.13,<5
```

Generate the Django project and `radar` application with `py -3.13`. Configure `INSTALLED_APPS` to include `radar`, set `TIME_ZONE = "Asia/Shanghai"`, set `USE_TZ = True`, and keep SQLite at `BASE_DIR / "db.sqlite3"`.

- [ ] **Step 2: Write the baseline configuration test**

Create `radar/tests/test_project.py`:

```python
from django.conf import settings
from django.test import SimpleTestCase


class ProjectConfigurationTests(SimpleTestCase):
    def test_project_uses_china_time_zone(self) -> None:
        self.assertEqual(settings.TIME_ZONE, "Asia/Shanghai")
        self.assertTrue(settings.USE_TZ)
```

- [ ] **Step 3: Run the test to verify the baseline is executable**

Run:

```powershell
py -3.13 manage.py test radar.tests.test_project -v 2
```

Expected: one passing test and no system-check errors.

- [ ] **Step 4: Run Django's project check**

Run:

```powershell
py -3.13 manage.py check
```

Expected: `System check identified no issues`.

- [ ] **Step 5: Record the checkpoint without committing**

Record the commands and outcomes in the implementation handoff. Do not initialize Git or commit without a separate user instruction.

### Task 2: Model Official Sources, Recruitment Notices, Evidence, and Personal Progress

**Files:**

- Create: `radar/models.py`
- Create: `radar/admin.py`
- Create: `radar/migrations/0001_initial.py`
- Create: `radar/tests/test_models.py`

**Interfaces:**

- Produces the models `Organization`, `OfficialSource`, `UpdateRun`, `FetchRun`, `SourceVersion`, `RecruitmentNotice`, `NoticePosition`, `ApplicationLink`, `Evidence`, and `ApplicationProgress`.
- `RecruitmentNotice` has a unique `(organization, official_notice_url)` identity.
- `ApplicationProgress` is a one-to-one record for `RecruitmentNotice` and has the seven confirmed choices.
- `OfficialSource` includes `is_verified`, `is_active`, `admission_evidence`, `adapter_name`, `parser_config`, and `last_etag`; `NoticePosition` includes `normalized_locations`.
- `UpdateRun` includes `trigger`, `scheduled_for_date`, and a status chosen from `running`, `success`, `partial_failure`, and `failed`; its `is_successful` property is true for `success` and `partial_failure`.

- [ ] **Step 1: Write failing model tests for notice identity and user-owned progress**

Create `radar/tests/test_models.py` with these core assertions:

```python
from django.db import IntegrityError
from django.test import TestCase

from radar.models import ApplicationProgress, Organization, RecruitmentNotice


class RecruitmentModelTests(TestCase):
    def setUp(self) -> None:
        self.organization = Organization.objects.create(
            name="示例互联网公司", company_type="internet", industry="互联网"
        )

    def test_same_organization_and_official_url_cannot_create_two_notices(self) -> None:
        RecruitmentNotice.objects.create(
            organization=self.organization,
            title="2027 校园招聘",
            official_notice_url="https://careers.example.com/2027",
        )
        with self.assertRaises(IntegrityError):
            RecruitmentNotice.objects.create(
                organization=self.organization,
                title="重复标题不影响 URL 去重",
                official_notice_url="https://careers.example.com/2027",
            )

    def test_new_notice_gets_user_progress_defaulting_to_not_applied(self) -> None:
        notice = RecruitmentNotice.objects.create(
            organization=self.organization,
            title="2027 校园招聘",
            official_notice_url="https://careers.example.com/another",
        )
        progress = ApplicationProgress.objects.create(notice=notice)
        self.assertEqual(progress.status, ApplicationProgress.Status.NOT_APPLIED)
```

- [ ] **Step 2: Implement the model contract and create the first migration**

Implement the model choices and key constraints. The important shape is:

```python
class RecruitmentNotice(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "招聘中"
        EXPIRED = "expired", "已截止"
        WITHDRAWN = "withdrawn", "已撤回"

    organization = models.ForeignKey("Organization", on_delete=models.PROTECT)
    title = models.CharField(max_length=300)
    official_notice_url = models.URLField()
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_verified_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "official_notice_url"],
                name="unique_notice_per_organization_and_url",
            )
        ]
```

Use `PROTECT` for historical entities, `JSONField(default=list)` for aliases, parser configuration, and normalized locations, and `TextField` only for short evidence excerpts. Define `UpdateRun.is_successful` as a property that returns true for `success` and `partial_failure`. Do not persist full raw third-party pages.

- [ ] **Step 3: Generate and apply the migration locally**

Run:

```powershell
py -3.13 manage.py makemigrations radar
py -3.13 manage.py migrate
```

Expected: one initial `radar` migration applies cleanly.

- [ ] **Step 4: Run the model tests**

Run:

```powershell
py -3.13 manage.py test radar.tests.test_models -v 2
```

Expected: all tests pass, including the uniqueness violation and default progress state.

- [ ] **Step 5: Register safe local management views**

Register the core models in `radar/admin.py`. Mark source evidence, fetch runs, source versions, and evidence records read-only after creation so ordinary UI edits cannot silently rewrite the audit trail.

### Task 3: Implement Deterministic Admission, Location, Normalization, and Publication Rules

**Files:**

- Create: `radar/services/__init__.py`
- Create: `radar/services/admission.py`
- Create: `radar/services/locations.py`
- Create: `radar/services/normalization.py`
- Create: `radar/services/publication.py`
- Create: `radar/tests/test_admission.py`
- Create: `radar/tests/test_locations.py`
- Create: `radar/tests/test_publication.py`

**Interfaces:**

- `is_target_location(location_text: str) -> bool` returns true for Beijing, Shanghai, Guangzhou, or Shenzhen and common Chinese variants.
- `source_is_admitted(source: OfficialSource) -> bool` requires active, verified, and non-empty official evidence.
- `publish_candidate(...) -> PublicationResult` never overwrites `ApplicationProgress`.

- [ ] **Step 1: Write failing policy tests for the five auto-publish gates**

Use a verified official source and a candidate position in Beijing as the positive path. Include these negative assertions:

```python
self.assertFalse(is_target_location("杭州"))
self.assertFalse(source_is_admitted(unverified_source))
self.assertEqual(result.action, "rejected")
self.assertIn("missing_target_location", result.reasons)
```

Add a regression test that changes a notice title through `publish_candidate()` after an `ApplicationProgress` record has status `已面试`, then asserts the progress remains `已面试`.

- [ ] **Step 2: Implement normalized target-location matching**

Implement an explicit alias map rather than fuzzy inference:

```python
TARGET_LOCATION_ALIASES = {
    "北京": {"北京", "北京市"},
    "上海": {"上海", "上海市"},
    "广州": {"广州", "广州市"},
    "深圳": {"深圳", "深圳市"},
}
```

Normalize punctuation and whitespace before matching. Return false for an empty or unknown location; do not assume that a national role includes all four cities unless the source text explicitly names one of them.

- [ ] **Step 3: Implement source admission and notice publication**

`source_is_admitted()` must require `is_verified=True`, `is_active=True`, an allowed source type, a non-empty `admission_evidence`, and an `https` source URL. `publish_candidate()` must:

1. reject non-admitted sources;
2. reject missing official notice URLs;
3. reject candidates with no target-city positions;
4. create or update the notice by organization and canonical official URL;
5. upsert positions, application links, and evidence; and
6. leave `ApplicationProgress` untouched.

- [ ] **Step 4: Run the rule suite**

Run:

```powershell
py -3.13 manage.py test radar.tests.test_admission radar.tests.test_locations radar.tests.test_publication -v 2
```

Expected: each rejection reason is explicit; the positive path creates one active notice; progress survives publication updates.

### Task 4: Build a Low-Frequency HTML Collector and Source-Version Change Detector

**Files:**

- Create: `radar/collectors/__init__.py`
- Create: `radar/collectors/base.py`
- Create: `radar/collectors/html.py`
- Create: `radar/collectors/registry.py`
- Create: `radar/tests/fixtures/official_notice.html`
- Create: `radar/tests/test_collection.py`

**Interfaces:**

- `HtmlSourceAdapter.fetch(source)` produces `FetchedPage` and honors an existing ETag.
- `HtmlSourceAdapter.extract(source, page)` returns `NoticeCandidate` values using per-source selector configuration held in `OfficialSource.parser_config`.
- `AdapterRegistry.get(source)` resolves only registered adapter names and rejects unknown ones.

- [ ] **Step 1: Write fixture-backed collector tests before making network code**

Create an HTML fixture with a known title, one Beijing position, one deadline, an official announcement URL, and an application URL. Mock the HTTP session so tests never access the network:

```python
with patch("radar.collectors.html.requests.Session.get") as get:
    get.return_value.status_code = 200
    get.return_value.text = fixture_text
    get.return_value.headers = {"ETag": '"fixture-v1"'}
    page = adapter.fetch(source)

self.assertEqual(page.http_status, 200)
self.assertFalse(page.not_modified)
self.assertEqual(len(adapter.extract(source, page)), 1)
```

Add a `304` response test that sets `not_modified=True` and does not invoke `extract()`.

- [ ] **Step 2: Implement the collector contract and deterministic content hash**

Use `requests.Session` with a 15-second timeout, an identifiable non-deceptive user agent, and `If-None-Match` only when `OfficialSource.last_etag` exists. Canonicalize the fetched URL without dropping query parameters that the source uses for content identity. Compute `content_hash` with SHA-256 over UTF-8 response text.

- [ ] **Step 3: Implement selector-config extraction**

Define and validate this JSON configuration shape:

```json
{
  "adapter": "html_selector",
  "notice_selector": "article.job",
  "title_selector": "h2",
  "location_selector": ".location",
  "deadline_selector": ".deadline",
  "application_selector": "a.apply",
  "excerpt_selector": ".description"
}
```

The extractor must reject a configuration missing `notice_selector` or `title_selector`. It may return an empty list but must not invent a candidate from unrelated page text.

- [ ] **Step 4: Persist collection observations through `FetchRun` and `SourceVersion`**

For a 200 changed page, create one successful `FetchRun` and one `SourceVersion`; for 304, create a successful not-modified `FetchRun` with no new version; for a request exception, create a failed `FetchRun` with a sanitized error message. Never store request headers containing credentials.

- [ ] **Step 5: Run collection tests**

Run:

```powershell
py -3.13 manage.py test radar.tests.test_collection -v 2
```

Expected: fixture parsing, ETag behavior, hashes, and failed-run persistence all pass without external traffic.

### Task 5: Orchestrate One Update Run and Automatic Notice Lifecycle Changes

**Files:**

- Create: `radar/services/update_runner.py`
- Create: `radar/management/__init__.py`
- Create: `radar/management/commands/__init__.py`
- Create: `radar/management/commands/run_daily_update.py`
- Create: `radar/tests/test_update_runner.py`

**Interfaces:**

- `run_update(trigger, now, source_ids)` creates an `UpdateRun` and returns `UpdateSummary`.
- The command accepts `--trigger scheduled|manual` and optional repeatable `--source-id` arguments.
- Expiration changes only active notices whose deadline is earlier than the Asia/Shanghai local date; fetch failures never trigger expiration.

- [ ] **Step 1: Write failing orchestration tests with fake adapters**

Use `unittest.mock.patch` to make `AdapterRegistry.get()` return a fake adapter. Assert one healthy source produces one published notice, one exception produces a failed `FetchRun`, and the successful source still completes:

```python
summary = run_update(trigger="scheduled", now=aware_datetime)
self.assertEqual(summary.sources_checked, 2)
self.assertEqual(summary.sources_failed, 1)
self.assertEqual(summary.notices_created, 1)
self.assertTrue(UpdateRun.objects.get(pk=summary.update_run_id).is_successful)
```

Add a test proving an active notice with yesterday's deadline becomes `expired`, while an active notice from a source that fails remains `active`.

- [ ] **Step 2: Implement a failure-isolated update runner**

Process each admitted active source in its own exception boundary. Continue after a single source failure, create the relevant run records, and calculate summary counts from actual `PublicationResult` values. Set `UpdateRun.is_successful` false only when no source completed successfully; partial source failure must be visible in the summary and dashboard.

- [ ] **Step 3: Implement the management command as a thin adapter**

The command must call `run_update()` and print this one-line machine-readable summary after completion:

```text
update_run_id=<id> sources_checked=<n> sources_failed=<n> notices_created=<n> notices_updated=<n> notices_rejected=<n>
```

Return a nonzero command exit only when no active admitted source can complete. A partial failure must exit zero while reporting the failure count.

- [ ] **Step 4: Run the update-runner suite**

Run:

```powershell
py -3.13 manage.py test radar.tests.test_update_runner -v 2
```

Expected: success, partial failure, deadline expiration, and non-deletion behavior pass.

### Task 6: Build the Local Table, Column Chooser, and Manual Application Progress Controls

**Files:**

- Create: `radar/forms.py`
- Create: `radar/urls.py`
- Create: `radar/views.py`
- Modify: `campus_radar/urls.py`
- Create: `radar/templates/radar/dashboard.html`
- Create: `radar/templates/radar/notice_table.html`
- Create: `radar/static/radar/dashboard.js`
- Create: `radar/static/radar/dashboard.css`
- Create: `radar/tests/test_views.py`

**Interfaces:**

- `GET /` lists active notices with filters for company name, company type, industry, recruitment type, target audience, target city, position keyword, and deadline.
- `POST /notices/<notice_id>/progress/` accepts exactly one of the seven approved progress choices and redirects back to the table.
- `POST /update-now/` calls `run_update(trigger="manual")` only from the local app UI, then redirects with a factual result message.

- [ ] **Step 1: Write failing view tests for visible fields, filters, and progress changes**

Create notices for Beijing and Hangzhou, then assert the city filter returns only the Beijing record. Test the progress form:

```python
response = self.client.post(
    f"/notices/{notice.pk}/progress/",
    {"status": "interviewed"},
    follow=True,
)
self.assertEqual(response.status_code, 200)
notice.application_progress.refresh_from_db()
self.assertEqual(notice.application_progress.status, "interviewed")
```

Add a test that `expired` notices are absent from the default listing but can be requested with `status=expired`.

- [ ] **Step 2: Implement query and progress forms with explicit allow-lists**

Use Django forms, not raw request values. Filter job locations through `NoticePosition.normalized_locations`; filter status through model choices. The progress endpoint must use `ApplicationProgress.objects.get_or_create(notice=notice)` before changing the approved status. The server must never accept arbitrary progress strings or modify recruitment status from the personal progress endpoint.

- [ ] **Step 3: Implement the table and column visibility behavior**

Render the confirmed columns: company name, company type, industry, recruitment type, target audience, locations, positions, application progress, update time, deadline, official application link, official announcement link, and notes. Add checkbox controls with `data-column` attributes and use `localStorage` only to remember visible columns for this browser. Do not add group labels, company-scale columns, or written-test columns.

- [ ] **Step 4: Implement local-only manual update feedback**

The `update-now` view must display the actual `UpdateSummary` counts. It must not claim a scheduled task ran when the trigger was manual.

- [ ] **Step 5: Run the view suite**

Run:

```powershell
py -3.13 manage.py test radar.tests.test_views -v 2
```

Expected: filtering, status isolation, default active-only list, and update feedback all pass.

### Task 7: Implement 22:00 Missed-Run Detection and Local Launch Support

**Files:**

- Create: `radar/services/update_status.py`
- Create: `radar/tests/test_update_status.py`
- Modify: `radar/views.py`
- Modify: `radar/templates/radar/dashboard.html`
- Create: `scripts/run_local.ps1`

**Interfaces:**

- `scheduled_run_is_missing(now)` uses Asia/Shanghai and compares the expected 22:00 scheduled run with stored successful scheduled runs.
- A manual update after a missed schedule is recorded as manual; the dashboard may report fresh data but still shows the audit fact that the scheduled trigger was missed.
- `scripts/run_local.ps1` starts the local app without installing or registering any external service.

- [ ] **Step 1: Write time-boundary tests**

Define the test helpers before the assertions:

```python
from datetime import date, datetime
from zoneinfo import ZoneInfo


def shanghai_datetime(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("Asia/Shanghai"))


def create_successful_scheduled_run(*, for_date: date) -> UpdateRun:
    return UpdateRun.objects.create(
        trigger="scheduled",
        scheduled_for_date=for_date,
        status="success",
    )
```

Then assert these cases:

```python
self.assertFalse(scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 21, 59)))
self.assertTrue(scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 22, 1)))
create_successful_scheduled_run(for_date=date(2026, 8, 17))
self.assertFalse(scheduled_run_is_missing(shanghai_datetime(2026, 8, 17, 22, 1)))
```

Also test that a successful manual run does not masquerade as a scheduled run.

- [ ] **Step 2: Implement expected-run-date and status helpers**

Compute the expected date as today only at or after 22:00 Asia/Shanghai; before 22:00, use the prior calendar day. Query `UpdateRun` by `trigger="scheduled"`, `status="success"`, and `scheduled_for_date`. Use a `scheduled_for_date` field rather than parsing timestamps so daylight or clock changes cannot blur the audit record.

- [ ] **Step 3: Display a missed-run banner and factual last-update details**

When a scheduled run is missing, render a visible banner containing the expected 22:00 time, the last successful run timestamp, and an `立即更新` form. When the current data came from a manual run after a miss, retain wording that distinguishes “manual refresh completed” from “scheduled run completed”.

- [ ] **Step 4: Implement a safe local launcher script**

Create `scripts/run_local.ps1` that resolves the project directory from `$PSScriptRoot`, starts `py -3.13 manage.py runserver 127.0.0.1:8000`, and opens no external ports. It must fail with a clear message when migrations have not been applied.

- [ ] **Step 5: Run missed-run tests**

Run:

```powershell
py -3.13 manage.py test radar.tests.test_update_status -v 2
```

Expected: the 21:59, 22:01, successful scheduled run, and manual-after-miss cases all pass.

### Task 8: Add Source-Catalog Import, Onboarding Controls, and Offline Fixture Coverage

**Files:**

- Create: `data/source_catalog.csv`
- Create: `radar/management/commands/import_source_catalog.py`
- Create: `radar/tests/test_source_catalog.py`
- Create: `docs/source-onboarding.md`

**Interfaces:**

- The CSV has this exact header:

```text
organization_name,company_type,industry,official_domain,source_type,source_url,admission_evidence,adapter_name,parser_config,is_active
```

- `import_source_catalog --path data/source_catalog.csv --dry-run` validates rows and writes nothing.
- Without `--dry-run`, the command upserts organizations and sources only after all rows validate; it never performs network requests.

- [ ] **Step 1: Write failing import tests for source evidence and atomic validation**

Create one valid local CSV row and one invalid row without `admission_evidence`. Assert that dry run produces no rows and a non-dry run with any invalid row also writes no organization or source:

```python
call_command("import_source_catalog", "--path", csv_path, "--dry-run")
self.assertEqual(OfficialSource.objects.count(), 0)

with self.assertRaises(CommandError):
    call_command("import_source_catalog", "--path", invalid_csv_path)
self.assertEqual(OfficialSource.objects.count(), 0)
```

- [ ] **Step 2: Implement the catalog command and template CSV**

Use `csv.DictReader`, reject non-HTTPS URLs, reject unknown `source_type` or `adapter_name`, validate `parser_config` as JSON, and wrap non-dry-run writes in `transaction.atomic()`. The committed template contains only the CSV header; `docs/source-onboarding.md` contains its explanation. Do not put unverified live corporate URLs into the codebase.

- [ ] **Step 3: Write the source-onboarding procedure**

`docs/source-onboarding.md` must state the exact human verification sequence:

1. identify a candidate organization from the agreed target pool;
2. locate the company career entrypoint on the official domain;
3. record the evidence that proves the career page or official recruitment account relationship;
4. record a low-frequency, public, no-login access policy;
5. validate its selector configuration against a saved, non-sensitive fixture;
6. run CSV dry-run validation; and
7. obtain approval before activating a new live source batch.

- [ ] **Step 4: Run source-catalog tests**

Run:

```powershell
py -3.13 manage.py test radar.tests.test_source_catalog -v 2
```

Expected: valid dry runs do not write, invalid batches are atomic, and no test accesses a real source.

### Task 9: Provide a Safe Windows 22:00 Scheduled-Task Installer and Runbook

**Files:**

- Create: `scripts/install_daily_task.ps1`
- Create: `docs/runbooks/windows-scheduled-task.md`
- Modify: `radar/tests/test_update_status.py`

**Interfaces:**

- `scripts/install_daily_task.ps1` accepts `-Apply` and is dry-run by default.
- The scheduled task name is `OfficialCampusRadarDailyUpdate`.
- The scheduled command is `py -3.13 <project>\manage.py run_daily_update --trigger scheduled` at 22:00 daily.

- [ ] **Step 1: Add a static contract test for the scheduled command arguments**

Create a pure-Python helper in `radar.services.update_status` named `scheduled_command_arguments(project_root: Path) -> list[str]`. Test that it returns exactly:

```python
[
    "-3.13",
    str(project_root / "manage.py"),
    "run_daily_update",
    "--trigger",
    "scheduled",
]
```

The PowerShell script consumes this documented contract; the test prevents accidental omission of the scheduled trigger.

- [ ] **Step 2: Implement the dry-run-first PowerShell installer**

`install_daily_task.ps1` must construct a `ScheduledTaskAction`, `ScheduledTaskTrigger -Daily -At 22:00`, and a `ScheduledTaskSettingsSet` that does not wake the computer. Without `-Apply`, print the intended action, trigger, working directory, and task name, then exit without calling `Register-ScheduledTask`. With `-Apply`, register or replace only `OfficialCampusRadarDailyUpdate`.

- [ ] **Step 3: Write the Windows runbook**

Document: prerequisites, the dry-run command, the exact `-Apply` command, how to inspect the task in Task Scheduler, how to test it manually, expected update-run records, how missed-run detection behaves when the computer is off, and how to remove the named task. Clearly label registration and removal as user-approved external/local system changes.

- [ ] **Step 4: Run the unit test and PowerShell syntax check**

Run:

```powershell
py -3.13 manage.py test radar.tests.test_update_status -v 2
powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/install_daily_task.ps1)) | Out-Null"
```

Expected: Python test passes and PowerShell parses the script. Do not run `-Apply` in this task without explicit user approval.

### Task 10: Run the Full V0 Validation Suite and Produce an Implementation Handoff

**Files:**

- Modify: `DEV_STATE.md`
- Modify: `docs/handoffs/phase-01-v0-design-handoff.md`
- Create: `docs/runbooks/local-verification.md`

**Interfaces:**

- Produces fresh, factual validation evidence and an implementation handoff. It does not assert that a real corporate source has been activated unless a separately approved source-onboarding batch has actually been verified.

- [ ] **Step 1: Run the complete automated suite and Django checks**

Run:

```powershell
py -3.13 manage.py makemigrations --check --dry-run
py -3.13 manage.py check
py -3.13 manage.py test radar.tests -v 2
```

Expected: no unapplied model changes, no Django system-check errors, and all tests passing.

- [ ] **Step 2: Perform local manual verification using fixtures and the local database**

Use the source-catalog dry run and fixture-backed collector tests. Launch the local app with `scripts/run_local.ps1`; verify the table filters, column chooser, official-link rendering, seven progress choices, active/expired behavior, and missed-run banner with controlled test data. Do not activate real sources or register the Windows task without the required approval.

- [ ] **Step 3: Write the local verification runbook**

`docs/runbooks/local-verification.md` must list the exact commands, expected screen behavior, expected database/run-record state, and the distinction between fixture validation and live source validation.

- [ ] **Step 4: Update the phase handoff and development state from actual evidence**

Replace planning-only statements with the real changed-file list, real command outcomes, unmet acceptance criteria, residual risks, and the next user decision. Do not claim Windows task registration or live-source success without direct evidence.

- [ ] **Step 5: Request a proportionate read-only review**

After required validation passes, request a separate read-only review against the approved Design Handoff. Route actionable findings back to the single implementation owner for one bounded repair round; do not let the reviewer edit files.

## Plan Self-Review

- Spec coverage: Tasks 1–2 provide the local application and data model; Tasks 3–5 implement source admission, automatic publication, update execution, and lifecycle behavior; Tasks 6–7 implement the personal table/progress/missed-run behavior; Tasks 8–9 cover source onboarding and Windows scheduling; Task 10 requires fresh validation and a separate review.
- Placeholder scan: The plan fixes names, paths, commands, interface signatures, test cases, and expected outcomes. Live company URLs are deliberately excluded because they require a separate evidence-based onboarding approval, not an unspecified implementation shortcut.
- Type consistency: `NoticeCandidate`, `PublicationResult`, `UpdateSummary`, `run_update`, and `scheduled_run_is_missing` have one definition in the cross-task contract and are used consistently by later tasks.

## Execution Handoff

The plan is ready at `docs/superpowers/plans/2026-08-17-local-campus-radar-v0.md`.

Execution is intentionally gated: the project is not yet a Git repository, and implementation will create local files, install dependencies, and eventually require a separately approved Windows scheduled-task registration. Under the approved phase model, implementation should be performed by one bounded `实施任务1` owner, followed by a separate read-only review. Before starting that task, the user must explicitly authorize Phase 01 implementation.
