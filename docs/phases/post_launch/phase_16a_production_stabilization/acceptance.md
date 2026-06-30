# Phase 16A — Production Stabilization — acceptance.md

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
OAuth URLs use HTTPS behind Caddy.
Google verified-email linking works safely.
robots.txt and sitemap.xml return 200.
External job descriptions render safely.
Fake PDF is rejected by magic-byte validation.
Match formula uses 45/20/15/10/10 weights.
LLM disabled state is not fake success.
Homepage jobs are real or honest empty state.
```
