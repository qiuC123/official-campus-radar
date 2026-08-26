# JSON API Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax.

**Goal:** Add a configuration-driven JSON recruitment API collector that produces one evidence-backed notice with multiple positions, without weakening existing admission or publication gates.

**Architecture:** JsonApiSourceAdapter validates OfficialSource.parser_config, fetches bounded page-index API results into canonical JSON, and produces one NoticeCandidate with JSON Path evidence. Existing update orchestration consumes the unchanged adapter protocol. The HTML adapter gains an optional position_selector; its absence retains legacy single-position extraction.

**Tech Stack:** Python 3.13, Django 5.2, SQLite, requests, BeautifulSoup, Django TestCase.

**Spec:** docs/handoffs/phase-02-01-json-api-adapter-prompt.md

## Global Constraints

- Use only Django, requests, and BeautifulSoup; add no dependency or browser automation.
- Do not change append-only/hashing semantics or formal()/historical() gates.
- Tests use only fixtures/mocked requests. Do not add a real source or issue a delivery-time external request.
- API endpoints require HTTPS; only GET/POST; every multi-page fetch delays between calls.
- Only page_index pagination is supported. max_pages is positive and capped at 100.
- Do not change templates, filters, city policy, Windows tasks, or source onboarding.

## Approved Plan Amendment (2026-08-21)

- Treat `OfficialSource.SourceType.API` like `WEBSITE` for admission: both the source URL and configured API endpoint must use HTTPS and belong to the organization's official domain. This extends the existing rule without weakening the admission chain.
- Require auditable `published_on` and `deadline` values. Each may be supplied either as a fixed value under `notice` or as a JSON field path under `field_map`; invalid or missing values fail configuration/extraction rather than bypassing evidence validation.
- Preserve the configured `list_path` inside canonical `FetchedPage.body`. Store adapter completion metadata separately under `_radar`, so evidence locators such as `$.Data.Posts[0].RecruitPostName` resolve against the stored JSON document.

---

### Task 1: Define API source type and configuration contract

**Files:**

- Modify: radar/models.py:29-33
- Create: radar/migrations/0010_officialsource_api_source_type.py
- Create: radar/collectors/json_api.py
- Create: radar/tests/test_json_api_adapter.py

**Interfaces:**

- Produces OfficialSource.SourceType.API = "api".
- Produces JsonApiSourceAdapter.validate_source_config(source) -> None.

- [ ] **Step 1: Write failing configuration tests**

Create a valid BASE_CONFIG with an HTTPS endpoint, GET, page_index, page_size=2, start_page=1, max_pages=2, list_path="Data.Posts", a complete notice object, and non-empty field_map.position_key/field_map.title. Assert each isolated invalid case raises ValueError containing its key:

    def test_validation_rejects_invalid_contract_values(self):
        cases = [
            ({"endpoint": ""}, "endpoint"),
            ({"endpoint": "http://api.example.test/posts"}, "HTTPS"),
            ({"method": "PUT"}, "method"),
            ({"list_path": ""}, "list_path"),
            ({"field_map": {"position_key": "", "title": "Name"}}, "position_key"),
            ({"pagination": {"mode": "page_index", "max_pages": 0}}, "max_pages"),
        ]
        for patch, message in cases:
            with self.subTest(patch=patch), self.assertRaisesRegex(ValueError, message):
                JsonApiSourceAdapter.validate_source_config(
                    make_api_source(merge_config(BASE_CONFIG, patch))
                )

Also assert "api" in OfficialSource.SourceType.values.

- [ ] **Step 2: Verify RED**

Run: python manage.py test radar.tests.test_json_api_adapter -v 2

Expected: failure because the API type/module/validator does not exist.

- [ ] **Step 3: Implement the minimal type and validator**

