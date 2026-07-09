# Phase 13 Acceptance Criteria

## Phase acceptance result definitions

- PASS: all required PostgreSQL-backed commands run and end OK, no critical route/template/security/CV privacy defects remain.
- BLOCKED: infrastructure prevents PostgreSQL/Redis/cache/test verification.
- FAIL: commands run but tests/checks fail or critical defects remain.

## Required commands

Run from project root:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

echo "DOCKER_HOST=${DOCKER_HOST:-}"
docker ps
docker compose ps || true

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase13_acceptance','ok',10); print('CACHE_VALUE=', cache.get('phase13_acceptance'))"
```

Expected:

```text
DB_VENDOR= postgresql
CACHE_VALUE= ok
```

## Required tests

Run all that exist. If an app has zero tests unexpectedly, report it.

```bash
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

## Frontend/route checks

Use Django test client tests where possible. Manual browser checks are allowed in final report for visual/responsive review.

Critical routes that should not 500:

- `/`
- `/jobs/`
- at least one job detail route using `public_id` when fixture data exists
- `/accounts/login/`
- `/accounts/signup/`
- `/dashboard/`
- `/dashboard/account/`
- `/dashboard/settings/delete-account/`
- `/privacy/`
- `/terms/`
- `/health/`
- `/admin/` redirects for anonymous user

## Security and privacy greps

```bash
grep -R "objects\.create_user" apps --exclude-dir="__pycache__" -n || echo "OK no objects.create_user"
grep -R "OpenRouter\|openrouter" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected OpenRouter runtime code"
grep -R "FranceTravailClient\|france_travail\|api.francetravail" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "OK no unexpected France Travail runtime code"
grep -R "CVUpload.all_objects" apps --exclude-dir="tests" --exclude-dir="__pycache__" -n || echo "CHECK all_objects usage"
grep -R "raw_text\|token\|secret\|password" apps/*/admin.py apps/*/templates --exclude-dir="__pycache__" -n || true
```

Interpretation:

- OpenRouter references are allowed only in `apps/llm` services/models/tasks/tests/docs.
- France Travail references are allowed only in ingestion/source service paths and commands/tasks, not public job search views/templates/admin lists.
- `CVUpload.all_objects` is allowed only for admin/privacy/deletion/internal tasks.
- Admin/templates must not expose unsubscribe tokens, secrets, passwords, raw CV text, or CV file paths.

## Static/private media checks

```bash
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local

grep -R "PRIVATE_MEDIA_ROOT\|PRIVATE_MEDIA_URL\|MEDIA_URL" config apps --exclude-dir="__pycache__" -n || true
grep -R "cv.file.url\|file.url\|raw_text" apps/*/templates apps/*/admin.py --exclude-dir="__pycache__" -n || true
```

No public route should serve private CV files.

## Artifact cleanup

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

These should print no unwanted artifacts except `.env` must be ignored.

## Manual UX checks

Document results in `agent_report.md`:

- mobile-ish width check for home/jobs/dashboard/CV/recommendations
- empty state checks
- validation message checks
- French wording pass
- 404/500 page visual check

## Stop/Go gate

Do not accept Phase 13 if:

- full PostgreSQL-backed tests did not run
- any critical page 500s
- private CV files are publicly linkable
- public routes expose integer IDs
- `.env` appears in git status
- Phase 14 deployment work was started
