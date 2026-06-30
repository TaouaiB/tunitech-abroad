# Phase 5 — Public Job Search and Pages — Tasks

## Phase goal

Expose public job browsing from the local PostgreSQL database.

Phase 5 turns the Phase 4 normalized job data into public, usable pages:

- `/jobs/` public job list/search page
- `/jobs/<uuid:public_id>/` public job detail page
- service-based local PostgreSQL search
- filters, sorting, pagination, and job cards
- detail lookup by UUID `public_id`
- safe job revalidation shell only

This phase must not implement CV parsing, matching, recommendations, saved jobs, LLM, email, or privacy deletion.

## Required source documents

Before implementation, read:

- `AGENTS.md`
- `docs/phases/phase_05_public_jobs_search/tasks.md`
- `docs/phases/phase_05_public_jobs_search/prompt.md`
- `docs/phases/phase_05_public_jobs_search/acceptance.md`
- Phase 4 report: `docs/phases/phase_04_job_ingestion_normalization/agent_report.md`

## Existing dependencies

Expected completed before this phase:

- Phase 0 repository/local environment
- Phase 1 auth foundation
- Phase 2 core profile/admin models
- Phase 3 skill taxonomy
- Phase 4 job ingestion and normalization

Phase 5 depends on `apps.jobs.models.NormalizedJob`, `JobSource`, `NormalizedJobSkill`, and Phase 4 fixture ingestion being complete.

## Hard phase boundary

Allowed in Phase 5:

- public job search views
- public job detail view
- `apps/jobs/urls.py`
- `apps/jobs/views.py`
- `apps/jobs/forms.py`
- `apps/jobs/services/search.py`
- `apps/jobs/services/query.py`
- `apps/jobs/services/revalidation.py`
- job templates under `templates/jobs/`
- pagination and filters
- local PostgreSQL search only
- safe event recording using existing analytics service if available
- tests for service, view, routing, filters, pagination, UUID detail, and no external API calls

Forbidden in Phase 5:

- CV upload/parsing
- matching or quick-match calculations
- recommendations
- saved jobs data model or save/unsave behavior
- OpenRouter or LLM calls
- email digest or unsubscribe
- privacy deletion workflows
- live France Travail API calls during normal search
- React, Next.js, Angular, FastAPI, SQLAlchemy, MongoDB, SPA architecture
- exposing internal integer IDs in public URLs
- using job internal `id` in public detail links

## Tickets

---

## TTA-0501 — Implement `JobSearchService`

### Goal

Create a service that searches local PostgreSQL normalized jobs using safe filters and pagination.

### File

Create or update:

- `apps/jobs/services/search.py`

### Required behavior

`JobSearchService.search(filters: dict, user=None) -> PaginatedJobResult`

The service must:

- query only local PostgreSQL
- never call France Travail or any external API
- default to active/visible jobs only
- support query text search
- support filters:
  - `q`
  - `location`
  - `contract_type`
  - `job_type`
  - `remote_type`
  - `experience_level`
  - `skill`
  - `page`
  - `page_size`
  - `sort`
- support pagination
- support sort options:
  - `newest`
  - `relevance`
  - `company`
- fallback safely when sort is unknown
- avoid large unbounded result sets
- return a structured result object usable by templates

### PostgreSQL full-text search

Use PostgreSQL full-text search where available. Do not rely on broad description-only `icontains` as the main search mechanism.

Expected weighting concept:

- title = A
- required skills = A
- optional skills = B
- company = B
- location = C
- description = D

If Phase 4 already maintains `search_vector`, use it. If not, use Django PostgreSQL search tools in the query service. Do not add external search engines.

### Suggested result dataclass

```python
@dataclass(frozen=True)
class PaginatedJobResult:
    page_obj: Page
    paginator: Paginator
    filters: dict[str, str]
    total_count: int
    sort: str
```

Adjust names if needed, but keep result explicit.

### Tests

Create/extend tests in `apps/jobs/tests/`:

- search returns matching active jobs
- expired/inactive/removed jobs are hidden by default
- filters work
- pagination works
- unknown sort falls back safely
- no external API/client is called

---

## TTA-0502 — Implement `JobQueryService`

### Goal

Centralize safe public job retrieval by UUID `public_id`.

### File

Create:

- `apps/jobs/services/query.py`

### Required behavior

`JobQueryService.get_public_job(public_id) -> NormalizedJob`

The service must:

