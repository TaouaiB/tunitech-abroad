# Codex Senior Repair Report — Phase 16B

Status: PASS

## Files changed

Senior repair pass touched:

- `apps/core/services/public_copy_audit.py`
- `apps/core/test_public_copy_audit.py`
- `apps/jobs/admin.py`
- `apps/jobs/forms.py`
- `apps/jobs/models.py`
- `apps/jobs/services/diagnostics.py`
- `apps/jobs/services/ingestion.py`
- `apps/jobs/services/search.py`
- `apps/jobs/tests/test_14j_observability.py`
- `apps/matching/tests.py`
- `apps/privacy/templates/privacy/terms.html`
- `templates/base.html`
- `templates/core/home.html`
- `templates/dashboard/cv_manage.html`
- `templates/dashboard/profile.html`
- `templates/matching/match_detail.html`
- `templates/recommendations/partials/recommendation_list.html`

The working tree also still contains the broader uncommitted Phase 16B implementation files from the earlier pass.

## Migrations created

- `apps/jobs/migrations/0010_jobingestionrun_config_snapshot_json.py`

## Commands run and results

```bash
python manage.py makemigrations jobs --settings=config.settings.local
# PASS — created jobs.0010_jobingestionrun_config_snapshot_json

python manage.py test apps.jobs.tests.test_14j_observability apps.core.test_public_copy_audit --settings=config.settings.local
# PASS — 19 tests

git diff --check
# PASS

python manage.py check --settings=config.settings.local
# PASS — System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
# PASS — No changes detected.

python manage.py audit_public_copy --settings=config.settings.local
# PASS — No forbidden phrases found in public templates.

python manage.py audit_job_search --settings=config.settings.local
# PASS — shared-contract JSON emitted; local DB total_searches=0.

python manage.py diagnose_job_ingestion --settings=config.settings.local
# FAIL first run — local DB had not applied jobs.0010, missing jobs_jobingestionrun.config_snapshot_json.

python manage.py migrate --settings=config.settings.local
# PASS — applied jobs.0010_jobingestionrun_config_snapshot_json locally.

python manage.py diagnose_job_ingestion --settings=config.settings.local
# PASS — shared-contract JSON emitted with latest_runs[*].config_snapshot.

python manage.py test apps.jobs.tests --settings=config.settings.local
# PASS — 181 tests.

python manage.py test --settings=config.settings.local
# FAIL first run — one stale assertion expected removed France-centric copy.

python manage.py test apps.matching.tests.Phase15GHardeningTests.test_match_detail_removes_scored_location_and_redundant_required_gap_card --settings=config.settings.local
# PASS — 1 test after updating assertion to country-neutral copy.

python manage.py test --settings=config.settings.local
# PASS — 571 tests.

python manage.py test apps.core.test_public_copy_audit --settings=config.settings.local
# PASS — 2 tests after widening audit scope to app-local templates.

python manage.py audit_public_copy --settings=config.settings.local
# PASS — app-local and root public template scan found no forbidden phrases.

python manage.py test --settings=config.settings.local
# PASS — 571 tests after final audit/template changes.

git diff --check
# PASS
```

## Intent-preserving fixes

- Removed trailing whitespace so `git diff --check` passes.
- Replaced remaining France-centric public/product copy with country-neutral wording while preserving source/job-data contexts such as France Travail.
- Strengthened `PublicCopyAuditService` to scan root and app-local templates and catch `offres françaises`, `offres IT françaises`, `offres françaises actualisées`, `offres en France`, `Objectif France`, `France-only`, `France first`, and `France-first`.
- Added public-copy audit tests proving a future `offres IT françaises` template line fails while France Travail and `job.location`/`job.country` contexts are allowed.
- Changed scheduled ingestion to prefer non-empty `config.queries_json`; empty scheduled configs still fall back to scheduled keywords.
- Added `JobIngestionRun.config_snapshot_json` and populated it with run-time config, query, limit, freshness, and provider cap values.
- Included each latest run config snapshot in `diagnose_job_ingestion` artifacts.
- Added tests proving scheduled ingestion uses `queries_json` and stores a runtime snapshot that does not change when the active config is later edited.
- Updated one older matching test whose assertion expected the now-forbidden France-centric copy.

## Intent-changing fixes or disagreements

- none

## Remaining risks

- Historical `JobIngestionRun` rows created before `jobs.0010` have empty `config_snapshot_json`; new runs will store snapshots.
- Production deployment still requires the Phase 16B manual before/after active, public-visible, and matchable job count checks.
- Local diagnostics were run after applying migrations locally only; no production migration, deploy, or production command was run.

## Ready for senior review

yes
