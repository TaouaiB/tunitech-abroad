# Phase 16C — CV Parser Quality Framework — acceptance.md

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
CV name extractor rejects 'je me suis'.
Low-confidence name returns None with warning.
Parser emits confidence/warnings.
private_test_corpus is gitignored.
audit_cv_parser command exists or is documented if deferred.
No real CVs committed.
```
