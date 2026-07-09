# Boundaries — Phase 14F

## Architecture rules

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data and do not call external APIs.
- No France Travail live API calls during normal user job search.
- No OpenRouter/LLM calls from Django views.
- User job search reads local PostgreSQL only.
- Public URLs use UUID `public_id`, never internal IDs.
- CV files are private and must never be exposed.
- Do not use React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.

## Ingestion rules

- The existing `sync_france_travail_jobs` command may remain safe/capped for smoke testing.
- Add a new dedicated command for broad IT ingestion.
- The new command must not silently cap explicit admin limits at 10.
- The new command must have visible safety limits: `limit_per_keyword`, `max_total`, and `max_pages_per_keyword`.
- Never run unbounded API loops.
- Never call France Travail from `/jobs/`, `/dashboard/recommendations/`, match detail, or any user-facing request path.

## Enrichment rules

- Every fetched active normalized IT job should be queued for enrichment by default.
- Do not call LLM synchronously from views.
- Do not use LLM to calculate final fit score.
- Use existing `JobEnrichment` service/tasks from Phase 14D.
- Respect feature flags and admin config.
- Use payload hash to avoid repeated enrichment for unchanged jobs.

## Production/Render rules

- Phase 14F must work locally with management commands.
- It must be scheduler-ready for Render Cron Job or Celery Beat.
- It must not require storing secrets in code.
- Do not assume Render paid-only pre-deploy commands.
