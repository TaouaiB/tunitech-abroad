# Phase 12 Implementation Prompt — Admin Operations and Observability

You are implementing Phase 12 only for TuniTech Abroad.

## Role

Act as a strict senior Django implementation agent. You may work autonomously through all Phase 12 tickets. You must stop after Phase 12 and must not start Phase 13 or Phase 14.

## Non-negotiable stack

Use only:

- Django
- Django ORM
- PostgreSQL
- Redis
- Celery/Celery Beat if needed
- django-allauth
- Django templates
- HTMX/Tailwind only if existing templates require tiny integration

Do not add React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, SPA architecture, external monitoring SaaS, or deployment services.

## Architecture rules

- Views stay thin.
- Admin actions stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data and do not call external APIs.
- No OpenRouter/LLM calls from Django views or admin list pages.
- No France Travail live calls during normal user job search.
- Admin list pages must not call France Travail live.
- Public URLs use UUID `public_id`, never internal integer IDs.
- CV files are private and must not be publicly exposed.
- `CVUpload.objects` excludes soft-deleted CVs.
- `CVUpload.all_objects` is only for admin/privacy/deletion/internal tasks.
- Never print, commit, log, or document real secrets.

## Phase 12 scope

Goal: make the system operable through Django Admin and health checks.

Deliverables:

- Admin list filters/search.
- Admin actions.
- Health endpoint.
- Ingestion monitoring.
- LLM usage monitoring.
- Email monitoring.
- Unknown skill review.
- Basic event analytics.

Do not implement Phase 13 polish or Phase 14 deployment.

## Required first steps

1. Read `AGENTS.md`.
2. Read:
   - `docs/phases/phase_12_admin_observability/README.md`
   - `docs/phases/phase_12_admin_observability/tasks.md`
   - `docs/phases/phase_12_admin_observability/acceptance.md`
   - `docs/phases/phase_12_admin_observability/preflight.md`
3. Read relevant planning docs in `docs/planning/`.
4. Run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
docker ps || true
docker compose ps || true
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase12_preflight','ok',10); print('CACHE_VALUE=', cache.get('phase12_preflight'))"
```

If Docker is blocked but PostgreSQL-backed `migrate` works, continue and report Docker limitation honestly.

If PostgreSQL is unreachable, try to start Compose once:

```bash
docker compose up -d postgres redis || docker compose up -d || true
```

Then rerun `migrate`.

If PostgreSQL remains unreachable, stop with `BLOCKED`. Do not implement code and do not claim PASS.

## Autonomous repair loop

For this phase, use up to 8 repair loops:

1. Implement a logical block.
2. Run the relevant focused tests.
3. Inspect failures and logs.
4. Fix root cause, not symptoms.
5. Rerun failed tests.
6. Rerun full acceptance before final report.

Stop only when:

- all PostgreSQL-backed acceptance checks pass, or
- a real blocker prevents required checks.

Never claim success if:

- PostgreSQL tests did not run,
- Redis/health checks did not run and were not correctly mocked in tests,
- tests show `Found 0 test(s)`,
- only SQLite smoke tests passed,
- hidden 500s appear in route tests,
- stale `agent_report.md` says blocked/failed after final pass.

## Implementation guidance

### Admin coverage

Inspect all `admin.py` files before editing. Add or improve admin registrations for operational models. Use list displays, filters, search, readonly fields, ordering, and date hierarchy where helpful.

Avoid heavy list columns and PII exposure.

### Admin actions

Representative admin actions should call services or enqueue tasks. Good examples:

- reparse CV -> CV parsing task/service
- refresh recommendations -> recommendation service/task
- reprocess raw job/normalized job -> existing job normalization/extraction service/task
- mark unknown skills reviewed/ignored -> skill review service or minimal service if missing

Do not put business logic directly in `admin.py`.

### Health check

Implement/harden `apps/core/services/health.py` with `HealthCheckService.check()`. Add `/health/` returning JSON.

Healthy:

```json
{"status":"ok","database":"ok","redis":"ok"}
```

Degraded:

```json
{"status":"degraded","database":"error","redis":"ok"}
```

Use HTTP 200 for healthy, 503 for degraded. Do not expose exception details or secrets.

### Tests

Add tests for:

- staff admin access
- non-staff admin denial
- representative admin pages load
- representative admin actions delegate to service/task
- health endpoint healthy and degraded responses
- failed ingestion/freshness visibility if model fields exist
- failed CV parse visibility
- unknown skill review visibility/action
- LLM/email log visibility in admin

Use project conventions. Do not use `objects.create_user` if existing code avoids it.

## Required final acceptance

Run every command in `acceptance.md`.

Minimum required final commands:

```bash
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.core --settings=config.settings.local
python manage.py test apps.analytics --settings=config.settings.local
python manage.py test apps.skills --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.llm --settings=config.settings.local
python manage.py test apps.notifications --settings=config.settings.local
python manage.py test apps.privacy --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Then run:

```bash
git diff --check
git status --short
git check-ignore -v .env
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 4 -name "*.sqlite3" -print
find . -maxdepth 4 -name "celerybeat-schedule*" -print
find . -maxdepth 5 -name "agent_report.md.save" -print
```

## Final report

Create or update:

```text
docs/phases/phase_12_admin_observability/agent_report.md
```

Use the template in `agent_report_template.md`.

The report must include exact test counts and final PASS/BLOCKED/FAIL.

## Final output

End your response with exactly one of:

```text
<!-- PHASE_12_PASS -->
```

or

```text
<!-- PHASE_12_BLOCKED -->
```

or

```text
<!-- PHASE_12_FAIL -->
```

Do not use `<!-- GOAL_COMPLETE -->` unless you also include the correct Phase 12 marker.
