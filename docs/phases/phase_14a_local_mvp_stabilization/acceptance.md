# Acceptance Commands

Run from repo root.

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
```

## 1. System checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
```

Required:

- All pass.
- No unapplied model drift.
- Migrate uses PostgreSQL-backed local settings, not accidental SQLite.

Confirm DB vendor:

```bash
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
```

Expected:

```text
DB_VENDOR= postgresql
```

## 2. Full test suite

```bash
python manage.py test --settings=config.settings.local
```

Required:

- Must not say `Found 0 test(s)`.
- Must finish with OK.
- If failures exist, fix root cause.

## 3. Focused app tests

Run if these paths exist:

```bash
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.profiles --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test apps.llm --settings=config.settings.local
python manage.py test apps.core --settings=config.settings.local
python manage.py test apps.dashboard --settings=config.settings.local
```

If an app has no tests, that is a defect for touched behavior.

## 4. Seed and local data smoke

```bash
python manage.py seed_skills --settings=config.settings.local || python manage.py seed_skill_taxonomy --settings=config.settings.local || true
python manage.py seed_job_sources --settings=config.settings.local || true
python manage.py seed_demo_data --settings=config.settings.local || true
python manage.py shell --settings=config.settings.local -c "from apps.jobs.models import RawJobRecord, NormalizedJob; print('RAW=', RawJobRecord.objects.count()); print('NORMALIZED=', NormalizedJob.objects.count()); print('ACTIVE=', NormalizedJob.objects.filter(status='active').count())"
```

Required:

- If seed commands exist, they must be idempotent.
- Active normalized jobs must be available for recommendation tests.

## 5. CV sample smoke

The agent must add or repair a no-browser service/command smoke for synthetic CV parsing.

Preferred command if created:

```bash
python manage.py cv_parse_smoke_test --settings=config.settings.local
```

Equivalent shell/test command is acceptable if it proves:

- Text extraction works from a real text-based PDF.
- CVParsedData contains name, email, phone, location, LinkedIn, GitHub, portfolio/website.
- CandidateProfile prefill works where fields are empty.
- Non-empty profile identity is not silently overwritten.
- ProfileSkill rows are created or updated.
- Profile completeness recalculates.

## 6. Recommendations smoke

Preferred command if created:

```bash
python manage.py recommendations_smoke_test --settings=config.settings.local
```

Equivalent shell/test command is acceptable if it proves:

- Usable profile exists.
- Active jobs exist.
- Refresh service creates stored JobRecommendation rows.
- RecommendationRun status is success.
- Dashboard query returns recommendations.

## 7. Quick match smoke

Must be covered by automated tests. Additional shell/test command optional.

Required proof:

- Same job + changed skill payload returns fresh result.
- No LLM call.
- No CV storage.
- HTMX/template reset behavior exists.

## 8. Safe 404 smoke

```bash
python manage.py test apps.core --settings=config.settings.local
```

Required proof:

- `DEBUG=False` safe 404 test passes.
- `/recommendations/` does not leak URLconf debug data in production-style test.

## 9. Real LLM validation

Run only after unit tests pass.

```bash
python manage.py shell --settings=config.settings.local -c "from django.conf import settings; print('LLM_ENABLED=', getattr(settings, 'LLM_ENABLED', None)); print('HAS_OPENROUTER_API_KEY=', bool(getattr(settings, 'OPENROUTER_API_KEY', '')))"
```

Then run the implemented safe command/test, for example:

```bash
python manage.py llm_smoke_test --kind cv_extraction --settings=config.settings.local
```

If command name differs, report exact command.

Required:

- At most 2 real calls.
- No secrets printed.
- Valid structured result.
- Usage log created or real run recorded.

## 10. Real France Travail small ingestion validation

Run only after unit tests pass.

```bash
python manage.py shell --settings=config.settings.local -c "from django.conf import settings; print('HAS_FT_CLIENT_ID=', bool(getattr(settings, 'FRANCE_TRAVAIL_CLIENT_ID', ''))); print('HAS_FT_CLIENT_SECRET=', bool(getattr(settings, 'FRANCE_TRAVAIL_CLIENT_SECRET', '')))"
```

Then run the implemented safe command, for example:

```bash
python manage.py sync_france_travail_jobs --limit 10 --settings=config.settings.local
```

If command name differs, report exact command.

Required:

- Raw records created/updated.
- Normalized jobs created/updated.
- No credentials printed.
- Public search remains local-only.

## 11. Secret and artifact hygiene

```bash
git status --short
find . -path ./.venv -prune -o -path ./env -prune -o -name "*.pyc" -print
find . -path ./.venv -prune -o -path ./env -prune -o -type d -name "__pycache__" -print
find . -maxdepth 4 -name "*.sqlite3" -print
find . -maxdepth 4 -name "celerybeat-schedule*" -print
grep -R "OPENROUTER_API_KEY=..\|FRANCE_TRAVAIL_CLIENT_SECRET=..\|EMAIL_HOST_PASSWORD=..\|Damn@\|password :" . --exclude-dir=.git --exclude-dir=.venv --exclude="*.pyc" -n || true
```

Required:

- Do not commit generated caches/pyc/sqlite/celerybeat files.
- No real password/API secret appears in tracked files or reports.

## Final classification

Use exactly one:

```text
PASS
FAIL
BLOCKED_DB
BLOCKED_REDIS
BLOCKED_REAL_LLM
BLOCKED_REAL_FRANCE_TRAVAIL
BLOCKED_EXTERNAL_VALIDATION
```

`PASS` is allowed only if all local tests and both real validations pass.
