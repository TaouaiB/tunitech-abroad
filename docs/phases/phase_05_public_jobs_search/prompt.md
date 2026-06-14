# Phase 5 — Public Job Search and Pages — Agent Prompt

You are implementing Phase 5 for TuniTech Abroad.

## Role

You are a coding agent working inside the existing Django repository. Implement only the current phase. Follow `AGENTS.md` and the phase files exactly.

## Read first

Read these files before coding:

- `AGENTS.md`
- `docs/phases/phase_05_public_jobs_search/tasks.md`
- `docs/phases/phase_05_public_jobs_search/prompt.md`
- `docs/phases/phase_05_public_jobs_search/acceptance.md`
- `docs/phases/phase_05_public_jobs_search/agent_report_template.md`
- `docs/phases/phase_04_job_ingestion_normalization/agent_report.md`

## Mission

Implement public job browsing from local PostgreSQL.

You must create:

- `JobSearchService`
- `JobQueryService`
- `JobRevalidationService` safe shell
- `/jobs/` public job list/search page
- `/jobs/<uuid:public_id>/` public job detail page
- job search form
- job templates/cards
- filters
- pagination
- search/detail tests

## Architecture rules

Strictly follow the TuniTech Abroad architecture:

- Django only
- Django ORM only
- Django templates
- HTMX optional only as progressive enhancement
- Tailwind-compatible templates
- views stay thin
- business logic goes in services
- services use local PostgreSQL only
- public job URLs use `public_id`, never internal integer IDs
- no live France Travail API calls during search/detail normal flow
- no external API calls in tests
- no LLM/OpenRouter calls

## Hard boundary

Do not start Phase 6 or later.

Forbidden:

- CV upload/parsing
- candidate CV profile extraction
- matching / quick-match calculation
- recommendations
- saved jobs model or save/unsave endpoint
- email digest / unsubscribe
- privacy deletion flows
- LLM/OpenRouter
- React, Next.js, Angular, FastAPI, SQLAlchemy, MongoDB, SPA
- public internal-id job routes

Allowed placeholder only:

- A disabled/non-functional CTA saying a feature is coming later.

Do not implement the feature behind that CTA.

## Implementation guidance

### Services

Create or update:

- `apps/jobs/services/search.py`
- `apps/jobs/services/query.py`
- `apps/jobs/services/revalidation.py`

Search service should use the Phase 4 normalized jobs and PostgreSQL full-text search/search vector where available.

Query service must retrieve jobs by UUID `public_id`.

Revalidation service must be safe no-op by default.

### Forms

Create:

- `apps/jobs/forms.py`

Use a simple Django form for public query params. Keep validation forgiving.

### Views and URLs

Create/update:

- `apps/jobs/views.py`
- `apps/jobs/urls.py`
- root URL include

Routes:

- `/jobs/` name `jobs:list`
- `/jobs/<uuid:public_id>/` name `jobs:detail`

No integer job detail route.

### Templates

Create:

- `templates/jobs/job_list.html`
- `templates/jobs/job_detail.html`
- `templates/jobs/partials/job_card.html`

Optional:

- `templates/jobs/partials/job_results.html`
- `templates/jobs/partials/job_filter_panel.html`

Templates must work for anonymous users.

### Events

If the existing analytics `UserEventService` supports this safely, record:

- `job_search`
- `job_detail_view`

Wrap event recording so failures never break public pages.

## Required checks

Before final report, run:

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

Then run:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

## Diagnostics gate

Before final report:

- open changed Python files in the IDE
- confirm no red diagnostics remain
- do not claim clean if red diagnostics remain

## Final report

Create:

- `docs/phases/phase_05_public_jobs_search/agent_report.md`

Use the template:

- `docs/phases/phase_05_public_jobs_search/agent_report_template.md`

The report must be truthful. Do not say tests passed unless they actually passed.

## Git behavior

Do not commit.
Do not merge.
Do not push.

The user will review before committing.
