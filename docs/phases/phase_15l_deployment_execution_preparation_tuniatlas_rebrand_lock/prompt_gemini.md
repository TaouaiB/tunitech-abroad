# Gemini Implementation Prompt — Phase 15L

You are Gemini implementing Phase 15L for TuniTech Abroad.

## Phase

Phase 15L — Deployment Execution Preparation + TuniAtlas Public Rebrand Lock

## Workflow

You are the implementation agent. Sonnet will review after you.
Do not create a Codex report. Do not create a GLM report.

## Context

The public brand is now **TuniAtlas**.

Final brand values:

- Public brand: `TuniAtlas`
- Product line: `TuniAtlas Jobs`
- Tagline: `Tech careers abroad for Tunisian talent`
- SEO title: `TuniAtlas — Tech Jobs Abroad for Tunisians`
- Primary domain target: `tuniatlas.com`
- Later/defensive domain: `tuniatlas.tn`
- Keep repo/internal project name: `tunitech-abroad` until after deployment

Stack rules:

- Django + Django ORM + PostgreSQL + Redis + Celery + django-allauth + Django templates + HTMX + Tailwind.
- No React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, SPA.
- Views stay thin.
- Business logic stays in services.
- No OpenRouter calls from views/templates/models/admin display.
- No France Travail live API calls from public job search/views.
- CV/private media must remain private.
- Public URLs use UUID public IDs.

## Strict boundaries

This is not actual deployment.
Do not provision a VPS.
Do not configure DNS.
Do not buy a domain.
Do not touch external servers.
Do not read, print, edit, create, or commit `.env`.
Do not add large UI/UX redesign features from the design pack.
Do not change matching/scoring logic.
Do not rename Django apps, Python packages, migrations, database tables, Celery queues, Git repo, or remote.

## Mission

Implement a small, safe public rebrand and deployment-preparation lock.

### 1. Public rebrand

Find public-facing old brand text and replace with the final brand.

Update likely places as applicable:

- base layout title
- navbar/header
- footer
- homepage/landing page
- auth pages
- dashboard public/product labels
- email templates
- admin site header/title if it shows old public brand
- SEO/meta title/description
- static manifest or app title constants if present

Use `TuniAtlas Jobs` when referring to the job product, and `TuniAtlas` for the platform/app.

Do not replace historical docs blindly.

### 2. Logo/favicon

If logo assets are available in the extracted phase package under `brand_assets/`, copy them to a safe static path, for example:

```text
static/img/brand/tuniatlas-logo-horizontal.png
```

Use the logo in templates where appropriate. Do not overbuild image processing. Do not invent fake brand files if unavailable; document missing assets instead.

### 3. Deployment execution preparation docs

Create/update docs so Phase 15M can execute deployment without guessing:

- `docs/deployment/phase_15l_deployment_decisions.md`
- `docs/deployment/phase_15l_final_pre_deploy_checklist.md`

They must cover:

- provider/server plan, without claiming current prices unless verified by the user
- domain plan: `tuniatlas.com` primary, `www.tuniatlas.com` canonical redirect behavior, `tuniatlas.tn` later
- email provider plan
- backup destination plan
- production `.env` manual fill checklist, placeholders only
- LLM automatic spending disabled
- private media/CV protection
- exact next phase order: 15M deployment, 15N smoke test, 15O Opus security audit, 15P public launch fixes

### 4. LLM/token safety

Do not remove LLM code.
Confirm deployment docs and `.env.example` keep automatic spending disabled:

```env
LLM_ENABLED=True
CV_LLM_EXTRACTION_ENABLED=False
JOB_ENRICHMENT_ENABLED=False
JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=0
JOB_ENRICHMENT_DAILY_LIMIT=0
OPENROUTER_CIRCUIT_BREAKER_ENABLED=True
OPENROUTER_ENRICHMENT_RATE_LIMIT=1/m
```

If `.env.example` differs, update `.env.example` only. Never read or edit `.env`.

## Commands to run

Run without hiding failures:

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
python manage.py collectstatic --dry-run --noinput --settings=config.settings.production
pip-audit
bandit -r apps config -x "*/tests.py,*/tests/*,*/test_*.py,*/migrations/*,*/fixtures/*"
npm audit --omit=dev
git diff --check
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
grep -R "TuniTech Abroad\|tunitech abroad\|Tunitech Abroad" templates static apps config docs/deployment .env.example -n || true
```

## Report

Create:

```text
docs/phases/phase_15l_deployment_execution_preparation_tuniatlas_rebrand_lock/agent_report.md
```

Use verdict:

```text
PASS / REPAIRED_PASS / BLOCKED / FAIL
```

Report:

- files changed
- brand replacements made
- logo/favicon status
- deployment decisions documented
- commands run and results
- old-name grep results and classification
- remaining risks
- commit recommendation
