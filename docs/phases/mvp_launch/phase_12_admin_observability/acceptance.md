# Phase 12 Acceptance — Admin Operations and Observability

## Mandatory local acceptance

Run from Fedora terminal, not from a web shell.

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
```

## 1. Infrastructure visibility

```bash
docker ps
docker compose ps
```

This command may show Podman-backed Docker Compose on Fedora. That is acceptable.

If Compose cannot start containers but PostgreSQL/Redis are reachable, record it honestly. The final acceptance depends on Django-backed PostgreSQL tests passing, not on a pretty `docker compose ps` table.

## 2. Database and Redis preflight

```bash
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase12_cache_check','ok',10); print('CACHE_VALUE=', cache.get('phase12_cache_check'))"
```

Expected:

```text
DB_VENDOR= postgresql
CACHE_VALUE= ok
```

If Redis is unavailable, health endpoint tests may use mocks, but the final report must say Redis local preflight is blocked.

## 3. Migration check

```bash
python manage.py makemigrations --check --dry-run --settings=config.settings.local
```

Expected:

```text
No changes detected
```

If model changes are intentionally added, commit migrations. Do not edit old migration history.

## 4. Required app tests

Run every command. Do not use SQLite as final acceptance.

```bash
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

Rules:

- `Found 0 test(s)` is failure.
- A full-suite pass is not enough if Phase 12 tests were not discovered.
- Warnings/errors intentionally asserted by tests are acceptable only if the final result is `OK`.
- SQLite smoke checks can be used for debugging only, not final acceptance.

## 5. Health endpoint manual check

With Django server running:

```bash
python manage.py runserver 127.0.0.1:8000 --settings=config.settings.local
```

In another terminal:

```bash
curl -i http://127.0.0.1:8000/health/
```

Expected when DB and Redis are OK:

```text
HTTP/1.1 200 OK
```

Body should be JSON with database and Redis status. It must not include secrets, usernames, passwords, API keys, or stack traces.

## 6. Boundary greps

```bash
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected OpenRouter runtime code"
grep -R "FranceTravailClient\|france_travail\|api.francetravail" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected France Travail runtime code"
grep -R "CVUpload.all_objects" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "CHECK all_objects usage"
grep -R "password\|secret\|token" docs/phases/phase_12_admin_observability --exclude="acceptance.md" -n || true
```

Review grep output manually:

- `OpenRouter` should appear only in LLM service/log/admin visibility, not in views/admin list actions that call the API directly.
- `FranceTravailClient` should appear only in ingestion/service/task paths, not public search.
- `CVUpload.all_objects` should be limited to admin/privacy/deletion/internal parse retry paths.
- Do not include real secret values in phase docs.

## 7. Artifact cleanup

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

Expected:

- `git diff --check` prints nothing.
- `.env` is ignored.
- No cache/artifact files are printed.
- `git status --short` shows only intentional Phase 12 files.

## 8. Final acceptance standard

Phase 12 is PASS only when:

- PostgreSQL-backed migrations and tests pass.
- Phase 12 tests are discovered and pass.
- Health endpoint works.
- Admin access/actions are tested.
- No phase boundary violations exist.
- `agent_report.md` and `codex_review_report.md` agree with actual test output.

If PostgreSQL, Redis, Docker/Podman, or permissions block required commands, final status is:

```text
BLOCKED
```

not PASS.
