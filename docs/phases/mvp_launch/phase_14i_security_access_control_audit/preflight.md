# Phase 14I Preflight

Run from repo root before implementation and before verification.

## 1. Confirm branch and clean state

```bash
cd ~/Projects/tunitech-abroad
git branch --show-current
git status --short
```

Expected:

```text
branch = dev
working tree should be clean or only contain intentional current phase docs/changes
```

Do not work directly on `main`.

## 2. Activate Python environment

```bash
source .venv/bin/activate
python --version
python -m pip --version
```

## 3. Start PostgreSQL and Redis

Use the repo's existing compose setup. On Fedora with Docker-compatible Podman, this is usually:

```bash
docker compose up -d
```

If the repo uses explicit Podman Compose commands, use the existing project convention.

Confirm containers/services:

```bash
docker ps
```

Redis is expected to be available for cache/broker. PostgreSQL must be the test database backend; do not silently switch to SQLite.

## 4. Baseline checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
```

If baseline fails before changes, document it in the report before fixing. Fix root cause only if inside Phase 14I or needed to run Phase 14I security tests.

## 5. Baseline security greps

```bash
grep -R "FranceTravailClient\|france_travail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

Document every non-empty result.
