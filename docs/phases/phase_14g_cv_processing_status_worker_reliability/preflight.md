# Preflight — Phase 14G

Before coding, run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
```

Confirm Redis is available for local manual proof:

```bash
redis-cli -p 6380 ping || true
```

If Redis is managed by Compose:

```bash
podman compose up -d redis
# or docker compose up -d redis
```

For Codex verification, start from Warp with:

```bash
codex-tunitech
```

Do not use plain `codex` because it may miss the rootless Podman socket configuration.
