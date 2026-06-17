# Preflight

Before coding, run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
```

Confirm Redis can run locally when needed:

```bash
python manage.py shell --settings=config.settings.local -c "from django.conf import settings; print(settings.CELERY_BROKER_URL)"
```

Do not start Celery Beat as a daemon. If testing Beat startup, run it in the foreground and stop it manually.