Add API = "api", "官方招聘接口". Generate the migration with python manage.py makemigrations radar --name officialsource_api_source_type. In JsonApiSourceAdapter.validate_source_config, require a dict; HTTPS endpoint; GET/POST; non-empty list_path; a notice dict with non-empty identity/title/official URL/recruitment type/target audience; non-empty field_map.position_key and field_map.title; pagination.mode == "page_index"; positive page_size and max_pages <= 100; and non-negative request_delay_seconds (default 1).

- [ ] **Step 4: Verify GREEN**

Run: python manage.py test radar.tests.test_json_api_adapter -v 2

Expected: every configuration test passes.

- [ ] **Step 5: Commit**

    git add radar/models.py radar/migrations/0010_officialsource_api_source_type.py radar/collectors/json_api.py radar/tests/test_json_api_adapter.py
    git commit -m "feat: add JSON API source contract"

### Task 2: Fetch canonical bounded pages

**Files:**

- Modify: radar/collectors/json_api.py
- Modify: radar/tests/test_json_api_adapter.py

**Interfaces:**

- Produces fetch(source) -> FetchedPage.
- FetchedPage.body is canonical JSON: {"positions":[...],"positions_complete":bool}.

- [ ] **Step 1: Write failing fetch tests**

Patch radar.collectors.json_api.requests.Session.request and time.sleep. Give the first page {"Data":{"Count":3,"Posts":[{"PostId":"1"},{"PostId":"2"}]}} and second {"Data":{"Count":3,"Posts":[{"PostId":"3"}]}}. Assert three aggregated rows, two requests, one sleep(0), and positions_complete=True. Add a test which reverses response dictionary key order and asserts identical content_hash. Add a cap test with max_pages=1 and a non-empty first page asserting positions_complete=False.

- [ ] **Step 2: Verify RED**

Run the three named fetch tests in radar.tests.test_json_api_adapter.

Expected: they fail because fetch has not created canonical aggregate JSON.

- [ ] **Step 3: Implement request and pagination helpers**

Implement _path_value(payload, path, default=None), walking dotted dictionary paths and returning default at a missing segment. Implement _canonical_json(value) with json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).

For each page, copy configured params, add page/size arguments, and use Session.request(method, endpoint, params=request_values, headers=headers, timeout=15) for GET or Session.request(method, endpoint, json=request_values, headers=headers, timeout=15) for POST. Reject status >= 400, require a JSON list at list_path, append rows, and stop on empty list, aggregate size reaching total_path, or max_pages. Sleep only before another request. Set completeness false only when a non-empty sequence reached the configured cap before the total/empty stop. Return FetchedPage with canonicalize_url(endpoint) and SHA-256 over canonical body.

- [ ] **Step 4: Verify GREEN and commit**

Run the Task 2 test command. Then:

    git add radar/collectors/json_api.py radar/tests/test_json_api_adapter.py
    git commit -m "feat: fetch bounded JSON API pages"

### Task 3: Extract one notice with JSON evidence

**Files:**

- Modify: radar/collectors/json_api.py
- Modify: radar/tests/test_json_api_adapter.py
- Create: radar/tests/fixtures/json_api_page.json

**Interfaces:**

- Produces extract(source, page) -> list[NoticeCandidate] containing exactly one candidate.
- Each retained position has JSON Path locators and evidence values accepted by existing evidence checks.

- [ ] **Step 1: Write failing extraction tests**

Use a fixture with two valid posts and rows with blank PostId and IsValid="False". Configure valid_values={"is_valid":["True", True]} and fields PostId, RecruitPostName, LocationName, Responsibility, PostURL, and LastUpdateTime. Assert candidate identity tencent-campus-2027, two positions, locator $.Data.Posts[0].RecruitPostName, and published_on=date(2026, 8, 20). Add a malformed date assertion returning None, and assert blank/invalid rows are absent.

- [ ] **Step 2: Verify RED**

Run the named extraction tests. Expected: failures because no candidate/evidence extraction is implemented.

