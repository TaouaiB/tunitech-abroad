# Phase 09 — LLM Support — Acceptance

## Mandatory local commands

Run from repo root:

```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local

python manage.py test apps.llm --settings=config.settings.local
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Zero-test rule

This is a blocker:

```text
Found 0 test(s).
NO TESTS RAN
```

The Phase 09 app must have real discoverable tests.

## Boundary greps

```bash
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps --exclude-dir="tests" -n
grep -R "send_mail\|email_digest\|unsubscribe" apps/llm apps/cvs apps/jobs apps/matching apps/recommendations apps/dashboard --exclude-dir="tests" -n || echo "OK no email phase work"
grep -R "requests\|httpx" apps/llm --exclude-dir="tests" -n || echo "OK check whether client uses approved transport only"
grep -R "CVUpload.all_objects" apps/llm --exclude-dir="tests" -n || echo "OK no all_objects in LLM runtime"
grep -R "file.url\|\.path\|raw_text" apps/llm --exclude-dir="tests" -n || echo "OK no obvious CV path/raw text logging"
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
```

## Required acceptance conditions

- App is registered in settings.
- Migrations are present if models are added.
- `.env.example` has placeholders only.
- No real secrets are committed or printed.
- OpenRouter integration is disabled by default or safe without API key.
- OpenRouter calls are isolated in services/client layer.
- No OpenRouter call from views.
- No OpenRouter call from models.
- No LLM scoring decision.
- LLM can only assist, explain, or suggest.
- Tests mock all provider calls.
- Full suite passes.
- Agent report is truthful and not stale.
