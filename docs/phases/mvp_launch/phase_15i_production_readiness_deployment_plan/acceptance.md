# Phase 15I Acceptance Criteria

## Product/deployment readiness acceptance

- Production `.env.example` uses placeholders only.
- Automatic LLM token spending is disabled by default for production.
- Whitenoise/static/private media responsibilities are clear.
- Private CV/media files are not served publicly.
- Rate limiting / abuse controls are documented with clear MVP decisions.
- Monitoring/health checks are documented.
- Backup and restore policy exists and requires restore testing.
- Privacy final review checklist exists.
- Legal wording final pass exists.
- Email/OAuth/domain checklist exists.
- Phase 15J deployment runbook outline exists.
- Production smoke checklist exists.

## Security/privacy acceptance

- No real secrets in docs, reports, `.env.example`, git diff, logs, or prompts.
- `.env` is not read, printed, changed, or committed.
- No code/docs suggest serving `private_media` through Caddy/Nginx/static URLs.
- No OpenRouter calls from views/templates/models/admin display.
- No France Travail live calls from public job search.
- No public integer ID regression.
- CV privacy rules preserved.

## Architecture acceptance

- No forbidden stack introduced.
- No React/Next/Angular/FastAPI/MongoDB/SQLAlchemy/SPA.
- Views remain thin.
- Services own business logic.
- Celery tasks call services only.
- Production plan uses Django + HTMX + Tailwind + PostgreSQL + Redis + Celery.

## Required commands

Must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
python manage.py check --deploy --settings=config.settings.production
python manage.py makemigrations --check --dry-run --settings=config.settings.production
python manage.py collectstatic --dry-run --noinput --settings=config.settings.production
pip-audit
bandit -r apps config -x "*/tests.py,*/tests/*,*/test_*.py,*/migrations/*,*/fixtures/*"
npm audit --omit=dev
git diff --check
```

Secret diff grep must show no obvious real secrets.

## Commit acceptance

Commit only in-scope files.

Do not commit:

```text
.env
agent_report.md at project root
docs/reports/
var/
staticfiles/
__pycache__/
.pytest_cache/
```
