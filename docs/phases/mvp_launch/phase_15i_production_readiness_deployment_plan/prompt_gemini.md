# Gemini Implementation Prompt — Phase 15I Production Readiness and Deployment Plan

You are Gemini implementing Phase 15I for TuniTech Abroad.

## Role

You are the implementation agent. GLM 5.2 will review after you. Do not write a GLM review report. Do not write a Codex report.

## Project rules

TuniTech Abroad stack:

- Django
- Django ORM
- PostgreSQL
- Redis
- Celery / Celery Beat
- django-allauth
- Django templates
- HTMX
- Tailwind CSS
- Alpine.js only where needed
- OpenRouter for controlled LLM usage
- PyMuPDF/pdfplumber for CV text extraction

Forbidden:

- React
- Next.js
- Angular
- FastAPI
- MongoDB
- SQLAlchemy
- SPA architecture

Architecture rules:

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models do not call external APIs.
- No OpenRouter calls from Django views/templates/models/admin display.
- No France Travail live API calls during public user job search.
- Public URLs use UUID `public_id`, never internal integer IDs.
- CV files are private and must not be publicly exposed.
- `CVUpload.objects` excludes soft-deleted CVs.
- `CVUpload.all_objects` is only for admin/privacy/deletion/internal tasks.
- LLM may extract/explain/suggest, but cannot decide final fit score.

## Mission

Implement Phase 15I: production readiness and deployment planning.

This is **not actual deployment**. Do not SSH. Do not create/buy server/domain resources. Do not run destructive system commands.

Read first:

- `AGENTS.md` if present
- `docs/phases/phase_15i_production_readiness_deployment_plan/tasks.md`
- `docs/phases/phase_15i_production_readiness_deployment_plan/acceptance.md`

## Important production LLM policy

For MVP deployment, keep LLM code but disable automatic token spending by default.

Expected production example values:

```env
LLM_ENABLED=True
CV_LLM_EXTRACTION_ENABLED=False
JOB_ENRICHMENT_ENABLED=False
JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=0
JOB_ENRICHMENT_DAILY_LIMIT=0
OPENROUTER_CIRCUIT_BREAKER_ENABLED=True
OPENROUTER_ENRICHMENT_RATE_LIMIT=1/m
```

Do not remove LLM code.

## Tasks

Complete all tasks in `tasks.md`.

Expected docs under `docs/deployment/`:

- `production_env_policy.md`
- `static_private_media_policy.md`
- `rate_limiting_abuse_controls.md`
- `monitoring_healthchecks.md`
- `backup_restore_policy.md`
- `privacy_final_review.md`
- `legal_wording_final_pass.md`
- `email_oauth_domain_checklist.md`
- `phase_15j_deployment_runbook_outline.md`
- `production_smoke_checklist.md`

You may update `.env.example` with safe placeholders only.

## Guardrails

Do not:
- read `.env`
- print `.env`
- commit secrets
- invent real API keys
- include personal Gmail/password/client secret values
- deploy
- add Docker for Django app
- expose private media
- add large dependencies
- create fake review reports

## Verification commands

Run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1

npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local

python manage.py check --deploy --settings=config.settings.production
python manage.py makemigrations --check --dry-run --settings=config.settings.production
python manage.py collectstatic --dry-run --noinput --settings=config.settings.production

pip-audit
bandit -r apps config -x "*/tests.py,*/tests/*,*/test_*.py,*/migrations/*,*/fixtures/*"
npm audit --omit=dev

git diff --check
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## Report

Create:

```text
docs/phases/phase_15i_production_readiness_deployment_plan/agent_report.md
```

Use the template. Be honest about commands that were not run.

Do not create:

```text
codex_report.md
glm_review_report.md
```
