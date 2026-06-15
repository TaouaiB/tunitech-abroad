# Phase 13 Preflight — Required Before Agent Work

Run from normal Warp terminal before Gemini/Antigravity and before Codex verification.

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git branch --show-current
git status --short

echo "DOCKER_HOST=${DOCKER_HOST:-}"
docker ps
docker compose ps || true

python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.db import connection; connection.ensure_connection(); print('DB_VENDOR=', connection.vendor)"
python manage.py shell --settings=config.settings.local -c "from django.core.cache import cache; cache.set('phase13_preflight','ok',10); print('CACHE_VALUE=', cache.get('phase13_preflight'))"
```

Expected:

```text
DB_VENDOR= postgresql
CACHE_VALUE= ok
```

If Docker/Podman is needed through Codex, start Codex only with:

```bash
codex-tunitech
```

Do not use plain `codex` for verification unless `DOCKER_HOST` is already set to the rootless Podman socket and the preflight passes.

## Go / No-Go

Go only if:

- branch is `dev`
- Phase 12 is committed
- `.env` is ignored
- PostgreSQL-backed `migrate` works
- cache check works

No-Go if:

- working tree contains uncommitted Phase 12 work
- PostgreSQL is unreachable
- cache is broken
- `.env` appears in `git status`
