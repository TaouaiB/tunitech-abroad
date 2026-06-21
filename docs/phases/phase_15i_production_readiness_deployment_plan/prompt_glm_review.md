# GLM 5.2 Review Prompt — Phase 15I Production Readiness and Deployment Plan

You are GLM 5.2 reviewing Phase 15I.

You are **not Codex**. Do not write a Codex report. Do not claim Codex verification.

## Role

You are the second-pass reviewer after Gemini implementation.

You may repair only small in-scope issues. Do not refactor broadly.

## Project rules

TuniTech Abroad is Django + HTMX + Tailwind + PostgreSQL + Redis + Celery.

Forbidden:

- React
- Next.js
- Angular
- FastAPI
- MongoDB
- SQLAlchemy
- SPA architecture

Architecture:

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- No OpenRouter from views/templates/models/admin display.
- No France Travail live API call from public search.
- Public URLs use UUID `public_id`, never internal integer IDs.
- CV files are private.
- `.env` must not be read, printed, changed, or committed.

## Mission

Review Phase 15I implementation.

Phase 15I prepares for deployment. It does **not** deploy.

Verify:

- production `.env.example` uses placeholders only
- LLM automatic token spending disabled by default
- Whitenoise/static/private media policy is correct
- Caddy/Nginx plan does not expose CV/private media
- rate limiting / abuse-control plan exists
- monitoring/health checks plan exists
- backup/restore policy exists and requires restore testing
- privacy final checklist exists
- legal wording final pass exists
- email/OAuth/domain checklist exists
- Phase 15J runbook outline exists
- production smoke checklist exists
- no real secrets exposed

## Expected production LLM defaults

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

## Blockers

Block if you find:

- real secrets in tracked files/diff/reports
- `.env` read or printed
- private media exposed by web server/static config
- public search calling France Travail
- LLM automation enabled by default in production example
- forbidden stack introduced
- missing backup/restore policy
- missing rollback/deployment runbook outline
- deployment was started instead of planned
- commands failing after repair

## Commands

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
docs/phases/phase_15i_production_readiness_deployment_plan/glm_review_report.md
```

Verdict:

```text
PASS / REPAIRED_PASS / BLOCKED / FAIL
```

Report:

- files reviewed
- commands run
- repairs made, if any
- remaining risks
- commit recommendation

Do not create or overwrite `codex_report.md`.
