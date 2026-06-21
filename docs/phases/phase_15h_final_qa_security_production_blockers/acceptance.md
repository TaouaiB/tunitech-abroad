# Phase 15H Acceptance Criteria

## Product acceptance

- Saved jobs page never exposes internal classification/debug text.
- Saved jobs handles removed/expired/excluded/non-public jobs with safe French labels or hides them safely.
- Active saved jobs still display normally.
- `Plus pertinentes` sort works for keyword searches.
- Relevance sort without keyword falls back safely.
- Operations dashboard metrics have clear labels and consistent sources.
- No public page displays internal statuses such as `excluded_non_it`, `provider_blocked`, `validation_error`, `reserved`, or `unclassified`.

## Security acceptance

- `pip-audit` reports no known vulnerabilities.
- `python-dotenv==1.2.2` remains in `requirements/base.txt`.
- Production `collectstatic` passes.
- Bandit has no unresolved high/medium production-code findings.
- Silent `except: pass` in production services/tasks is replaced with safe logging.
- MD5 in production LLM services is replaced with SHA-256.
- OpenRouter client no longer uses unsafe arbitrary URL handling.
- No real secrets in repo, diff, reports, logs, or prompts.

## Architecture acceptance

- Views stay thin.
- Job search logic stays in services.
- Saved job display logic uses services/presentation helpers, not raw template condition soup.
- Admin metrics logic stays in analytics/admin service layer.
- Celery tasks call services only.
- No OpenRouter call from views/templates/models/admin display.
- No France Travail live API call from public search.
- No forbidden stack introduced.

## Required test coverage

- Saved job internal text suppression.
- Saved unavailable/excluded job safe display or hide behavior.
- Saved job ownership isolation.
- Relevance sort with query.
- Relevance sort without query fallback.
- No France Travail client call from public search.
- Operations dashboard staff-only access.
- Operations dashboard metric source consistency.
- LLM SHA-256 hash behavior.
- OpenRouter client success/error behavior after requests refactor.
- CV/privacy/saved-job non-critical side effects log but do not crash.

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

Secret diff grep must report no obvious secrets.

## Commit acceptance

Commit only in-scope source/test/config/doc files.

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
