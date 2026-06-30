# Production Deploy Policy

Never edit production Python code manually unless it is an emergency containment step. Normal changes go:

```text
dev branch -> review -> main -> pull on server -> migrate/collectstatic/restart -> smoke test
```

Production smoke must include:

```bash
python manage.py check --settings=config.settings.production
python manage.py migrate --check --settings=config.settings.production || true
curl -I https://tuniatlas.com/health/
```

Sensitive checks must not print secrets.
