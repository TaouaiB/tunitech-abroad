# Phase 0 Tasks — Repository and Local Environment Foundation

## Phase Goal

Create the local development foundation for TuniTech Abroad.

Phase 0 must stop after the repository, Django skeleton, PostgreSQL, Redis, Celery, Celery Beat, environment configuration, and local setup documentation are stable.

Do not implement product features in this phase.

## Phase Scope

Included:

- Git repository foundation
- `README.md`
- `.gitignore`
- `.env.example`
- Python dependency files
- Django project skeleton
- `config/` package
- `apps/` package
- settings split: base/local/production
- Docker Compose for PostgreSQL and Redis only
- Redis-backed Django cache
- Celery app configuration
- Celery Beat startup configuration
- local logging basics
- local setup commands for Fedora/Linux/bash
- basic health/debug checks for local infrastructure

Excluded:

- custom User model
- django-allauth configuration
- auth pages
- accounts app
- CandidateProfile
- EmailPreference
- admin customization
- job models
- job ingestion
- public job search
- CV upload
- matching
- recommendations
- OpenRouter integration
- email delivery
- privacy deletion flows
- production deployment
- Django web Docker container

## Critical Phase 0 Constraint: Avoid Default Auth Lock-In

Phase 1 owns the custom User model.

Do not accidentally lock the project into Django's default `auth.User` by applying auth migrations before the custom User model exists.

Acceptable Phase 0 approach:

- create the Django project skeleton with minimal installed apps needed for local infrastructure checks;
- keep `django.contrib.auth`, `django.contrib.admin`, and `allauth` out of Phase 0 migrations;
- do not create an `accounts` app yet;
- do not run migrations that create the default `auth_user` table.

`python manage.py migrate` must pass for the Phase 0 minimal app set, but it must not create auth/user tables that conflict with Phase 1.

Phase 1 will introduce the custom User model before auth/admin/allauth are enabled.

## Ticket TTA-0001 — Create Project Repository

Priority: P0  
Type: setup

### Description

Create the Git repository foundation for TuniTech Abroad.

### Required Work

- Initialize Git if the repository does not already exist.
- Create or preserve `main` and `dev` branch workflow.
- Create `README.md` with local setup instructions.
- Create `.gitignore` with Python, Django, virtualenv, environment, cache, editor, OS, and local media exclusions.
- Add `docs/` structure if missing.
- Add this phase documentation under:

```text
docs/phases/phase_00_repository_foundation/
```

### Acceptance Criteria

- Repository exists.
- `README.md` exists.
- `.gitignore` exists.
- `.env` and `.env.*` are ignored except `.env.example`.
- No secrets are committed.
- `docs/phases/phase_00_repository_foundation/` exists.

### Test Expectations

- `git status` shows no accidental generated junk after setup.
- `git check-ignore .env` confirms `.env` is ignored.
- `.env.example` is tracked or trackable.

## Ticket TTA-0002 — Create Django Project Skeleton

Priority: P0  
Type: setup

### Description

Create a Django project structure with `config/` and `apps/`.

### Required Work

Recommended structure:

```text
.
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
```

### Required Settings Rules

- Use `config.settings.local` for local development.
- Read configuration from environment variables.
- Keep `SECRET_KEY` out of committed code.
- Use PostgreSQL as the local database.
- Configure Redis cache from `REDIS_URL`.
- Configure timezone and language safely for MVP.
- Do not enable allauth yet.
- Do not create custom User yet.
- Do not enable auth/admin migrations that create default `auth_user`.

### Acceptance Criteria

- `manage.py` exists.
- `config/settings/` split exists.
- `apps/` package exists.
- Django loads with `config.settings.local`.
- `python manage.py check --settings=config.settings.local` passes.

### Test Expectations

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
```

## Ticket TTA-0003 — Configure Local PostgreSQL and Redis

Priority: P0  
Type: setup

### Description

Add Docker Compose for PostgreSQL and Redis.

### Required Work

- Create `docker-compose.yml` with only:
  - PostgreSQL
  - Redis
- Do not create a Django web service/container.
- Use named volumes for database persistence.
- Use local exposed ports:
  - PostgreSQL: `5432`
  - Redis: `6379`
- Configure Django database via environment variables.
- Configure Redis cache via environment variables.
- Add safe local defaults only where useful. Do not use real secrets.

### Acceptance Criteria

- `docker-compose.yml` exists.
- PostgreSQL container starts.
- Redis container starts.
- Django connects to PostgreSQL.
- Django can use Redis cache.

### Test Expectations

```bash
docker compose up -d postgres redis
docker compose ps
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('database ok')"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase0_ping', 'ok', 30); print(cache.get('phase0_ping'))"
docker compose exec redis redis-cli ping
```

Expected Redis response:

```text
PONG
```

## Ticket TTA-0004 — Configure Celery and Celery Beat

Priority: P0  
Type: setup

### Description

Set up Celery and Celery Beat with Redis broker.

### Required Work

- Create `config/celery.py`.
- Load Django settings inside Celery.
- Use Redis as Celery broker.
- Use Redis as Celery result backend for local development.
- Add a minimal debug task inside `config/celery.py` or another Phase 0-safe location.
- Ensure Celery autodiscovery is wired but do not create future app tasks.
- Ensure Celery worker can start.
- Ensure Celery Beat can start.

### Acceptance Criteria

- Celery app is configured.
- Worker starts.
- Beat starts.
- A debug task can run through Redis.
- No business logic lives in Celery tasks.

### Test Expectations

Terminal 1:

```bash
docker compose up -d postgres redis
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

Expected result must prove the task executed through Celery, not eager/local fake execution.

## Ticket TTA-0005 — Add Environment Configuration

Priority: P0  
Type: setup

### Description

Create `.env.example` and settings split with environment-based configuration.

### Required Work

- Create `.env.example` with variable names only or safe placeholders.
- Do not create `.env`.
- Configure settings to read from environment variables.
- Fail clearly if required environment variables are missing.
- Provide local setup instructions telling Baha to create `.env` manually.
- Create `requirements/base.txt`, `requirements/local.txt`, and `requirements/production.txt`.
- Add local developer commands to README.

### Minimum `.env.example` Variables

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

Secrets must stay blank in `.env.example`.

### Acceptance Criteria

- `.env.example` exists.
- `.env` is not committed.
- settings split exists.
- project starts using environment values.
- no secrets are hardcoded.

### Test Expectations

```bash
grep -n "^\.env$" .gitignore
git check-ignore .env
python manage.py check --settings=config.settings.local
```

## Final Phase 0 Stop Point

Stop after all of this is true:

- Django starts.
- PostgreSQL connects.
- Redis connects.
- Celery worker starts.
- Celery Beat starts.
- `python manage.py check --settings=config.settings.local` passes.
- `python manage.py migrate --settings=config.settings.local` passes without default auth lock-in.
- No auth, jobs, CV, matching, recommendations, LLM, email, privacy, or deployment features were implemented.
