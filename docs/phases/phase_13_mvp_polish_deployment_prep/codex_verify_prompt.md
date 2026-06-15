# Phase 13 Codex Verification Prompt — Strict Review and Repair

You are Codex verifying Phase 13 of TuniTech Abroad.

This is a strict review-and-repair pass. Do not trust the Gemini/agent report. Inspect the implementation, run the required commands, repair defects if safe, and write a final Codex report.

## Start with preflight

Run from project root:

```bash
pwd
git status --short --branch
echo "DOCKER_HOST=${DOCKER_HOST:-}"
docker ps
docker compose ps || true
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase13_codex_cache','ok',10); print('CACHE_VALUE=', cache.get('phase13_codex_cache'))"
```

If Docker/Podman/PostgreSQL/Redis/cache is blocked, attempt one safe start:

```bash
docker compose up -d postgres redis || docker compose up -d || true
```

Then retry DB/cache checks.

## Verdict rules

- PASS only if PostgreSQL-backed migrate and tests actually run and end OK.
- BLOCKED if Docker/PostgreSQL/Redis/cache is inaccessible and prevents required verification.
- FAIL if tests run and fail or critical defects remain.
- SQLite smoke tests are allowed only as supplementary diagnostics, not final acceptance.
- `Found 0 test(s)` is failure.
- Hidden 500s in test logs are failure unless explicitly expected by test.
- Stale `agent_report.md` with wrong verdict is failure and must be corrected.

## Docs and scope to read

Read:

- `AGENTS.md`
- `docs/phases/phase_13_mvp_polish_deployment_prep/tasks.md`
- `docs/phases/phase_13_mvp_polish_deployment_prep/acceptance.md`
- `docs/phases/phase_13_mvp_polish_deployment_prep/agent_report.md` if present
- relevant planning docs under `docs/planning/`

## Inspect implementation for these defects

Check for:

- Phase 14 deployment started accidentally
- real secrets in docs/settings/tests/templates/reports
- `.env` tracked
- public integer ID URLs
- CV file path or `file.url` exposed in templates/admin
- raw CV text exposed in admin/templates
- unsubscribe tokens exposed in admin/templates
- production settings breaking local development
- missing `collectstatic` readiness
- 404/500 pages leaking debug/internal paths/secrets
- broken URL names in templates
- missing routes for newly created templates
- hidden route 500s
- unsupported stack additions
- OpenRouter calls outside LLM services/tasks
- France Travail live calls in public search/admin list pages
- business logic moved into views/models/templates/admin actions
- Celery tasks containing business logic instead of calling services
- stale docs/report claiming false PASS/BLOCKED

## Required commands

Run all commands in `acceptance.md`. At minimum:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase13_codex_acceptance','ok',10); print('CACHE_VALUE=', cache.get('phase13_codex_acceptance'))"
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
python manage.py test apps.core --settings=config.settings.local
python manage.py test apps.accounts --settings=config.settings.local
python manage.py test apps.analytics --settings=config.settings.local
python manage.py test apps.skills --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.profiles --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.llm --settings=config.settings.local
python manage.py test apps.notifications --settings=config.settings.local
python manage.py test apps.privacy --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Run boundary checks:

```bash
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected OpenRouter runtime code"
grep -R "FranceTravailClient\|france_travail\|api.francetravail" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected France Travail runtime code"
grep -R "CVUpload.all_objects" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "CHECK all_objects usage"
grep -R "raw_text\|token\|secret\|password" apps/*/admin.py apps/*/templates docs/phases/phase_13_mvp_polish_deployment_prep --exclude-dir="__pycache__" -n || true
grep -R "cv.file.url\|file.url\|PRIVATE_MEDIA_ROOT" apps/*/templates apps/*/admin.py config --exclude-dir="__pycache__" -n || true
```

Run cleanup checks:

```bash
git diff --check
git check-ignore -v .env
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 4 -name "*.sqlite3" -print
find . -maxdepth 4 -name "celerybeat-schedule*" -print
find . -maxdepth 5 -name "agent_report.md.save" -print
```

Remove generated artifacts if needed.

## Repair authority

You may fix defects inside Phase 13 scope only.

Allowed fixes:

- route/template mismatch
- error/empty state bugs
- unsafe token/raw text/file exposure
- production settings parsing bugs
- test failures
- stale report status
- cleanup artifacts
- missing docs/checklist content

Do not:

- deploy
- add hosting provider
- start Phase 14
- add unrelated features
- replace stack
- print real secrets
- commit or push

## Final report

Create or update:

`docs/phases/phase_13_mvp_polish_deployment_prep/codex_review_report.md`

Include:

1. Verdict: PASS/BLOCKED/FAIL
2. Defects found
3. Fixes applied
4. Files changed
5. Commands run with exact results/test counts
6. Docker/PostgreSQL/Redis/cache status
7. Boundary grep interpretation
8. Artifact cleanup status
9. Remaining risks
10. Phase boundary confirmation

End with one marker:

- `<!-- CODEX_PHASE_13_PASS -->`
- `<!-- CODEX_PHASE_13_BLOCKED -->`
- `<!-- CODEX_PHASE_13_FAIL -->`
