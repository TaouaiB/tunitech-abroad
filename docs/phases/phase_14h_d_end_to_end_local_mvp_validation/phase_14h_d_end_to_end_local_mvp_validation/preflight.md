# Preflight

Run from Fedora/Linux terminal:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short
python --version
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
```

## PostgreSQL / Redis

Check services:

```bash
docker compose ps || true
python manage.py health_check --settings=config.settings.local || true
python manage.py cv_worker_check --settings=config.settings.local || true
```

If Redis is already reachable on `localhost:6380`, do not fight Docker/Podman port conflicts. Record the state in the report.

## Static CSS

```bash
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
```

## Worker startup commands

Terminal 1:

```bash
celery -A config worker --loglevel=info --concurrency=2
```

Terminal 2, optional beat smoke:

```bash
timeout 20s celery -A config beat --loglevel=info --pidfile= --schedule=/tmp/tunitech_phase14hd_celerybeat_schedule
rm -f /tmp/tunitech_phase14hd_celerybeat_schedule*
```

Terminal 3:

```bash
python manage.py runserver --settings=config.settings.local
```
