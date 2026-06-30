# Preflight

Run from repo root.

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
```

## 1. Git state

```bash
git status --short --branch
git branch --show-current
```

Rules:

- Must be on `dev`.
- Do not commit.
- Do not push.
- If there are uncommitted user changes, preserve them.

## 2. Python/Django sanity

```bash
python --version
python manage.py check --settings=config.settings.local
```

## 3. Database and Redis reachability

Try current services first:

```bash
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase14a_cache_check','ok',10); print('CACHE_VALUE=', cache.get('phase14a_cache_check'))"
```

If DB/Redis are blocked, make one safe start attempt:

```bash
docker compose up -d postgres redis || docker compose up -d || true
```

Then retry the two shell checks.

If Docker/Podman socket permission or port conflicts block startup, report exact blocker and stop with `BLOCKED_DB` or `BLOCKED_REDIS`.

## 4. Migrations and tests baseline

```bash
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Rules:

- `Found 0 test(s)` is failure.
- A stale report claiming pass is not evidence.
- Failing tests must be fixed root-cause first.

## 5. Route inventory

```bash
python manage.py show_urls --settings=config.settings.local 2>/dev/null | sort | grep -E "jobs|dashboard|match|recommend|cv|privacy|email|health|explain" || true
```

If `show_urls` is not installed, do not add dependency just for this. Use Django resolver inspection from shell or grep URL files.

## 6. Existing issue probes

```bash
python manage.py shell --settings=config.settings.local -c "from django.conf import settings; print('LLM_ENABLED=', getattr(settings, 'LLM_ENABLED', None)); print('HAS_OPENROUTER_API_KEY=', bool(getattr(settings, 'OPENROUTER_API_KEY', ''))); print('HAS_FT_CLIENT_ID=', bool(getattr(settings, 'FRANCE_TRAVAIL_CLIENT_ID', ''))); print('HAS_FT_CLIENT_SECRET=', bool(getattr(settings, 'FRANCE_TRAVAIL_CLIENT_SECRET', '')))"
python manage.py shell --settings=config.settings.local -c "from django.apps import apps; print('LLM_MODELS=', [m.__name__ for m in apps.get_app_config('llm').get_models()]) if apps.is_installed('apps.llm') else print('LLM app not installed')"
python manage.py help | grep -i -E "france|travail|ingest|sync|job|llm|cv|recommend" || true
```

Do not print actual secret values.

## 7. Static architecture smoke

```bash
grep -R "requests\.\|urllib\|OpenRouter\|FranceTravail" apps --exclude-dir="__pycache__" -n || true
grep -R "CVUpload.all_objects" apps --exclude-dir="__pycache__" -n || true
grep -R "recommendations/" templates apps --exclude-dir="__pycache__" -n || true
```

Interpret results. Do not blindly remove valid service-layer usage.
