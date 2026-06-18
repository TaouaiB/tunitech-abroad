Read this entire prompt and execute it exactly.

# Phase 14F — Automated France Travail IT Ingestion

## Mission

Build the automatic job inventory layer for TuniTech Abroad.

Users must not depend on manual commands to see jobs. The app must be able to fetch broad France IT jobs from France Travail, normalize them, queue LLM enrichment, expire stale jobs, and keep public search/recommendations reading local PostgreSQL only.

## Product defaults required by Baha

Default values must be:

```text
limit_per_keyword = 50
max_total_per_run = 1000
nightly_max_total = 2000
enqueue_enrichment = True
enrich_every_fetched_it_job = True
```

Admin must be able to reduce/increase these later.

“Every fetched job is enriched” means every fetched active normalized eligible IT job must get enrichment queued by default, unless it already has successful enrichment for the same payload hash, is already pending/processing, or enrichment is globally disabled.

Do not enrich obvious non-IT garbage intentionally.

## Current known blocker

Existing command `sync_france_travail_jobs` has a safe cap:

```python
actual_limit = min(limit, 10)
```

Do not simply remove this from the old command. Add a new dedicated broad IT command that has visible admin safety limits instead of a hidden cap.

## Hard rules

- Do not commit.
- Do not deploy.
- Do not start Phase 14G.
- Do not edit real `.env`.
- Do not print secrets.
- No React/Next/Angular/FastAPI/MongoDB/SQLAlchemy/SPA.
- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- No France Travail live API calls from user-facing views/search/recommendations.
- No LLM calls from Django views.
- Final match score remains deterministic.
- CV privacy rules remain untouched.
- Existing Phase 14D enrichment should be reused, not duplicated.

Final verdict must be only `FAIL` or `BLOCKED_HUMAN_VISUAL_SIGNOFF`.

## Implement

### 1. Models/admin

Add admin-configurable models:

- `JobIngestionConfig`
- `JobIngestionRun`

Use defaults from this prompt.
Register in Django admin.
Create migrations.

### 2. Broad IT preset

Add `broad_it` preset with broad IT keyword coverage from `broad_it_preset.md`.

### 3. Ingestion service

Create a service that:

- takes config/overrides;
- loops through broad IT keywords;
- calls France Travail client;
- paginates;
- stops at `limit_per_keyword`, `max_total`, and `max_pages_per_keyword`;
- deduplicates source job IDs across keywords;
- saves/updates `RawJobRecord`;
- normalizes to `NormalizedJob` when enabled;
- records counts in `JobIngestionRun`;
- records errors without crashing the whole run if one keyword fails.

### 4. Management command

Add:

```bash
python manage.py sync_france_travail_it_jobs --preset broad_it --limit-per-keyword 50 --max-total 1000 --normalize --enqueue-enrichment
```

Required options:

- `--config default`
- `--preset broad_it`
- `--limit-per-keyword`
- `--max-total`
- `--max-pages-per-keyword`
- `--normalize`
- `--enqueue-enrichment`
- `--no-enrichment`
- `--expire-stale`
- `--dry-run`

Optional local test option:

- `--sync-enrichment` only for explicitly small local testing.

### 5. Enrichment queueing

After a job is fetched and normalized, queue enrichment by default if:

- job is active;
- job is likely IT/enrichment-eligible;
- enrichment is enabled;
- no successful enrichment exists for the same payload hash;
- no pending/processing enrichment exists;
- run enrichment limit not exceeded.

Use existing Phase 14D `JobEnrichment`, service, and Celery task.
Do not call LLM directly from ingestion command unless explicit `--sync-enrichment` is used for small local tests.

### 6. Expiry

Add `JobExpiryService` and command or command option.

Rules:

- mark stale/expired jobs inactive;
- do not hard delete by default;
- keep raw records;
- exclude inactive jobs from public search/recommendations.

### 7. Celery task / scheduler-ready

Add a Celery task that runs ingestion from config.

If Celery Beat exists, add schedule in a safe way. If not, document Render Cron command in phase docs/report.

Do not require paid Render pre-deploy features.

### 8. Tests

Implement tests from `test_plan.md`.

### 9. Report

Create `docs/phases/phase_14f_automated_it_ingestion/agent_report.md` using the template.

## Required checks

Run all checks in `regression_security_checks.md` and report results.

## Acceptance

Use `acceptance.md` as the acceptance source.

Remember: do not commit, do not deploy, and final verdict cannot be PASS.
