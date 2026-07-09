# Phase 16G — Admin Monitoring and Alerts — acceptance.md

## General acceptance

```text
All tickets in tasks.md are complete or explicitly deferred with reason.
No next-phase work was implemented.
No stack changes.
Service-layer boundary preserved.
Tests pass or failures are documented and clearly unrelated.
No secrets, raw CV text, OAuth tokens, API keys, or private file paths are logged.
```

## Required checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Phase-specific acceptance

```text
Admin dashboards are staff/superuser protected.
Sensitive CV downloads require owner/superuser permission.
AdminFileAccessLog records sensitive file access.
Admin alerts use env-configured recipient, not hardcoded secrets.
No raw CV text in alert emails.
```
