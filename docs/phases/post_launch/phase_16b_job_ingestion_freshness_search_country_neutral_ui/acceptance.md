# Phase 16B — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening — acceptance.md

## General acceptance

```text
All tickets in tasks.md are complete or explicitly deferred with reason.
No next-phase work was implemented.
No stack changes.
Service-layer boundary preserved.
Tests pass or failures are documented and clearly unrelated.
No secrets, raw CV text, OAuth tokens, API keys, or private file paths are logged.
```

## Required checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Phase-specific acceptance

```text
diagnose_job_ingestion exists and explains fetched -> raw -> normalized -> active -> public visible -> matchable.
Admin can configure target_daily_fetch_count default 1000.
Freshness does not mass-stale/remove after failed ingestion.
Whitespace-only search returns active jobs.
Company filter works.
Published exact/from/to filters work.
audit_job_search exists.
audit_public_copy exists and allows France only as job/source data.
```
