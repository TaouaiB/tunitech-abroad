# TuniTech Abroad

**France-first job intelligence platform for Tunisian IT candidates.**

TuniTech Abroad matches Tunisian IT developers, students, bootcamp graduates, internship seekers, and junior/mid-level engineers with France IT jobs and internships — providing CV parsing, job matching, missing-skill detection, and personalised recommendations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5 (modular monolith) |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Task queue | Celery 5 + Celery Beat |
| Frontend | Django templates + HTMX + Alpine.js |
| CSS | Tailwind CSS |
| Infrastructure | Docker Compose (Postgres + Redis only in early phases) |
| Python | 3.12+ |

> **Important:** Docker Compose is used **only** for PostgreSQL and Redis.
> Django, Celery, and Celery Beat run **locally**, not inside Docker.

---

## Prerequisites

- Fedora / Linux
- Python 3.12+
- Docker + Docker Compose plugin
- Git

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/tunitech-abroad.git
cd tunitech-abroad
```

### 2. Create the Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/local.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Then open `.env` and fill in the required values:

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | **Yes** | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `POSTGRES_PASSWORD` | **Yes** | Password for the local PostgreSQL user |
| `DJANGO_DEBUG` | No | `True` for local (default) |
| `REDIS_URL` | No | Defaults to `redis://localhost:6379/0` |

> **Never commit `.env` or put real secrets in `.env.example`.**

### 4. Start PostgreSQL and Redis

```bash
docker compose up -d postgres redis
docker compose ps
```

Verify Redis:

```bash
docker compose exec redis redis-cli ping
# Expected: PONG
```

### 5. Run Django checks and migrations

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
```

### 6. Verify database and cache connections

```bash
# PostgreSQL
python manage.py shell --settings=config.settings.local \
  -c "from django.db import connection; connection.ensure_connection(); print('database ok')"

# Redis cache
python manage.py shell --settings=config.settings.local \
  -c "from django.core.cache import cache; cache.set('ping', 'ok', 30); print(cache.get('ping'))"
```

### 7. Start the Django development server

```bash
source .venv/bin/activate
python manage.py runserver --settings=config.settings.local
```

Visit: <http://localhost:8000/health/>

---

## Celery

Open **two** additional terminals.

**Terminal 1 — Celery Worker:**

```bash
source .venv/bin/activate
celery -A config worker -l info
```

**Terminal 2 — Celery Beat (scheduler):**

```bash
source .venv/bin/activate
celery -A config beat -l info --pidfile=
```

**Verify Celery (Terminal 3):**

```bash
source .venv/bin/activate
python manage.py shell --settings=config.settings.local \
  -c "from config.celery import debug_task; result = debug_task.delay(); print(result.get(timeout=10))"
```

---

## Stopping services

```bash
docker compose down
```

To remove data volumes:

```bash
docker compose down -v
```

---

## Project Structure

```
.
├── manage.py
├── config/
│   ├── __init__.py        # Loads Celery app on Django startup
│   ├── asgi.py
│   ├── celery.py          # Celery app + debug task
│   ├── urls.py
│   ├── wsgi.py
│   └── settings/
│       ├── base.py        # Shared settings (reads from env vars)
│       ├── local.py       # Local overrides
│       └── production.py  # Production hardening
├── apps/
│   └── __init__.py        # Package placeholder
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
├── docker-compose.yml     # PostgreSQL + Redis only
├── .env.example           # Variable names — no real secrets
├── .gitignore
└── docs/
    └── phases/
        └── phase_00_repository_foundation/
```

---

## Git Workflow

```
main   — stable, reviewed code
dev    — active development
```

Commit convention:

```bash
git commit -m "Complete Phase 0 repository foundation"
```

---

## Security Notes

- `.env` is **gitignored**. Never commit it.
- All secrets are read from environment variables.
- No secrets are hardcoded anywhere in the codebase.
- CV files (future phases) will be private and never publicly exposed.
