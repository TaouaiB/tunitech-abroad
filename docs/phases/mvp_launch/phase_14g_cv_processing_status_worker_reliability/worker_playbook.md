# Local Worker Playbook — Phase 14G

## Normal local development

Use three terminals.

### Terminal 1 — Web

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
python manage.py runserver --settings=config.settings.local
```

### Terminal 2 — Worker

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
celery -A config worker --loglevel=info --concurrency=2
```

### Terminal 3 — Redis check

```bash
redis-cli -p 6380 ping
```

If Redis is not running:

```bash
podman compose up -d redis
# or docker compose up -d redis
```

## Symptoms

### CV remains queued/pending

Likely causes:

- Celery worker not running.
- Redis not running.
- Task failed; inspect worker logs.

### CV failed

Likely causes:

- Invalid PDF.
- Extraction failure.
- Service exception.

User-facing UI must show safe failure text only. Admin/logs may show detailed failure reason.

## Do not do

- Do not expose CV file URL.
- Do not expose raw extracted text.
- Do not parse synchronously inside the upload view just to hide worker issues.
