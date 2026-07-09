# Phase 15I Tasks — Production Readiness and Deployment Plan

## Task 0 — Preflight

Run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
```

Rules:

- Work only on `dev`.
- Do not deploy.
- Do not read, print, modify, or commit `.env`.
- Do not add real secrets anywhere.
- Do not create server-specific files with real IP/domain/secrets.
- Do not start Phase 15J.

## Task 1 — Production environment policy

Update `.env.example` and/or create `docs/deployment/production_env_policy.md`.

Required production policy:

```env
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production

LLM_ENABLED=True
CV_LLM_EXTRACTION_ENABLED=False
JOB_ENRICHMENT_ENABLED=False
JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=0
JOB_ENRICHMENT_DAILY_LIMIT=0
OPENROUTER_CIRCUIT_BREAKER_ENABLED=True
OPENROUTER_ENRICHMENT_RATE_LIMIT=1/m
```

Important:

- Keep LLM code available.
- Disable automatic token spending by default.
- User-facing search/matching must still use local PostgreSQL and deterministic services.
- No OpenRouter from views/templates/models/admin display.
- No France Travail live calls during public search.

`.env.example` must use placeholders only.

Forbidden examples:

```env
OPENROUTER_API_KEY=sk-or-real-value
EMAIL_HOST_PASSWORD=real-password
FRANCE_TRAVAIL_CLIENT_SECRET=real-secret
```

## Task 2 — Static/private media deployment rules

Create/update deployment docs explaining:

- Whitenoise serves static files only.
- CV/private files are not static files.
- Caddy/Nginx must not expose `private_media`.
- CV downloads/status routes must enforce authentication and ownership.
- `CVUpload.objects` excludes soft-deleted CVs.
- `CVUpload.all_objects` is admin/privacy/internal only.

Required doc:

```text
docs/deployment/static_private_media_policy.md
```

## Task 3 — Rate limiting / abuse controls plan

Create:

```text
docs/deployment/rate_limiting_abuse_controls.md
```

Cover at minimum:

- login
- signup
- password reset
- CV upload
- quick match
- recommendation refresh
- save/unsave job
- email/unsubscribe/contact actions
- admin endpoints

Preferred MVP approach:

- Django/Redis cache-backed rate-limit service.
- Thin views call service.
- No heavy dependency unless justified.
- Caddy/Nginx may add coarse IP limits later, but app-level guardrails are still required for user-specific actions.

If current code already has rate limiting, document it. If missing, create clear Phase 15I/15J TODOs. Do not overbuild unless the implementation is small, safe, and well-tested.

## Task 4 — Monitoring and health checks plan

Create:

```text
docs/deployment/monitoring_healthchecks.md
```

Must cover:

- web health endpoint
- Gunicorn systemd status
- Celery worker status
- Celery beat status
- Redis availability
- PostgreSQL connectivity
- Celery heartbeat freshness
- ingestion success/failure
- queue/pending/stale processing counts
- disk usage
- backup success/failure
- error logs

Do not integrate paid monitoring yet. Provide MVP steps and future options.

## Task 5 — Backup and restore policy

Create:

```text
docs/deployment/backup_restore_policy.md
```

Minimum policy:

- daily PostgreSQL dump
- daily private media archive
- encrypted backup storage
- keep 7 daily + 4 weekly backups
- backup logs
- restore test before public launch
- rollback notes

Do not include real backup credentials or bucket names.

## Task 6 — Privacy final review checklist

Create:

```text
docs/deployment/privacy_final_review.md
```

Must check:

- CV files private
- user ownership on CV/match/saved jobs/recommendations
- soft-deleted CVs excluded from normal manager
- account deletion flow
- CV deletion flow
- email unsubscribe flow
- admin-only access to sensitive dashboards
- logs do not include CV text, LLM raw prompts, real secrets, access tokens

## Task 7 — Legal wording final pass

Create:

```text
docs/deployment/legal_wording_final_pass.md
```

Required wording principles:

- no visa guarantee
- no job guarantee
- no relocation guarantee
- recommendations are informational
- fit score is rule-based support, not an employment decision
- LLM suggestions are assistive, not final decision-making
- France-first/Tunisian IT positioning is clear
- privacy statement for CV/profile data is clear

This can be MVP wording. It does not replace lawyer review.

## Task 8 — Email/OAuth/domain checklist

Create:

```text
docs/deployment/email_oauth_domain_checklist.md
```

Must cover:

- production domain placeholders
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- Google OAuth callback URLs
- GitHub OAuth callback URLs
- email sender/domain setup
- unsubscribe URL correctness
- no real secrets in docs

## Task 9 — Phase 15J deployment runbook outline

Create:

```text
docs/deployment/phase_15j_deployment_runbook_outline.md
```

Target architecture:

- Hetzner VPS
- Fedora/Ubuntu server acceptable, but commands should be Linux/bash-oriented
- Caddy as HTTPS reverse proxy
- Gunicorn for Django
- PostgreSQL and Redis
- Celery worker and Celery beat under systemd
- Whitenoise for static assets
- private media protected by Django, not public web server

This is an outline only. Do not run server commands.

## Task 10 — Production smoke checklist

Create:

```text
docs/deployment/production_smoke_checklist.md
```

Must cover after-deployment checks:

- homepage
- login/logout
- Google/GitHub OAuth
- jobs list/search/detail
- `Plus pertinentes`
- quick match
- CV upload/delete
- profile page
- recommendations
- saved jobs
- admin operations dashboard
- email unsubscribe
- health endpoint
- Celery heartbeat
- ingestion dry/manual command
- private media cannot be accessed directly
- no LLM token burn unless explicitly enabled

## Task 11 — Verification commands

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

If any command fails, repair only in-scope issues or report clearly.

## Task 12 — Reports

Gemini creates:

```text
docs/phases/phase_15i_production_readiness_deployment_plan/agent_report.md
```

GLM reviewer creates:

```text
docs/phases/phase_15i_production_readiness_deployment_plan/glm_review_report.md
```

Do not create `codex_report.md`.
