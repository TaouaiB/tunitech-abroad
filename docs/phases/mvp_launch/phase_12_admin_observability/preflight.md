# Phase 12 Preflight — Docker/Podman, PostgreSQL, Redis, Tests

Run this before giving the phase to Gemini or Codex.

## 1. Confirm clean phase boundary

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git branch --show-current
git status --short
```

Expected:

```text
dev
```

Phase 11 should already be committed. Do not start Phase 12 with uncommitted Phase 11 implementation files unless Baha explicitly chooses to continue in the same commit.

## 2. Check Compose visibility

```bash
docker ps
docker compose ps
```

If `docker compose ps` shows empty but Django can migrate, the database may already be running outside Compose. That is acceptable for test execution, but report it honestly.

If Docker/Podman socket is denied, try:

```bash
systemctl --user enable --now podman.socket
```

Then open a new terminal or rerun:

```bash
docker ps
docker compose ps
```

## 3. Start infra when possible

```bash
docker compose up -d postgres redis || docker compose up -d
```

If Redis port `6380` is busy:

```bash
ss -ltnp | grep ':6380' || true
```

Do not kill random processes without Baha approval.

## 4. Prove PostgreSQL works

```bash
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print(connection.vendor)"
```

Expected final output includes:

```text
postgresql
```

## 5. Prove Redis/cache path works

```bash
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase12_preflight','ok',10); print(cache.get('phase12_preflight'))"
```

Expected:

```text
ok
```

If Redis/cache fails but PostgreSQL works, continue only if the phase explicitly mocks Redis health in tests and report the local Redis blocker. Health endpoint implementation still must handle Redis failure correctly.

## 6. Acceptance rule

The agent must run PostgreSQL-backed tests using:

```bash
python manage.py test ... --settings=config.settings.local
```

Do not accept:

```bash
DATABASE_URL=sqlite:///...
```

as final acceptance.
