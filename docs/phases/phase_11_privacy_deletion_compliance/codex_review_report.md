# Phase 11 Codex Review Report

## 1. Verdict

Manual rerun by Baha after PostgreSQL became reachable:
- makemigrations --check --dry-run: PASS, No changes detected
- apps.privacy: 15 tests OK
- apps.cvs: 17 tests OK
- apps.notifications: 29 tests OK
- apps.matching: 17 tests OK
- apps.recommendations: 59 tests OK
- apps.llm: 10 tests OK
- apps.jobs: 48 tests OK
- full suite: 224 tests OK

PASS after manual PostgreSQL acceptance rerun

Phase 11 had real implementation defects during review. I repaired the defects listed below and verified code-level behavior with `manage.py check`, `git diff --check`, and a temporary SQLite smoke run for `apps.privacy`.

Final acceptance remains blocked because the required local PostgreSQL service is not reachable and Docker access is denied in this environment.

## 2. Defects found

- `ConsentService.record()` did not match the Phase 11 contract and did not store stable consent text.
- `CVUploadService`, `CVDeletionService`, and `AccountDeletionService` imported `apps.analytics.services.events`, which does not exist. User events were silently skipped.
- `AccountDeletionService` referenced `LLMUsageLog`, but the project model is `LLMRequestLog`.
- Account deletion attempted to delete `CandidateProfile` before `MatchResult`, which can fail because `MatchResult.profile` is protected.
- Account deletion did not scrub `EmailEvent.to_email`, `EmailEvent.metadata_json`, `LLMRequestLog.error_message`, or `RecommendationRun.user`.
- Account deletion did not handle already soft-deleted CV rows when deleting files during account deletion.
- Privacy Celery maintenance tasks contained cleanup/scanning logic directly instead of delegating to services.
- `/dashboard/account/` rendered a template that extended missing `dashboard/base_dashboard.html`.
- `/dashboard/settings/delete-account/` redirected to missing URL name `home`.
- Dashboard account template used un-namespaced `privacy_policy` and `terms` URL names.
- Phase 11 tests missed route rendering, task delegation, and private-data cleanup coverage.

## 3. Fixes applied

- Added `ConsentRecord.consent_text` and migration `0003_consentrecord_consent_text.py`.
- Updated `ConsentService.record()` to accept `consent_text`, `consent_version`, and optional `request_meta`.
- Updated CV upload and email preference services to record consent through `ConsentService.record()`.
- Fixed analytics event calls to use `apps.analytics.services.user_event.UserEventService.record_event()`.
- Added `CVDeletionService.delete_cv_record()` for internal/privacy cleanup, including already soft-deleted CV rows.
- Reordered account deletion cleanup and added scrubbing/anonymization for email events, LLM request logs, recommendation runs, and user events.
- Added `PrivacyMaintenanceService` and made privacy Celery tasks delegate to services.
- Fixed dashboard templates to extend `base.html`, use `content`, and reverse `privacy:*` route names.
- Fixed delete-account redirect to `core:home`.
- Added privacy tests for route access/rendering, deliberate confirmation, task delegation, consent text, retry counts, and deletion cleanup.
- Registered `DeletionRequest` in privacy admin using existing admin conventions.

## 4. Files changed

- `apps/cvs/services/deletion.py`
- `apps/cvs/services/upload.py`
- `apps/cvs/tests/test_services.py`
- `apps/dashboard/urls.py`
- `apps/dashboard/views.py`
- `apps/dashboard/templates/dashboard/account.html`
- `apps/dashboard/templates/dashboard/delete_account.html`
- `apps/notifications/services/preferences.py`
- `apps/privacy/admin.py`
- `apps/privacy/models.py`
- `apps/privacy/migrations/0002_deletionrequest.py`
- `apps/privacy/migrations/0003_consentrecord_consent_text.py`
- `apps/privacy/services/account_deletion.py`
- `apps/privacy/services/consent.py`
- `apps/privacy/services/maintenance.py`
- `apps/privacy/tasks.py`
- `apps/privacy/templates/privacy/privacy_policy.html`
- `apps/privacy/templates/privacy/terms.html`
- `apps/privacy/tests.py`
- `apps/privacy/urls.py`
- `apps/privacy/views.py`
- `config/urls.py`
- `docs/phases/phase_11_privacy_deletion_compliance/codex_review_report.md`

## 5. Commands run with final results

Required local-settings commands:

