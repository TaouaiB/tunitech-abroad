# Phase 12 Codex Verification Prompt — Strict Review and Repair

You are Codex verifying Phase 12 for TuniTech Abroad.

This is a review-and-repair pass. Do not rubber-stamp Gemini's report. Inspect the code, run required checks, fix defects inside Phase 12 scope, and produce a review report.

## Hard scope

Verify and repair Phase 12 only:

```text
Phase 12 — Admin Operations and Observability
```

Allowed:

- Django Admin registrations/actions.
- Health endpoint and health service.
- Admin/observability tests.
- Minimal services needed to keep admin actions thin.
- Report/documentation updates inside Phase 12 folder.

Forbidden:

- Phase 13 polish.
- Phase 14 deployment.
- Public UI redesign.
- Production settings/hosting/domain/HTTPS.
- External monitoring SaaS.
- Live France Travail calls from public search or admin list pages.
- Direct OpenRouter calls from views/admin actions.
- Committing/pushing.

## Source docs to read

First read:

```bash
pwd
rg --files -g 'AGENTS.md' -g 'docs/phases/phase_12_admin_observability/**' -g 'docs/planning/**'
```

Then inspect:

```text
AGENTS.md
docs/phases/phase_12_admin_observability/tasks.md
docs/phases/phase_12_admin_observability/acceptance.md
docs/phases/phase_12_admin_observability/agent_report.md if present
docs/planning/ relevant roadmap/PRD/service contracts/page map
```

## Infrastructure requirement

Before judging code, run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
docker ps || true
docker compose ps || true
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase12_codex_cache_check','ok',10); print('CACHE_VALUE=', cache.get('phase12_codex_cache_check'))"
```

If Docker is blocked but PostgreSQL and Redis/cache are reachable, continue and report Docker limitation honestly.

If PostgreSQL is unreachable, try once:

```bash
docker compose up -d postgres redis || docker compose up -d || true
python manage.py migrate --settings=config.settings.local
```

If PostgreSQL remains unreachable, do static/code review and optional compile checks, but final verdict must be BLOCKED. Do not claim PASS from SQLite.

## What to inspect

Inspect all changed and relevant files:

```bash
git status --short
find apps -maxdepth 3 -name admin.py -o -path '*/services/*.py' -o -name urls.py -o -name views.py -o -name tests.py | sort
```

Review specifically:

- `apps/*/admin.py`
- `apps/core/services/health.py`
- health endpoint URL/view
- tests for admin access/actions and health
- `apps/jobs`, `apps/cvs`, `apps/skills`, `apps/recommendations`, `apps/llm`, `apps/notifications`, `apps/privacy`, `apps/analytics`

## Required architecture checks

Fail or repair if:

- Admin actions contain business logic instead of calling services/tasks.
- Health view contains all health logic instead of calling `HealthCheckService`.
- Admin list pages call France Travail live.
- Admin actions call OpenRouter directly.
- CV files become publicly exposed.
- Raw CV text appears in admin list displays.
- Secrets/tokens/API keys are logged/displayed in admin or phase docs.
- Public URLs expose integer IDs.
- `CVUpload.all_objects` is used outside admin/privacy/deletion/internal parse retry/test paths.
- `objects.create_user` appears where project style forbids it.
- Models call external APIs.
- Celery tasks contain business logic.
- `Found 0 test(s)` appears for Phase 12/current tests.
- Old migration history was edited incorrectly.

## Required command set

Run PostgreSQL-backed commands. Do not use SQLite as final acceptance.

```bash
source .venv/bin/activate
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

If a command fails, inspect and repair root cause. Rerun the failed command, then rerun the full command set.

## Health endpoint check

If `/health/` exists, test it with Django test client or `curl` if server is running. Confirm:

- 200 when healthy.
- 503 when DB or Redis mocked as failing.
- JSON response.
- No secrets.

## Boundary greps

Run:

```bash
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected OpenRouter runtime code"
grep -R "FranceTravailClient\|france_travail\|api.francetravail" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected France Travail runtime code"
grep -R "CVUpload.all_objects" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "CHECK all_objects usage"
grep -R "password\|secret\|token" docs/phases/phase_12_admin_observability -n || true
```

Interpret, do not blindly pass. The phase docs may contain words like `secret` as warnings, but must not contain real values.

## Artifact checks

Run:

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

Clean accidental artifacts if present.

## Report

Create:

```text
docs/phases/phase_12_admin_observability/codex_review_report.md
```

The report must include:

1. Verdict: PASS / BLOCKED / FAIL.
2. Defects found.
3. Fixes applied.
4. Files changed.
5. Commands run and final results with test counts.
6. Docker/PostgreSQL/Redis status.
7. Boundary grep results.
8. Artifact cleanup status.
9. Remaining risks.
10. Confirmation Phase 13/14 were not started.

## Verdict rules

Use `PASS` only if PostgreSQL-backed acceptance ran and passed.

Use `BLOCKED` if:

- PostgreSQL was unreachable,
- Redis/cache was unreachable and required checks could not be completed,
- Docker/Podman permissions blocked infrastructure and required DB tests could not run.

Use `FAIL` if tests ran and code still fails after repair loops.

Do not claim PASS from:

- SQLite-only smoke tests,
- `manage.py check` only,
- static greps only,
- agent report claims.

Final response must end with one of:

```text
<!-- CODEX_PHASE_12_PASS -->
```

```text
<!-- CODEX_PHASE_12_BLOCKED -->
```

```text
<!-- CODEX_PHASE_12_FAIL -->
```
