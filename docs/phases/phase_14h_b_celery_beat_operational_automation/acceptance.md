# Acceptance Criteria

Phase 14H-B is accepted only if all criteria pass.

## Functional acceptance

- `CELERY_BEAT_SCHEDULE` is populated with operational maintenance tasks.
- Running Django without Celery Beat still works.
- Running Celery worker still works.
- Running Celery Beat starts without import errors.
- Scheduled job ingestion uses the existing task/service/config flow.
- Scheduled recommendation refresh uses local PostgreSQL data only.
- Scheduled cleanup tasks do not expose or delete active CV files incorrectly.

## Architecture acceptance

- Celery tasks remain thin and call services.
- No Django view calls Celery Beat/France Travail/OpenRouter directly.
- No public job search endpoint calls France Travail.
- No LLM final scoring is introduced.
- No forbidden stack is added.

## Security/privacy acceptance

- No CV file URLs are exposed.
- No raw CV text is exposed in templates/logs.
- No real secrets are added to `.env.example`, docs, tests, or settings.
- No internal integer ID public route is added.

## Test acceptance

Required commands must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.core apps.jobs apps.recommendations apps.privacy --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

Also run the security greps in `regression_security_checks.md`.

## Final verdict

Agent final verdict must be exactly one of:

- `FINAL_VERDICT: FAIL`
- `FINAL_VERDICT: BLOCKED_HUMAN_VISUAL_SIGNOFF`
