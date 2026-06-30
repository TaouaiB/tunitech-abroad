# Acceptance — Phase 14F

Phase 14F is acceptable only when all are true:

## Ingestion

- New command `sync_france_travail_it_jobs` exists.
- Existing `sync_france_travail_jobs` can remain capped/safe.
- New command does not silently cap explicit limits at 10.
- Default `limit_per_keyword` is 50.
- Default `max_total_per_run` is 1000.
- Nightly default max total is 2000.
- Broad IT preset covers multiple IT families.
- Pagination works up to visible limits.
- Deduplication by source job ID works.
- Normalization runs after fetch when enabled.

## Enrichment

- By default, every fetched active normalized eligible IT job is queued for enrichment.
- Existing successful enrichment with same payload hash is not repeated.
- Pending/processing enrichment is not duplicated.
- Admin/config can disable enrichment.
- LLM is never called from views.

## Expiry

- Stale jobs can be marked inactive automatically.
- Public search/recommendations exclude inactive jobs.
- Raw records remain available for audit.

## Admin/control

- Admin can edit ingestion config.
- Admin can lower frequency/limits.
- Admin can disable sync.
- Admin can disable enrichment.
- Ingestion run logs are visible in admin.

## Automation

- A Celery task or cron-ready command exists.
- It can run without user interaction.
- It is safe for Render Cron / local cron / Celery Beat.

## Architecture

- No France Travail live API in public search/recommendation pages.
- No LLM in views.
- Views stay thin.
- Services own logic.
- Tasks call services.
- Tests pass.
- No secrets printed.

## Manual proof examples

The report must show example output for:

```bash
python manage.py sync_france_travail_it_jobs --preset broad_it --limit-per-keyword 50 --max-total 1000 --normalize --enqueue-enrichment --dry-run
python manage.py sync_france_travail_it_jobs --preset broad_it --limit-per-keyword 5 --max-total 20 --normalize --enqueue-enrichment
python manage.py expire_stale_jobs --days 21 --dry-run
```

Final verdict must be `BLOCKED_HUMAN_VISUAL_SIGNOFF` if all code/tests pass but Baha has not manually approved in Chrome/admin.
