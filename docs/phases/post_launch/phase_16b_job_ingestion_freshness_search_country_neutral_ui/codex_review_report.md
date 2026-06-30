# Codex Verification Report — Phase 16B — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening

## 1. Summary

```text
Status: PASS
Branch: dev
Commit/hash if available: not committed
```

Codex reviewed Gemini's Phase 16B implementation against the post-launch rules, shared diagnostics contract, and Phase 16B acceptance criteria. I repaired in-scope gaps in query-level ingestion tracking, diagnostics shape, freshness semantics, search audit fields, admin visibility, public-copy audit service placement, and test coverage.

## 2. Tickets completed

```text
- TTA-16B-001: PASS — diagnose_job_ingestion reports fetched -> raw -> normalized -> active -> public_visible -> public_matchable with status and reason buckets.
- TTA-16B-002: PASS — admin-configurable ingestion/freshness limits exist, scheduled ingestion uses them, and legacy default rows are upgraded by migration.
- TTA-16B-003: PASS — JobIngestionQueryRun records per-query fetched/created/updated/unchanged/skipped/error counts and requested ranges.
- TTA-16B-004: PASS — freshness ordering is explicit, failed latest ingestion aborts mass status changes, removed wins over stale, date-only expiry uses end-of-day plus grace.
- TTA-16B-005: PASS — empty/whitespace query returns active jobs, invalid filters are safe, pagination is safe, no external API calls in search.
- TTA-16B-006: PASS — company and published exact/from/to filters work and are covered by tests.
- TTA-16B-007: PASS — SearchQueryLog and audit_job_search report searches, zero-result searches, whitespace searches, invalid filters, company filters, and skill queries.
- TTA-16B-008: PASS — public copy audit passes; France remains allowed only as source/job data.
```

## 3. Files changed

```text
Modified:
- apps/jobs/admin.py
- apps/jobs/forms.py
- apps/jobs/models.py
- apps/jobs/services/freshness.py
- apps/jobs/services/ingestion.py
- apps/jobs/services/search.py
- apps/jobs/tests/test_14f_automated_it_ingestion.py
- apps/jobs/tests/test_14j_observability.py
- apps/jobs/tests/test_services.py
- apps/jobs/tests/test_services_search.py
- apps/jobs/tests/test_views.py
- apps/jobs/views.py
- templates/account/login.html
- templates/account/signup.html
- templates/base.html
- templates/core/home.html
- templates/dashboard/profile.html
- templates/jobs/job_list.html
- templates/jobs/partials/job_filter_panel.html

Created:
- apps/core/management/commands/audit_public_copy.py
- apps/core/services/public_copy_audit.py
- apps/jobs/management/commands/audit_job_search.py
- apps/jobs/management/commands/diagnose_job_ingestion.py
- apps/jobs/migrations/0007_jobingestionconfig_expire_grace_hours_and_more.py
- apps/jobs/migrations/0008_jobingestionqueryrun_and_more.py
- apps/jobs/migrations/0009_update_phase_16b_default_config_values.py
- apps/jobs/services/diagnostics.py
- apps/jobs/services/search_audit.py
- docs/phases/post_launch/phase_16b_job_ingestion_freshness_search_country_neutral_ui/codex_review_report.md
```

## 4. Migrations

```text
- apps/jobs/migrations/0007_jobingestionconfig_expire_grace_hours_and_more.py
- apps/jobs/migrations/0008_jobingestionqueryrun_and_more.py
- apps/jobs/migrations/0009_update_phase_16b_default_config_values.py
```

Migration notes:

```text
- 0007 adds Gemini's initial Phase 16B config/search log fields.
- 0008 adds JobIngestionQueryRun, missing search audit fields, indexes, and documented default alterations.
- 0009 upgrades existing config rows that still have Gemini's old default values; reverse is no-op to avoid mutating admin-configured production values on rollback.
```

## 5. Commands run

```bash
python manage.py check --settings=config.settings.local
# PASS — System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
# PASS — No changes detected.

python manage.py migrate --settings=config.settings.local
# PASS — applied jobs.0007, jobs.0008, jobs.0009 locally.

python manage.py diagnose_job_ingestion --settings=config.settings.local
# PASS — produced shared-contract JSON with raw_total=1160, normalized_total=1160, active=258, public_visible=241, public_matchable=241 in the local DB.

python manage.py audit_job_search --settings=config.settings.local
# PASS — produced shared-contract JSON; local DB currently has total_searches=0.

python manage.py audit_public_copy --settings=config.settings.local
# PASS — No forbidden phrases found in public templates.

python manage.py test apps.jobs.tests.test_services_search apps.jobs.tests.test_services apps.jobs.tests.test_14j_observability --settings=config.settings.local
# PASS — 49 tests.

python manage.py test apps.jobs.tests.test_services_search apps.jobs.tests.test_views --settings=config.settings.local
# PASS — 41 tests.

python manage.py test --settings=config.settings.local
# PASS — 567 tests.
```

Production-only commands not run locally:

```bash
python manage.py diagnose_job_ingestion --settings=config.settings.production
python manage.py audit_job_search --settings=config.settings.production
```

## 6. Tests

```text
passed: 567
failed: 0
skipped: 0
```

New/strengthened coverage:

```text
- whitespace-only search behaves like empty search
- company and published date filters
- invalid date safety
- search audit flags for whitespace and invalid filters
- skill alias search consumption
- failed ingestion freshness abort
- date-only expiry end-of-day plus grace
- query-level ingestion run counts
```

## 7. Manual/browser checks

```text
Not run in browser. Covered by template/view tests and audit_public_copy.
Production before/after active/public/matchable count capture remains a deployment manual step.
```

## 8. Architecture compliance

```text
views thin: yes
services own logic: yes
Celery tasks thin: yes
models do not call external APIs: yes
no live external job API during user search: yes
public_id preserved: yes
CV privacy preserved: yes
no raw CV text or secrets logged: yes
admin-only features protected by Django admin/management command access: yes
no fake enterprise RBAC: yes
phase boundary respected: yes
```

## 9. Risks / follow-ups

```text
- Existing historical local ingestion runs have empty query_runs because query-level rows only exist after this phase is deployed.
- Production deployment must capture active/public_visible/public_matchable counts before deploy, after deploy, and after the next ingestion/freshness run.
- Production diagnostics commands need to be run on the server after migrations.
```

## 10. Intent-preserving fixes

```text
- Replaced query_stats_json-only tracking with JobIngestionQueryRun while keeping query_stats_json for compatibility.
- Corrected Phase 16B defaults and added data migration for rows using Gemini's old defaults.
- Made scheduled ingestion use target_daily_fetch_count/max_jobs_per_run/max_pages_per_query/page_size instead of hard-coded reduced caps.
- Made freshness expiry logic explicit and safe for failed latest ingestion runs.
- Added missing search audit fields and safe logging.
- Moved public copy audit logic into a service and kept the management command thin.
- Added tests for Phase 16B acceptance behavior.
```

## 11. Intent-changing fixes or disagreements

```text
none
```

## 12. Ready for senior review

```text
yes
```
