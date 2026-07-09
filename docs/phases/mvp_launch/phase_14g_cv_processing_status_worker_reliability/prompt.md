# Phase 14G Agent Prompt — CV Processing Status UX + Worker Reliability

You are implementing Phase 14G for TuniTech Abroad.

Work automatically through all tickets in this phase only.

Do not commit.
Do not deploy.
Do not start Phase 14H.
Do not refactor unrelated areas.

## Project context

TuniTech Abroad is a France-first job intelligence platform for Tunisian IT candidates.

Current stack:

- Django
- Django ORM
- PostgreSQL
- Redis
- Celery
- Celery Beat where needed later
- django-allauth
- Django templates
- HTMX
- Tailwind CSS
- Alpine.js only when necessary
- OpenRouter only in controlled service/task contexts
- PyMuPDF/pdfplumber for CV text extraction

Forbidden stack:

- React
- Next.js
- Angular
- Vue SPA
- FastAPI
- MongoDB
- SQLAlchemy
- public CV media URLs

## Phase objective

Make CV upload and parsing status understandable and reliable in local MVP usage.

A user must clearly see:

- Upload complete
- Queued for analysis
- Analyzing CV
- Completed
- Failed safely
- Local worker guidance when stuck in development

## Current known issue

In local testing, a CV appeared stuck forever in pending because Celery worker was not running. After starting Celery, the parse task succeeded. The product still needs better status UX and worker reliability guidance.

## Required work

Implement tasks in:

- `docs/phases/phase_14g_cv_processing_status_worker_reliability/tasks.md`
- `docs/phases/phase_14g_cv_processing_status_worker_reliability/acceptance.md`
- `docs/phases/phase_14g_cv_processing_status_worker_reliability/boundaries.md`

## Hard rules

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- No OpenRouter/LLM calls from Django views.
- No France Travail live API calls in normal user search.
- CV files are private and must not be publicly exposed.
- Public/user-facing routes must use UUID `public_id`, never internal integer IDs.
- `CVUpload.objects` must exclude soft-deleted CVs.
- `CVUpload.all_objects` is only for admin/privacy/deletion/internal tasks.
- Do not change matching score logic.
- Do not change Phase 14F ingestion/enrichment behavior except if a test import needs harmless adjustment.

## Expected output

When finished, create/update:

- implementation code
- tests
- docs if needed
- `docs/phases/phase_14g_cv_processing_status_worker_reliability/agent_report.md`

## Required commands

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.cvs apps.profiles apps.matching apps.recommendations --settings=config.settings.local
python manage.py test --settings=config.settings.local
git diff --check
```

Also run security greps from `regression_security_checks.md`.

## Final verdict

Return only one of:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Use `BLOCKED_HUMAN_VISUAL_SIGNOFF` only when all automated checks pass but Baha still needs browser/manual signoff.