- [ ] **Step 3: Implement conversion and evidence**

Parse canonical FetchedPage.body. For each original list index, evaluate optional valid_values against the configured field; skip blank stringified position keys; map optional values to empty string/None; and build PositionCandidates. Locators must be $.<list_path>[<index>].<mapped-field>, such as $.Data.Posts[0].RecruitPostName. Build FieldEvidenceValue(str(raw), locator, parsed) for title/location/application URL when present. Build one notice from the fixed notice mapping, with evidence for title, recruitment type, target audience, published date, deadline, and official notice URL. Parse Chinese YYYY年M月D日 via full-match regex; return None on bad input. Set positions_complete solely from canonical body.

- [ ] **Step 4: Verify GREEN and commit**

Run the Task 3 test command. Then:

    git add radar/collectors/json_api.py radar/tests/test_json_api_adapter.py radar/tests/fixtures/json_api_page.json
    git commit -m "feat: extract JSON API recruitment notices"

### Task 4: Register JSON API and add HTML multi-position support

**Files:**

- Modify: radar/collectors/registry.py
- Modify: radar/collectors/html.py
- Modify: radar/tests/test_collection.py
- Modify: radar/tests/test_json_api_adapter.py

**Interfaces:**

- AdapterRegistry.get(source) returns JsonApiSourceAdapter when adapter_name="json_api".
- Existing HTML configs may optionally provide position_selector.

- [ ] **Step 1: Write failing integration tests**

Assert isinstance(AdapterRegistry.get(make_api_source(BASE_CONFIG, adapter_name="json_api")), JsonApiSourceAdapter). Add an HTML fixture containing one notice with two descendant .position elements, each with a stable ID, title, location, and link. Configure position_selector=".position" and assert both identities are extracted. Keep and run the existing no-position_selector test to prove legacy one-position behavior stays unchanged.

- [ ] **Step 2: Verify RED**

Run focused registry and multi-position tests. Expected: an unregistered adapter error and a single extracted position.

- [ ] **Step 3: Implement integration**

Add "json_api": JsonApiSourceAdapter to the existing registry without altering other entries. In the HTML extractor, choose node.select(config["position_selector"]) when configured, otherwise [node]. Extract position-level values and identity from each selected node while retaining notice-level fields and locators at the notice node. Skip malformed selected positions. Do not make position_selector required; existing source configurations remain valid.

- [ ] **Step 4: Verify GREEN and commit**

Run focused tests and python manage.py test radar.tests.test_collection -v 2. Then:

    git add radar/collectors/registry.py radar/collectors/html.py radar/tests/test_collection.py radar/tests/test_json_api_adapter.py
    git commit -m "feat: register JSON API collector"

### Task 5: Full verification and delivery report

**Files:**

- Create: work/phase-02-01-json-api-adapter-report.md

- [ ] **Step 1: Run acceptance checks**

    python manage.py makemigrations --check --dry-run
    python manage.py check
    python manage.py test radar.tests -v 2

Expected: no migration drift, zero Django check issues, no live requests, and a passing test count greater than 102.

- [ ] **Step 2: Write the report**

The report must list all changed files; state the HTML compatibility result; define positions_complete=True only for empty-list/total-reached completion and false for cap truncation/page failure; include exact validation results; and state either None or each approved deviation with its reason.

- [ ] **Step 3: Final diff review and commit**

    git diff --check
    git status --short
    git add work/phase-02-01-json-api-adapter-report.md
    git commit -m "docs: report JSON API adapter implementation"

## Plan Self-Review

- Tasks 1-4 cover the source type/migration, validator, GET/POST config, bounded pagination, canonical hash, dotted paths, one-notice grouping, evidence locators, filtering, dates, registry, and optional HTML multi-position behavior.
- Task 5 covers the report, no-network checks, migration consistency, and full-suite acceptance.
- City changes and real-source onboarding remain deferred; no protected gate is modified.
