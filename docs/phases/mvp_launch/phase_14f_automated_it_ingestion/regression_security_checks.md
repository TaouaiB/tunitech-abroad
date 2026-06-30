# Regression / Security Checks — Phase 14F

Run and report:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.llm apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
git diff --check
git status --short
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

Boundary greps:

```bash
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/accounts apps/dashboard apps/profiles apps/privacy apps/recommendations templates -n 2>/dev/null || true
grep -R "OpenRouter\|OPENROUTER\|llm\|LLM\|job_enrichment\|enrich_job" apps/*/views.py apps/*/views templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|raw_text" templates -n 2>/dev/null || true
grep -R "actual_limit = min(limit, 10)" apps/jobs/management/commands/sync_france_travail_it_jobs.py apps/jobs/services -n 2>/dev/null || true
```

The new broad IT command must not contain a hidden `min(limit, 10)` cap.

Allowed France Travail references:

- `apps/jobs/services/france_travail/`
- ingestion services
- management commands
- Celery tasks
- tests

Forbidden France Travail references:

- public job views
- recommendation views
- matching views
- dashboard views
- templates

Allowed LLM references:

- LLM service
- Celery task
- management command
- tests

Forbidden LLM references:

- Django views
- templates
- user request path
