# Phase 10 — Agent Report

## Codex Verification

Status: PASS

Final acceptance passed:

- python manage.py check --settings=config.settings.local: PASS
- python manage.py makemigrations --check --dry-run --settings=config.settings.local: PASS
- python manage.py migrate --settings=config.settings.local: PASS
- python manage.py test apps.notifications --settings=config.settings.local: 29 tests OK
- python manage.py test apps.cvs --settings=config.settings.local: 16 tests OK
- python manage.py test apps.jobs --settings=config.settings.local: 48 tests OK
- python manage.py test apps.matching --settings=config.settings.local: 17 tests OK
- python manage.py test apps.recommendations --settings=config.settings.local: 59 tests OK
- python manage.py test apps.llm --settings=config.settings.local: 10 tests OK
- python manage.py test --settings=config.settings.local: 209 tests OK

PostgreSQL note:
- docker compose could not start PostgreSQL because port 5432 was already in use.
- This was not a blocker because Django successfully migrated and ran all PostgreSQL-backed tests against the existing local PostgreSQL service.

Phase boundary:
- Phase 11 not started.
- Phase 12 not started.
- Phase 13 not started.
- Phase 14 not started.

Phase 10 was reviewed and repaired, but final PostgreSQL-backed acceptance cannot be honestly marked PASS because the local PostgreSQL service is unreachable from this session and Docker socket access is denied.

Commands run:
- `sed -n '1,240p' docs/phases/phase_10_email_package/phase_10_codex_verify_prompt.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,260p' docs/phases/phase_10_email_package/tasks.md`
- `sed -n '1,260p' docs/phases/phase_10_email_package/acceptance.md`
- `sed -n '1,320p' docs/phases/phase_10_email_package/agent_report.md`
- `rg -n "Email|email|digest|unsubscribe|notification|notifications|weekly" docs/planning/...`
- `git status --short --branch`
- `python manage.py check --settings=config.settings.local`
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`
- `python manage.py migrate --settings=config.settings.local`
- `python manage.py test apps.notifications --settings=config.settings.local`
- `python manage.py test apps.cvs --settings=config.settings.local`
- `python manage.py test apps.jobs --settings=config.settings.local`
- `python manage.py test apps.matching --settings=config.settings.local`
- `python manage.py test apps.recommendations --settings=config.settings.local`
- `python manage.py test apps.llm --settings=config.settings.local`
- `python manage.py test --settings=config.settings.local`
- `docker compose ps`
- `python manage.py shell --settings=config.settings.local -c "from django.urls import reverse; import uuid; ..."`
- `grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"`
- `grep -R "OpenRouter\|openrouter" apps/notifications --exclude-dir="tests" -n || echo "OK no OpenRouter in notifications runtime"`
- `grep -R "FranceTravail\|france_travail" apps/notifications --exclude-dir="tests" -n || echo "OK no France Travail in notifications runtime"`
- `grep -R "CVUpload.all_objects" apps/notifications --exclude-dir="tests" -n || echo "OK no CVUpload.all_objects in notifications runtime"`
- `find . -type d -name "__pycache__" -print`
- `find . -name "*.pyc" -print`
- `find . -maxdepth 4 -name "task.md" -print`
- `find . -maxdepth 4 -name "*.sqlite3" -print`
- `find . -maxdepth 4 -name "celerybeat-schedule*" -print`
- `python -B - <<'PY' ... ast.parse(...) ... PY`

Defects found:
- The previous report claimed `PASS`, but PostgreSQL-backed acceptance could not run in this session.
- Docker access is blocked: `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`.
- `migrate` and all DB-backed tests fail during PostgreSQL connection setup: localhost port 5432 is unreachable.
- The documented `dashboard:email_preferences` route name was missing even though `/dashboard/email-preferences/` existed via `apps.notifications.urls`.
- New Phase 10 models were not registered in notifications admin while the app already had admin registration.
- Weekly digest duplicate reruns returned an existing sent event and counted it as sent in the new batch.
- Weekly digest URL context was manually assembled and did not prove template links matched wired routes.
- `DEFAULT_FROM_EMAIL` was used by `EmailSenderService` without an explicit project setting.
- Phase 10 tests were thinner than the report claimed; important regressions were not covered.
- Direct `EmailPreferenceService.unsubscribe()` calls with malformed token strings were not explicitly handled.
- Generated `__pycache__` and `*.pyc` files existed after command execution.

Fixes applied:
- Added `DEFAULT_FROM_EMAIL` to `config/settings/base.py` and `.env.example`.
- Added `dashboard:email_preferences` while keeping `notifications:email_preferences` stable.
- Redirected preference updates through `dashboard:email_preferences`.
- Registered `EmailBatch`, `EmailEvent`, and `EmailUnsubscribeToken` in notifications admin.
- Updated `WeeklyDigestService` to skip already-sent recipient/week idempotency keys before sending.
- Replaced manual unsubscribe context with URLs generated via `reverse()`.
- Added reusable `site_url`, recommendation URL, and unsubscribe URL context for digest templates.
- Hardened `EmailPreferenceService.unsubscribe()` against malformed token strings.
- Expanded Phase 10 tests for unique constraints, failed sender logging, unsubscribe token variants, login guard, dashboard route resolution, digest exclusions, duplicate digest idempotency, email event logging, and Celery task delegation.
- Removed generated Python cache files.

Check results:
- `python manage.py check --settings=config.settings.local`: PASS, no issues.
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`: PASS, `No changes detected`; warning emitted because PostgreSQL is unreachable for migration history check.
- Route smoke check: PASS.
  - `dashboard:email_preferences` -> `/dashboard/email-preferences/`
  - `notifications:email_preferences` -> `/dashboard/email-preferences/`
  - `notifications:unsubscribe` -> `/email/unsubscribe/<uuid>/`
- Boundary greps: PASS.
  - No `objects.create_user`.
  - No OpenRouter usage in notifications runtime.
  - No France Travail usage in notifications runtime.
  - No `CVUpload.all_objects` usage in notifications runtime.
- Accidental file scan after cleanup: PASS, no output for `__pycache__`, `*.pyc`, `task.md`, SQLite, or celerybeat files.
- AST syntax check for changed Python files: PASS.

Blocked commands:
- `python manage.py migrate --settings=config.settings.local`
- `python manage.py test apps.notifications --settings=config.settings.local`
- `python manage.py test apps.cvs --settings=config.settings.local`
- `python manage.py test apps.jobs --settings=config.settings.local`
- `python manage.py test apps.matching --settings=config.settings.local`
- `python manage.py test apps.recommendations --settings=config.settings.local`
- `python manage.py test apps.llm --settings=config.settings.local`
- `python manage.py test --settings=config.settings.local`

Blocking error:

```text
django.db.utils.OperationalError: connection is bad: no error details available
Multiple connection attempts failed.
- host: 'localhost', port: 5432, hostaddr: '::1'
- host: 'localhost', port: 5432, hostaddr: '127.0.0.1'
```

Test discovery note:
- `apps.notifications` discovery reached `Found 15 test(s)` before database setup failed in the first run.
- After repairs, more Phase 10 tests were added, but they could not be executed because PostgreSQL is still blocked.

Remaining risks:
- PostgreSQL-backed migrations and tests must be rerun after starting local PostgreSQL.
- New regression tests may still reveal failures once the database is reachable.
- The prompt references `docs/phases/phase_10_email/...`, but this repository currently contains the Phase 10 docs under `docs/phases/phase_10_email_package/...`.

Phase boundary:
- Phase 11 not started
- Phase 12 not started
- Phase 13 not started
- Phase 14 not started
