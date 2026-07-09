# Phase 16B — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening — tasks.md

## Goal

Explain and fix low automatic job inventory, make ingestion configurable, harden freshness/search, and remove France-only public copy.

## In-scope apps/areas

```text
jobs ingestion/config/freshness/search/forms/services/commands/admin
audit/search logging
core/templates public copy
```

## Tickets

### TTA-16B-001 — Diagnose job count discrepancy

Priority: P0  
Type: diagnostics/service/command/admin

Add:

```bash
python manage.py diagnose_job_ingestion --settings=config.settings.production
```

Acceptance:

```text
Output explains fetched -> raw -> normalized -> active -> public_visible -> matchable.
Latest ingestion runs visible.
Per-query counts visible.
Normalization status counts visible.
Skill extraction status counts visible.
Freshness status counts visible.
Public eligibility/hide reasons visible.
Warnings explain why automatic production shows 100-200 when manual showed ~1000.
Uses shared diagnostics dict contract.
```

### TTA-16B-002 — Configurable ingestion limits

Priority: P0  
Type: model/service/admin/test

Admin configurable fields:

```text
target_daily_fetch_count default 1000
max_jobs_per_run
max_pages_per_query
page_size
queries_json
stale_after_hours
removed_after_hours
expire_grace_hours
```

Acceptance:

```text
If JobIngestionConfig exists, extend it; do not duplicate config model.
Admin can update config.
Scheduled ingestion reads config through service.
target_daily_fetch_count is treated as target/limit, not fake guarantee.
System reports when source/config returns fewer than target.
Config snapshot is stored for run diagnostics.
```

### TTA-16B-003 — Query-level ingestion run tracking

Priority: P0  
Type: model/service/task/admin/test

Acceptance:

```text
Each configured query records fetched/created/updated/unchanged/skipped/error counts.
Each query records params/range used.
Admin can identify which query underperforms.
Partial query failures do not destroy whole run if other queries succeed.
```

### TTA-16B-004 — Freshness/expiry hardening

Priority: P0  
Type: service/test/production-safety

Required ordering:

```python
if expires_at and expires_at < now - expire_grace:
    status = "expired"
elif last_seen_at and last_seen_at < now - removed_after:
    status = "removed"
elif last_seen_at and last_seen_at < now - stale_after:
    status = "stale"
else:
    status = "active"
```

Acceptance:

```text
Failed ingestion run does not mass-stale jobs.
Failed ingestion run does not mass-remove jobs.
Removed threshold wins over stale threshold.
Date-only expiry uses end of day plus grace.
Missing expires_at uses last_seen_at thresholds.
Tests cover edge cases.
Before/after active job counts are captured for rollout.
```

### TTA-16B-005 — Search hardening

Priority: P0  
Type: service/form/test

Acceptance:

```text
/jobs/?q=%20%20%20 behaves like /jobs/ and returns active jobs.
Empty q returns active jobs.
Multi-space q is normalized.
Invalid filters do not 500.
Anonymous best-match sort falls back safely.
Page below 1 becomes page 1.
Page too high does not crash.
No search path calls external API.
```

### TTA-16B-006 — Company and published date filters

Priority: P0  
Type: service/form/frontend/test

Add filters:

```text
company
published_exact
published_from
published_to
```

Acceptance:

```text
Company filter matches company_name.
Space-only company ignored.
published_exact applies same-day range and takes precedence over from/to.
published_from/to apply start/end of day range.
Invalid date handled safely with no 500.
Pagination preserves filters.
```

### TTA-16B-007 — Search logs and audit

Priority: P1  
Type: analytics/service/command/admin/test

Add:

```bash
python manage.py audit_job_search --settings=config.settings.production
```

Acceptance:

```text
SearchQueryLog or equivalent records raw/normalized query, company, filters, result_count, user/session hash.
Search logging failure does not break search.
Audit reports top searches, zero-result searches, whitespace searches, invalid filters, company filters, skill queries.
Uses shared diagnostics dict contract.
```

### TTA-16B-008 — Country-neutral public UI

Priority: P1  
Type: frontend/content/command/test

Acceptance:

```text
Public marketing/product UI no longer says France-only or France-first.
Job location can still show France as source data.
Admin/internal/source config can still say France Travail/France.
No public country dropdown yet.
audit_public_copy command detects forbidden public phrases.
```

## Interim production safety before Phase 16G alerts

Until Phase 16G alerting exists, deployment of 16B must include manual before/after checks:

```text
active job count before deploy
public visible job count before deploy
matchable job count before deploy
same counts after deploy
same counts after next ingestion/freshness run
```

Stop and rollback if active/public visible jobs drop unexpectedly.

## Out of scope

```text
No CV parser work.
No skill taxonomy overhaul beyond search alias consumption.
No matching formula changes.
No multi-country selector.
No full UI redesign.
```
