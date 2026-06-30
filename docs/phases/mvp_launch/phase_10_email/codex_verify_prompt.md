# Codex Verification Prompt — Phase 10 Email

You are reviewing and fixing **Phase 10 — Email** for TuniTech Abroad.

You are allowed to inspect code, run tests, and fix Phase 10 defects.

You must not start Phase 11.

## Read first

```text
AGENTS.md
docs/phases/phase_10_email/tasks.md
docs/phases/phase_10_email/acceptance.md
docs/phases/phase_10_email/agent_report.md
docs/planning/Implementation_Roadmap_v1.pdf
docs/planning/Service_Contracts_v1.pdf
docs/planning/PRD_v1.pdf
docs/planning/Page_URL_View_Map_v1.pdf
docs/planning/Database_Schema_v1.pdf
```

## Review target

Phase 10 scope only:

- EmailBatch
- EmailEvent
- EmailUnsubscribeToken
- EmailSenderService
- EmailPreferenceService
- WeeklyDigestService
- email preference page
- unsubscribe flow
- weekly digest task
- digest templates
- tests

Use existing `apps.notifications`.

Do not create `apps.email`.

## Strict checks

Reject or fix:

- app created but not registered
- missing migrations
- `Found 0 test(s)`
- current phase tests not discovered
- full suite passing while `apps.notifications` tests do not run
- URL referenced in template but not wired
- view missing even if template exists
- template created but never used
- service created but not called
- Celery task contains business logic instead of calling service
- hidden HTTP 500
- stale `agent_report.md`
- `objects.create_user`
- raw secrets
- `.env` committed
- OpenRouter calls in notifications runtime
- France Travail calls in notifications runtime
- `CVUpload.all_objects` in notifications runtime
- internal integer IDs in public email links
- weekly digest sent to unverified users
- weekly digest sent without opt-in
- weekly digest sent to inactive users
- weekly digest duplicate sends for same user/week
- unsubscribe requires login
- invalid unsubscribe causes 500
- Phase 11 account deletion implementation
- Phase 12 admin observability implementation
- Phase 13 polish implementation
- Phase 14 deployment implementation

## Required command set

Run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local

python manage.py test apps.notifications --settings=config.settings.local
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.llm --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Then run boundary checks:

```bash
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps/notifications --exclude-dir="tests" -n || echo "OK no OpenRouter in notifications runtime"
grep -R "FranceTravail\|france_travail" apps/notifications --exclude-dir="tests" -n || echo "OK no France Travail in notifications runtime"
grep -R "CVUpload.all_objects" apps/notifications --exclude-dir="tests" -n || echo "OK no CVUpload.all_objects in notifications runtime"
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 4 -name "*.sqlite3" -print
find . -maxdepth 4 -name "celerybeat-schedule*" -print
```

## Repair rules

If any command fails:

1. Read the exact error.
2. Find the root cause.
3. Fix only Phase 10 defects.
4. Add or update regression tests.
5. Re-run the failed command.
6. Re-run the full acceptance set.
7. Repeat up to 8 repair loops.

Do not claim success if PostgreSQL tests are blocked.

Do not claim success if `Found 0 test(s)` appears.

## Output required

Update:

```text
docs/phases/phase_10_email/agent_report.md
```

Add a final verification section:

```markdown
## Codex Verification

Status: PASS / FAIL / BLOCKED

Commands run:
- ...

Defects found:
- ...

Fixes applied:
- ...

Remaining risks:
- ...

Phase boundary:
- Phase 11 not started
- Phase 12 not started
- Phase 13 not started
- Phase 14 not started
```

Stop after Phase 10 is clean.
