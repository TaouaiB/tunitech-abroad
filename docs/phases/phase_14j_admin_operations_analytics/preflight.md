# Phase 14J Preflight

Run before implementation.

## 1. Confirm branch

```bash
git branch --show-current
git status --short
```

Must be on `dev`, not `main`.

## 2. Confirm services

Use the local setup. PostgreSQL and Redis must be available.

```bash
docker compose ps
ss -ltnp '( sport = :5432 or sport = :6380 )' || true
```

If services are not running:

```bash
docker compose up -d postgres redis
```

If Redis port is already occupied, verify the existing Redis is the intended local service before continuing.

## 3. Baseline checks

```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
```

Do not implement if baseline is broken unless the failure is clearly caused by Phase 14J files.

## 4. Inspect current admin registrations

```bash
find apps -maxdepth 3 -type f | sort | grep '/admin.py$'
grep -R "admin.site.register\|@admin.register\|ModelAdmin" apps -n
```

## 5. Inspect candidate sensitive fields

```bash
grep -R "raw_text\|file\|token\|request_payload\|response_payload\|api_key\|secret" apps/*/admin.py apps -n 2>/dev/null || true
```

Review manually. Non-empty results are expected. They must be safe.
