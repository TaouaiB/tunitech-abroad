# Phase 16I — Email Professionalization — acceptance.md

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
Email templates have HTML and plain-text fallback.
Verification/password reset remain functional.
Admin alert email templates avoid secrets/raw CV text.
Digest is not enabled unless recommendation quality is accepted.
Unsubscribe/preferences footer exists where required.
```
