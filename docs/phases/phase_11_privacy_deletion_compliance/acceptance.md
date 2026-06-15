# Phase 11 Acceptance — Privacy Deletion and Compliance Flows

Run all commands from the repository root on Fedora/Linux.

## Pre-flight

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short
git branch --show-current
```

Expected:

- Branch should be `dev` unless Baha explicitly says otherwise.
- Previous phase should already be committed or intentionally present in the working tree.
- `.env` must not appear in `git status`.

## Clean accidental artifacts before final test

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 4 -name "*.sqlite3" -print
find . -maxdepth 4 -name "celerybeat-schedule*" -print
find . -maxdepth 5 -name "agent_report.md.save" -print
find . -maxdepth 3 -name "*.zip" -print
```

Any printed accidental files must be removed unless intentionally required and documented.

## Django checks and migrations

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
```

Expected:

- `check` passes.
- `makemigrations --check --dry-run` reports no missing migrations.
- `migrate` passes against PostgreSQL.

If PostgreSQL is unavailable, do not claim success. Report the blocker exactly.

## Phase app tests

```bash
python manage.py test apps.privacy --settings=config.settings.local
```

Expected:

- Tests are discovered.
- `Found 0 test(s)` is failure.
- All privacy tests pass.

## Regression tests for touched dependent apps

Run these because Phase 11 touches CV deletion, recommendations, matching, notifications, and analytics/user events:

```bash
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.notifications --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.llm --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
```

Expected:

- All pass.
- No tests skipped silently unless documented.
- `Found 0 test(s)` is failure for any phase-critical app.

## Full suite

```bash
python manage.py test --settings=config.settings.local
```

Expected:

- Full suite passes.
- No hidden DB fallback to SQLite unless explicitly configured and approved. PostgreSQL-backed local settings are expected.

## Required route smoke checks

```bash
python manage.py shell --settings=config.settings.local -c "
from django.urls import reverse
names = [
    'privacy:privacy_policy',
    'privacy:terms',
]
for name in names:
    print(name, '->', reverse(name))
"
```

If route names differ, the agent report must list the actual names and justify them.

Expected public paths:

```text
/privacy/
/terms/
```

Expected private paths if implemented/named:

```text
/dashboard/account/
/dashboard/settings/delete-account/
```

## Manual smoke test with runserver

Start server:

```bash
python manage.py runserver 127.0.0.1:8000 --settings=config.settings.local
```

Open:

```text
http://127.0.0.1:8000/privacy/
http://127.0.0.1:8000/terms/
http://127.0.0.1:8000/dashboard/account/
http://127.0.0.1:8000/dashboard/settings/delete-account/
```

Expected:

- Public privacy and terms pages load anonymously.
- Dashboard account and delete-account pages require login.
- No server 500s in terminal logs.

## Boundary greps

```bash
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps/privacy apps/cvs apps/notifications --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected OpenRouter runtime code"
grep -R "FranceTravailClient\|france_travail\|api.francetravail" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || true
grep -R "CVUpload.all_objects" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "No all_objects usage found"
grep -R "password\|secret\|token" docs/phases/phase_11_privacy_deletion_compliance apps/privacy --exclude-dir="__pycache__" -n || true
```

Review output manually:

- `objects.create_user` should not be used.
- OpenRouter should not appear in privacy runtime code.
- France Travail live calls must not appear in public search or privacy code.
- `CVUpload.all_objects` must be limited to privacy/deletion/admin/internal task code.
- Grep for `password/secret/token` must not reveal real values. Model field names and safe text are OK.

## Git review

```bash
git status --short
git diff --stat
git diff --check
git diff -- . ':!*.lock'
```

Expected:

- Only intentional Phase 11 files changed.
- No `.env`.
- No real secrets.
- No cache files.
- No accidental review artifacts.

## Final acceptance checklist

The phase is not accepted unless all are true:

- Privacy Policy page exists and loads.
- Terms page exists and loads.
- CV processing consent is recorded.
- Email digest opt-in consent is recorded.
- User can delete CV safely.
- CV physical file is removed or safely handled if already missing.
- Deleted CV is excluded from `CVUpload.objects`.
- User can request account deletion.
- Account deletion processing disables login.
- Account deletion removes/anonymizes private candidate data.
- Account deletion removes CV files.
- Account deletion removes profile, skills, saved jobs, matches, recommendations, and email preferences where applicable.
- User events are deleted/anonymized.
- Deletion request records completion/failure and can be retried after failure.
- Celery task delegates to service only.
- No OpenRouter calls from views/privacy deletion.
- No live France Travail calls during public job search.
- No public integer IDs introduced.
- Full tests pass.
- Agent report is current and honest.
