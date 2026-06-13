# Phase 0 Agent Prompt — Repository and Local Environment Foundation

Paste this prompt into Antigravity/Gemini/Codex when starting Phase 0.

---

You are implementing Phase 0 only for TuniTech Abroad.

Read first:

1. `AGENTS.md`
2. `docs/phases/phase_00_repository_foundation/tasks.md`
3. `docs/phases/phase_00_repository_foundation/acceptance.md`
4. relevant planning PDFs in `docs/planning/`, especially:
   - Working Agreement v1
   - Implementation Roadmap v1
   - MVP Backlog v1
   - Service Contracts v1

## Mission

Implement Phase 0 only: repository and local environment foundation.

Tickets to complete:

- TTA-0001 — Create project repository
- TTA-0002 — Create Django project skeleton
- TTA-0003 — Configure local PostgreSQL and Redis
- TTA-0004 — Configure Celery and Celery Beat
- TTA-0005 — Add environment configuration

You may complete all tickets in this phase automatically. Do not ask for approval between tickets.

## Hard Stop Boundary

Stop after Phase 0.

Do not implement Phase 1 or any future phase.

Forbidden in Phase 0:

- custom User model
- django-allauth configuration
- accounts app
- login/signup/logout pages
- CandidateProfile
- EmailPreference
- admin customization
- job models
- France Travail live client
- job ingestion
- public job search
- CV upload/parsing
- matching
- recommendations
- OpenRouter/LLM
- email delivery
- privacy deletion
- deployment
- Django web Docker container

## Critical Django Auth Warning

Phase 1 owns the custom User model.

Do not create a default `auth_user` table in Phase 0.

Do not apply Django auth/admin migrations before the custom User model exists.

For Phase 0, use a minimal Django app configuration that allows:

- Django settings to load
- PostgreSQL connection check
- Redis cache check
- migrations to run for the minimal Phase 0 app set
- Celery worker/Beat startup

Do not enable `django.contrib.auth`, `django.contrib.admin`, or `allauth` in a way that creates default auth tables during Phase 0.

Phase 1 will add the custom User model before auth/admin/allauth are enabled.

## Docker Rule

Use Docker Compose only for PostgreSQL and Redis.

Do not Dockerize Django.

Allowed services in `docker-compose.yml`:

- `postgres`
- `redis`

Run locally:

- Django server
- Celery worker
- Celery Beat
- Tailwind watcher later

## Required Structure

Create or verify this structure:

```text
.
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── manage.py
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py
│   ├── urls.py
│   ├── wsgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── local.py
│       └── production.py
├── apps/
│   └── __init__.py
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
└── docs/
    └── phases/
        └── phase_00_repository_foundation/
            ├── tasks.md
            ├── prompt.md
            ├── acceptance.md
            └── agent_report_template.md
```

## Dependencies

Use stable Django ecosystem packages only.

Expected base dependencies:

```text
Django
psycopg[binary]
redis
celery
django-environ or python-decouple
```

Local/dev dependencies may include:

```text
pytest
pytest-django
ruff
```

Do not add frontend build complexity in Phase 0 unless the planning docs already require a placeholder only. Tailwind implementation is not Phase 0.

## Environment Configuration

Create `.env.example` only. Do not create `.env`.

`.env.example` must not contain real secrets.

Minimum variables:

```dotenv
DJANGO_ENV=
DJANGO_SETTINGS_MODULE=
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DJANGO_ALLOWED_HOSTS=

POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
DATABASE_URL=

REDIS_URL=
CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=

OPENROUTER_API_KEY=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
FRANCE_TRAVAIL_CLIENT_ID=
FRANCE_TRAVAIL_CLIENT_SECRET=
```

`.gitignore` must include:

```gitignore
.env
.env.*
!.env.example
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
media/
staticfiles/
```

## README Requirements

Write a practical Fedora/Linux/bash README section with commands for:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements/local.txt
cp .env.example .env
# Baha fills .env manually

docker compose up -d postgres redis
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py runserver
celery -A config worker -l info
celery -A config beat -l info --pidfile=
```

Do not include real secret values in README.

## Required Checks

Run checks as you work. If a check fails, fix it and rerun.

Minimum final commands:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
docker compose up -d postgres redis
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('database ok')"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase0_ping', 'ok', 30); print(cache.get('phase0_ping'))"
docker compose exec redis redis-cli ping
```

Celery manual checks require separate terminals:

Terminal 1:

```bash
source .venv/bin/activate
celery -A config worker -l info
```

Terminal 2:

```bash
source .venv/bin/activate
celery -A config beat -l info --pidfile=
```

Terminal 3:

```bash
source .venv/bin/activate
python manage.py shell --settings=config.settings.local -c "from config.celery import debug_task; result = debug_task.delay(); print(result.get(timeout=10))"
```

## Final Report

After implementation, fill:

```text
docs/phases/phase_00_repository_foundation/agent_report_template.md
```

Your final response must include:

1. completed tickets
2. files created/changed
3. commands run
4. final check results
5. remaining risks/manual steps

Do not include secrets.

## Final Stop Instruction

When all checks pass, stop. Do not start Phase 1.
