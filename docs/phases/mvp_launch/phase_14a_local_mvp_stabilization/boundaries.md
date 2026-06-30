# Boundaries and Hard Rules

## Stack rules

Allowed:

- Django
- Django ORM
- PostgreSQL
- Redis
- Celery / Celery Beat
- django-allauth
- Django templates
- HTMX
- Tailwind CSS
- OpenRouter through controlled services only
- PyMuPDF/pdfplumber for PDF text extraction

Forbidden:

- React
- Next.js
- Angular
- FastAPI
- MongoDB
- SQLAlchemy
- SPA architecture
- Browser automation

## Architecture rules

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data; models do not call external APIs.
- No OpenRouter or LLM calls from Django views.
- No France Travail live API calls during normal public job search.
- Public job search reads local PostgreSQL only.
- Public routes use UUID `public_id`, never internal integer IDs.
- CV files are private and must not be publicly exposed.
- `CVUpload.objects` must exclude soft-deleted CVs.
- `CVUpload.all_objects` is for admin/privacy/deletion/internal tasks only.
- LLM can extract, explain, suggest; LLM cannot decide or change final fit score.
- User-confirmed/manual profile fields are stronger than parsed CV fields.

## Secrets rules

- Do not print real `.env` values.
- Do not print API keys, OAuth secrets, SMTP passwords, tokens, or user passwords.
- Do not commit `.env`.
- Do not write real secrets to `.env.example`, docs, tests, fixtures, logs, screenshots, or reports.
- Checking whether a variable exists is allowed: print `HAS_OPENROUTER_API_KEY=True`, never the key.

## Git rules

- Work on `dev`.
- Do not commit.
- Do not merge.
- Do not push.
- Final output is code changes + report only.

## External API rules

### OpenRouter

Allowed only from LLM service layer.

Real validation limit:

- Maximum 2 real OpenRouter calls in this phase.
- Use a tiny synthetic CV/match payload.
- Log usage without revealing prompt secrets or CV full raw text.

### France Travail

Allowed only from ingestion service/client/management command/task.

Forbidden:

- Calling France Travail from `/jobs/` search.
- Calling France Travail from templates.
- Calling France Travail from model methods.

Real validation limit:

- Maximum 1 small real ingestion run.
- Maximum 10 offers.
- Must persist raw records then normalize locally.
- Must not trigger infinite pagination.

## Browser rule

No browser testing. No Playwright. No Selenium. No manual browser steps.

Use:

- Django test client
- RequestFactory
- service tests
- task tests
- template rendering assertions
- management command tests
- shell smoke commands