- retrieve by `public_id`
- never retrieve public detail by internal integer id
- only return jobs allowed for public display
- raise `Http404` or `NormalizedJob.DoesNotExist` consistently for missing/private jobs
- use `select_related`/`prefetch_related` where useful

### Tests

- known `public_id` returns job
- unknown UUID returns 404/not found
- inactive/removed job does not return publicly
- no internal integer route exists

---

## TTA-0503 — Build public job search page

### Goal

Create a public `/jobs/` page using Django templates and service-backed search.

### Files

Create/update:

- `apps/jobs/forms.py`
- `apps/jobs/views.py`
- `apps/jobs/urls.py`
- project root `config/urls.py` or equivalent include
- `templates/jobs/job_list.html`
- `templates/jobs/partials/job_card.html`
- optional `templates/jobs/partials/job_results.html`
- optional `templates/jobs/partials/job_filter_panel.html`

### Required behavior

- `GET /jobs/` returns 200 for anonymous users
- search form visible
- job cards visible when data exists
- filters visible
- pagination visible when needed
- list view calls `JobSearchService.search()`
- view stays thin
- no external API call
- no user-specific matching logic
- job links use `public_id`

### HTMX

HTMX partials are allowed but optional. If used, keep progressive enhancement: page must work without HTMX.

### Tests

- anonymous user can access `/jobs/`
- search query filters result
- filters preserve query parameters
- pagination works
- generated links use UUID public_id, not internal integer id

---

## TTA-0504 — Build public job detail page

### Goal

Create `/jobs/<uuid:public_id>/` public detail page.

### Files

Create/update:

- `apps/jobs/views.py`
- `apps/jobs/urls.py`
- `templates/jobs/job_detail.html`

### Required behavior

Detail page shows:

- title
- company
- location
- contract type
- job type
- remote type
- experience level
- description
- required skills
- optional skills
- language requirements if present
- job freshness/status label
- source/apply link if available

Detail page must:

- load by UUID `public_id`
- never load by internal integer id
- call `JobQueryService.get_public_job()`
- call `JobRevalidationService.revalidate_if_needed()` shell safely
- optionally record a job detail event
- show placeholder CTAs only if needed, without implementing matching/saved-job behavior

### CTA boundary

You may show non-functional or disabled placeholder CTAs such as:

- “Quick match — coming in Phase 7”
- “Save job — coming later”

Do not create matching forms, save-job endpoints, saved-job models, or recommendation logic.

### Tests

- valid UUID detail returns 200
- unknown UUID returns 404
- internal integer URL does not resolve
- detail template displays core job fields
- stale/expired label appears when relevant

---

## TTA-0505 — Implement `JobRevalidationService` shell

### Goal

Create a safe service shell for future high-intent detail refresh without making live API calls during normal search.

### File

Create:

- `apps/jobs/services/revalidation.py`

### Required behavior

`JobRevalidationService.revalidate_if_needed(job) -> NormalizedJob`

The service must:

- return the existing job by default
- check a configurable/fixed freshness threshold
- never break detail page if revalidation cannot happen
- not call live France Travail by default
- not make HTTP calls in tests
- be ready for future controlled revalidation without adding it now

### Tests

- fresh job returns unchanged
- stale job follows safe no-op path when client is unavailable
- external failure would not break detail page, if a mock client hook exists

---

## TTA-0506 — Record basic search/detail events safely

### Goal

Use the existing analytics/event service if available without making views fat.

### Required behavior

- record `job_search` event when `/jobs/` is loaded or searched
- record `job_detail_view` event when detail page is loaded
- failure to record analytics must not break public pages
- anonymous users must be supported

### Tests

- public pages still return 200 if analytics service raises
- authenticated user events can be recorded if existing service supports it

---

## TTA-0507 — Phase 5 tests and cleanup

### Required tests

Run and pass:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

### Junk checks

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

Expected:

- no `__pycache__`
- no `.pyc`
- no `task.md`
- no SQLite DB
- no Celery Beat runtime files
- no Phase 6+ files
- no review artifacts committed

## Final report

Create:

- `docs/phases/phase_05_public_jobs_search/agent_report.md`

Use:

- `docs/phases/phase_05_public_jobs_search/agent_report_template.md`

Report must include:

- files changed
- services implemented
- routes implemented
- tests run
- search/filter/pagination coverage
- confirmation no external API call occurs during search
- confirmation public URLs use `public_id`
- confirmation no Phase 6+ work
- final `git status --short`
- final `git diff --stat`