- `git status --short`: ran; Phase 11 files are modified/untracked, no `.env` shown.
- `python manage.py check --settings=config.settings.local`: PASS, `System check identified no issues (0 silenced).`
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`: PASS for model drift, `No changes detected`; warning because PostgreSQL connection could not be checked.
- `python manage.py migrate --settings=config.settings.local`: BLOCKED by PostgreSQL connection failure.
- `python manage.py test apps.privacy --settings=config.settings.local`: BLOCKED by PostgreSQL test DB connection failure; discovered 15 tests before failure.
- `python manage.py test apps.cvs --settings=config.settings.local`: BLOCKED by PostgreSQL test DB connection failure; discovered 17 tests before failure.
- `python manage.py test apps.notifications --settings=config.settings.local`: BLOCKED by PostgreSQL test DB connection failure; discovered 29 tests before failure.
- `python manage.py test apps.matching --settings=config.settings.local`: BLOCKED by PostgreSQL test DB connection failure; discovered 17 tests before failure.
- `python manage.py test apps.recommendations --settings=config.settings.local`: BLOCKED by PostgreSQL test DB connection failure; discovered 59 tests before failure.
- `python manage.py test apps.llm --settings=config.settings.local`: BLOCKED by PostgreSQL test DB connection failure; discovered 10 tests before failure.
- `python manage.py test apps.jobs --settings=config.settings.local`: BLOCKED by PostgreSQL test DB connection failure; discovered 48 tests before failure.
- `python manage.py test --settings=config.settings.local`: BLOCKED by PostgreSQL test DB connection failure; discovered 224 tests before failure.

Exact blocker:

```text
django.db.utils.OperationalError: connection is bad: no error details available
Multiple connection attempts failed.
- host: 'localhost', port: 5432, hostaddr: '::1'
- host: 'localhost', port: 5432, hostaddr: '127.0.0.1'
```

Docker check:

```text
docker compose ps
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

Additional smoke checks:

- `python -m compileall apps/privacy apps/cvs apps/notifications apps/dashboard`: PASS.
- `DATABASE_URL=sqlite:////tmp/tunitech_phase11.sqlite3 python manage.py test apps.privacy --settings=config.settings.local`: PASS, `Found 15 test(s)`, `Ran 15 tests`, `OK`.
- `git diff --check`: PASS after removing trailing whitespace.

## 6. Boundary grep results

```text
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n
OK no objects.create_user
```

```text
grep -R "OpenRouter\|openrouter" apps/privacy apps/cvs apps/notifications --exclude-dir="tests" --exclude-dir="__pycache__" -n
OK no unexpected OpenRouter runtime code
```

```text
grep -R "CVUpload.all_objects" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n
apps/privacy/tests.py
apps/privacy/services/account_deletion.py
apps/privacy/services/maintenance.py
apps/cvs/services/parsing.py
```

`CVUpload.all_objects` usage is limited to tests, privacy/deletion maintenance, and internal CV parsing retry-safety code.

```text
grep -R "FranceTravailClient\|france_travail\|api.francetravail" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n
apps/jobs/services/france_travail/client.py
apps/jobs/services/source_seed.py
apps/jobs/services/fixture_ingestion.py
apps/jobs/management/commands/ingest_job_fixtures.py
apps/jobs/tasks.py
```

These are ingestion/source paths, not public job search calls.

Artifact checks after cleanup:

```text
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 4 -name "*.sqlite3" -print
find . -maxdepth 4 -name "celerybeat-schedule*" -print
find . -maxdepth 5 -name "agent_report.md.save" -print
```

All printed no results.

## 7. Remaining risks

- Required PostgreSQL-backed migrations and tests have not passed because PostgreSQL is unreachable and Docker socket access is denied.
- SQLite smoke testing is not a substitute for final acceptance because the locked stack requires PostgreSQL.
- `delete_orphaned_cv_files` remains a dry-run/report flow by design; physical deletion of orphaned files should only be enabled after storage behavior is tested in the deployed environment.

## 8. Final git status --short

```text
M apps/cvs/services/deletion.py
M apps/cvs/services/upload.py
M apps/cvs/tests/test_services.py
M apps/dashboard/urls.py
M apps/dashboard/views.py
M apps/notifications/services/preferences.py
M apps/privacy/admin.py
M apps/privacy/models.py
M apps/privacy/services/consent.py
M apps/privacy/tests.py
M apps/privacy/views.py
M config/urls.py
?? apps/dashboard/templates/
?? apps/privacy/migrations/0002_deletionrequest.py
?? apps/privacy/migrations/0003_consentrecord_consent_text.py
?? apps/privacy/services/account_deletion.py
?? apps/privacy/services/maintenance.py
?? apps/privacy/tasks.py
?? apps/privacy/templates/
?? apps/privacy/urls.py
?? docs/phases/phase_11_privacy_deletion_compliance/
```
