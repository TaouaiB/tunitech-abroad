# Phase 11 Codex Verification Prompt — Strict Review and Repair

You are Codex acting as strict senior reviewer/repair agent for TuniTech Abroad Phase 11.

## Scope

Review and, if needed, fix Phase 11 only: Privacy deletion and compliance flows.

Do not start Phase 12 admin/observability, Phase 13 polish, or Phase 14 deployment.

## Read first

```text
AGENTS.md
README.md
docs/phases/phase_11_privacy_deletion_compliance/tasks.md
docs/phases/phase_11_privacy_deletion_compliance/acceptance.md
docs/phases/phase_11_privacy_deletion_compliance/agent_report.md
```

Inspect:

```text
apps/privacy/
apps/cvs/
apps/profiles/
apps/matching/
apps/recommendations/
apps/notifications/
apps/analytics/
apps/accounts/
config/urls.py
```

## Review rules

Be strict. Do not trust the previous agent report blindly.

Check for:

- wrong stack usage
- business logic in views
- Celery tasks containing business logic instead of delegating to services
- deletion logic in models
- missing migrations
- tests not discovered (`Found 0 test(s)` is failure)
- route/template mismatches
- hidden 500s
- stale report claiming blocked/failed after fixes
- secret exposure
- public internal integer IDs
- CV privacy violations
- `CVUpload.objects` / `CVUpload.all_objects` misuse
- LLM/OpenRouter calls from views/privacy deletion code
- live France Travail public search calls
- future phase work
- overbuilding

## Required architecture expectations

- `ConsentService.record()` owns consent creation.
- `AccountDeletionService.request_deletion()` creates/returns deletion request idempotently.
- `AccountDeletionService.process_request()` owns deletion/anonymization orchestration.
- `CVDeletionService` owns CV file and CV parsed data deletion.
- Privacy views are thin and call services.
- Privacy Celery tasks are thin and call services.
- Deletion is retry-safe.
- Account deletion disables login.
- Private candidate data is deleted/anonymized.
- Global jobs, skills, sources, and system settings are not deleted.

## Commands to run

Run exactly from repo root:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py test apps.privacy --settings=config.settings.local
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.notifications --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.llm --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

If PostgreSQL is blocked, do not claim pass. Report exact blocker.

## Boundary greps

```bash
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps/privacy apps/cvs apps/notifications --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected OpenRouter runtime code"
grep -R "CVUpload.all_objects" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "No all_objects usage found"
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 4 -name "*.sqlite3" -print
find . -maxdepth 4 -name "celerybeat-schedule*" -print
find . -maxdepth 5 -name "agent_report.md.save" -print
```

## Repair authority

You may fix Phase 11 defects. Keep fixes minimal and architectural.

You must not:

- implement Phase 12/13/14
- rewrite unrelated apps
- change stack
- commit secrets
- hide failing tests
- claim success if tests did not run

## Final output required

Update or create:

```text
docs/phases/phase_11_privacy_deletion_compliance/codex_review_report.md
```

Include:

1. Verdict: PASS / FAIL / BLOCKED
2. Defects found
3. Fixes applied
4. Files changed
5. Commands run with final results and test counts
6. Boundary grep results
7. Remaining risks
8. Final `git status --short`

Stop after Phase 11 review/fix. Do not start next phase.
