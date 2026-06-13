# Phase 0 Acceptance — Repository and Local Environment Foundation

## Acceptance Gate

Phase 0 is accepted only if the repository foundation and local infrastructure are stable and the phase boundary was respected.

Do not accept Phase 0 if the agent implemented authentication, product models, job ingestion, CV upload, matching, recommendations, LLM, email delivery, or deployment.

## Required Files

The following files or directories must exist:

```text
README.md
.gitignore
.env.example
manage.py
config/
config/__init__.py
config/asgi.py
config/wsgi.py
config/urls.py
config/celery.py
config/settings/
config/settings/__init__.py
config/settings/base.py
config/settings/local.py
config/settings/production.py
apps/
apps/__init__.py
requirements/
requirements/base.txt
requirements/local.txt
requirements/production.txt
docker-compose.yml
docs/phases/phase_00_repository_foundation/tasks.md
docs/phases/phase_00_repository_foundation/prompt.md
docs/phases/phase_00_repository_foundation/acceptance.md
docs/phases/phase_00_repository_foundation/agent_report_template.md
```

## Forbidden Files or Scope in Phase 0

Phase 0 must not create or implement:

```text
apps/accounts/
apps/profiles/
apps/jobs/
apps/cvs/
apps/matching/
apps/recommendations/
apps/llm/
apps/notifications/
apps/privacy/
custom User model
django-allauth config
auth pages
job models
CV models
matching models
recommendation models
OpenRouter client
France Travail live client
email sending service
Django web Dockerfile or web service container
```

Exception: `apps/__init__.py` is required as a package placeholder.

## Critical Database Acceptance

Phase 0 must not lock the project into Django's default `auth.User`.

Run:

```bash
python manage.py dbshell --settings=config.settings.local
```

Then inspect tables with PostgreSQL:

```sql
\dt
```

Reject Phase 0 if an `auth_user` table was created before the custom User model exists.

Reason: Phase 1 owns the custom User model. Creating `auth_user` in Phase 0 creates migration debt and can break the clean auth foundation.

## Local Environment Setup Checks

Run from project root.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements/local.txt
```

Expected:

- virtual environment created
- dependencies installed
- no dependency using the wrong stack

## Docker Compose Checks

```bash
docker compose config
docker compose up -d postgres redis
docker compose ps
```

Expected:

- Compose config is valid.
- `postgres` service is running.
- `redis` service is running.
- No Django `web` service exists.

Redis check:

```bash
docker compose exec redis redis-cli ping
```

Expected:

```text
PONG
```

## Django Checks

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('database ok')"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase0_ping', 'ok', 30); print(cache.get('phase0_ping'))"
```

Expected:

```text
database ok
ok
```

## Celery Checks

Terminal 1:

```bash
source .venv/bin/activate
celery -A config worker -l info
```

Expected:

- worker starts
- worker connects to Redis broker
- no import errors

Terminal 2:

```bash
source .venv/bin/activate
celery -A config beat -l info --pidfile=
```

Expected:

- Beat starts
- no import errors

Terminal 3:

```bash
source .venv/bin/activate
python manage.py shell --settings=config.settings.local -c "from config.celery import debug_task; result = debug_task.delay(); print(result.get(timeout=10))"
```

Expected:

- debug task executes through worker
- output proves task completed

## Secret Handling Checks

```bash
git check-ignore .env
git check-ignore .env.local || true
grep -n "^!.env.example$" .gitignore
grep -R "OPENROUTER_API_KEY=.*[^=]" -n . --exclude-dir=.git --exclude=.env.example || true
grep -R "SECRET_KEY=.*[^=]" -n . --exclude-dir=.git --exclude=.env.example || true
```

Expected:

- `.env` is ignored.
- `.env.example` is not ignored.
- no real secret values are committed.
- settings read secrets from environment variables.

## README Acceptance

`README.md` must contain:

- project purpose
- stack summary
- local setup commands
- how to create `.env` from `.env.example`
- how to start PostgreSQL and Redis
- how to run Django checks
- how to run migrations
- how to start the Django server
- how to start Celery worker
- how to start Celery Beat
- clear statement: Docker Compose is only for PostgreSQL and Redis at this stage
- clear statement: no real secrets belong in Git

## Git Acceptance

```bash
git status --short
git branch --show-current
git check-ignore .env
```

Expected:

- branch is `dev` during active work unless Baha intentionally chose otherwise
- no generated junk is staged accidentally
- `.env` ignored

## Final Review Checklist

Reject the phase if any answer is no:

- Did the agent stay inside Phase 0?
- Did the agent avoid implementing auth and future product features?
- Did the agent avoid default auth_user lock-in?
- Did Django check pass?
- Did migrate pass?
- Did PostgreSQL run through Docker Compose?
- Did Redis run through Docker Compose?
- Did Celery worker start?
- Did Celery Beat start?
- Did debug task execute?
- Did `.env.example` avoid real secrets?
- Is `.env` gitignored?
- Is Django not Dockerized?
- Is README usable on Fedora/Linux/bash?

## Phase 0 Definition of Done

Phase 0 is done when:

- repository foundation exists
- local infrastructure works
- settings split is clean
- environment configuration is safe
- Docker Compose runs PostgreSQL and Redis only
- Django can connect to PostgreSQL
- Django can use Redis cache
- Celery worker and Beat can boot
- debug task executes through Celery
- no future phase was implemented
