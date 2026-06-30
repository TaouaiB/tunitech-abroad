# Phase 10 — Acceptance Commands

Run from the project root.

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
```

## 0. Preflight

```bash
git branch --show-current
git status --short
```

Expected branch: `dev`.

Do not continue if unrelated uncommitted work exists.

## 1. Django system checks and migrations

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
```

Failure rules:

- migration drift is failure
- missing migration is failure
- system check warning from Phase 10 wiring is failure unless documented and justified

## 2. Phase 10 app tests

Use the actual notifications app path.

```bash
python manage.py test apps.notifications --settings=config.settings.local
```

Failure rules:

- `Found 0 test(s)` is failure
- test discovery failure is failure
- skipped DB tests are failure unless the skip is pre-existing and documented

## 3. Cross-phase regression tests

```bash
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.llm --settings=config.settings.local
```

## 4. Full suite

```bash
python manage.py test --settings=config.settings.local
```

Failure rules:

- `Found 0 test(s)` is failure
- SQLite fallback is failure if local settings should use PostgreSQL
- DB blocked but "success" report is failure

## 5. Route smoke checks

Run with Django shell or tests. Prefer tests, but if manual verification is needed:

```bash
python manage.py shell --settings=config.settings.local -c "from django.urls import reverse; print(reverse('dashboard:email_preferences'))"
python manage.py shell --settings=config.settings.local -c "from django.urls import reverse; import uuid; print(reverse('notifications:unsubscribe', kwargs={'token': uuid.uuid4()}))"
```

If route names differ because the existing project has a different namespace, document the actual route names in `agent_report.md` and ensure tests cover them.

## 6. Boundary grep checks

```bash
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps/notifications --exclude-dir="tests" -n || echo "OK no OpenRouter in notifications runtime"
grep -R "FranceTravail\|france_travail" apps/notifications --exclude-dir="tests" -n || echo "OK no France Travail in notifications runtime"
grep -R "CVUpload.all_objects" apps/notifications --exclude-dir="tests" -n || echo "OK no CVUpload.all_objects in notifications runtime"
grep -R "delete_account\|DeletionRequest\|AccountDeletionService\|process_account_deletion" apps/notifications docs/phases/phase_10_email --exclude-dir="__pycache__" -n || echo "OK no Phase 11 account deletion implementation in Phase 10"
```

Interpretation:

- `objects.create_user` in app code should be fixed.
- OpenRouter in notification runtime is failure.
- France Travail in notification runtime is failure.
- `CVUpload.all_objects` in notification runtime is suspicious and must be justified or removed.
- Phase 11 deletion implementation in Phase 10 is failure. Mentions in phase boundary docs are acceptable only when clearly marked as forbidden/not implemented.

## 7. Accidental file checks

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 4 -name "*.sqlite3" -print
find . -maxdepth 4 -name "celerybeat-schedule*" -print
find . -maxdepth 4 -name "*review*.zip" -print
find . -maxdepth 4 -name "phase10*.zip" -print
```

Any output must be removed unless intentionally outside the repository or explicitly required.

## 8. Git diff review

```bash
git status --short
git diff --stat
git diff -- docs/phases/phase_10_email
```

Expected Phase 10 files may include:

```text
apps/notifications/
templates/dashboard/email_preferences.html
templates/notifications/
config/urls.py
apps/dashboard/urls.py
apps/dashboard/views.py
config/settings/base.py
.env.example
docs/phases/phase_10_email/
```

Do not include:

- `.env`
- real secrets
- `__pycache__`
- `.pyc`
- SQLite database
- celerybeat schedule
- review zip
- unrelated Phase 11/12/13/14 implementation

## 9. Agent report

The agent must create:

```text
docs/phases/phase_10_email/agent_report.md
```

Report must be fresh.

Stale `agent_report.md` is failure.

The report must include exact commands and final results.

## Required success statement

Only report success if all acceptance commands pass and Phase 10 tests were discovered.

Never claim success if:

- PostgreSQL-backed local tests were blocked
- test output says `Found 0 test(s)`
- migrations are missing
- route/template tests are missing
- hidden 500s remain
