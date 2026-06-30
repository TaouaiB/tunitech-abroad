# Phase 5 — Public Job Search and Pages — Acceptance Criteria

Phase 5 is accepted only when all criteria below pass.

## Scope acceptance

- [ ] `apps/jobs/services/search.py` exists and implements local PostgreSQL job search.
- [ ] `apps/jobs/services/query.py` exists and retrieves public jobs by UUID `public_id`.
- [ ] `apps/jobs/services/revalidation.py` exists as a safe no-op/shell.
- [ ] `/jobs/` exists and is public.
- [ ] `/jobs/<uuid:public_id>/` exists and is public.
- [ ] no public internal integer job detail route exists.
- [ ] templates under `templates/jobs/` exist.
- [ ] job cards link using `public_id`, not internal `id`.
- [ ] Phase 5 does not implement CV, matching, recommendations, saved jobs, LLM, email, or privacy deletion.

## Search acceptance

- [ ] Anonymous users can search jobs.
- [ ] Search reads local PostgreSQL only.
- [ ] Search does not call France Travail live API.
- [ ] Search uses PostgreSQL full-text/search-vector behavior where available.
- [ ] Only active/displayable jobs are shown by default.
- [ ] Expired/removed/inactive jobs are hidden by default.
- [ ] Filters work:
  - [ ] query text
  - [ ] location
  - [ ] contract type
  - [ ] job type
  - [ ] remote type
  - [ ] experience level
  - [ ] skill
- [ ] Pagination works.
- [ ] Unknown/invalid page input is handled safely.
- [ ] Unknown sort input falls back safely.

## Detail acceptance

- [ ] valid `public_id` returns job detail 200.
- [ ] unknown `public_id` returns 404.
- [ ] inactive/removed/private jobs do not load publicly.
- [ ] detail page shows title, company, location, contract/job/remote/experience fields.
- [ ] detail page shows description.
- [ ] detail page shows required/optional skills when available.
- [ ] detail page shows freshness/status label.
- [ ] detail page shows source/apply link when available.
- [ ] revalidation shell cannot break detail page.

## Architecture acceptance

- [ ] views are thin and call services/forms.
- [ ] business logic is in services.
- [ ] no external API calls in search/detail views.
- [ ] no OpenRouter/LLM calls.
- [ ] no React/SPA stack.
- [ ] no raw SQL unless strongly justified.
- [ ] templates are server-rendered Django templates.
- [ ] optional HTMX is progressive only.

## Test acceptance

Required commands must pass:

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

Expected result:

- [ ] all commands pass
- [ ] no pending migrations
- [ ] app tests pass
- [ ] full test suite passes

## Static/IDE acceptance

- [ ] no red diagnostics in changed Python files.
- [ ] no invalid imports.
- [ ] no unused placeholder `task.md`.
- [ ] no stale review artifacts.

## Junk acceptance

These commands must print nothing except expected `git status`/diff output:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
```

Forbidden in final git status:

- `.env`
- `.venv`
- `__pycache__`
- `.pyc`
- `celerybeat-schedule*`
- `task.md`
- review zip/patch/status artifacts
- Phase 6+ files

## Stop/go gate

Do not move to Phase 6 until:

- public job search works
- job detail works by `public_id`
- full test suite passes
- no external API is called in normal search/detail
- senior review approves the package
