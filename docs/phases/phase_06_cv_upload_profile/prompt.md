# Phase 6 — CV Upload, Parsing, and Profile Completion — Agent Prompt

You are implementing Phase 6 of TuniTech Abroad.

Read first:

- `AGENTS.md`
- `docs/phases/phase_06_cv_upload_profile/tasks.md`
- `docs/phases/phase_06_cv_upload_profile/acceptance.md`
- `docs/phases/phase_06_cv_upload_profile/agent_report_template.md`
- `docs/phases/phase_05_public_jobs_search/agent_report.md`

## Mission

Implement authenticated CV upload/parsing/profile completion for Tunisian IT candidates.

This phase must create a safe private CV workflow:

1. user uploads PDF CV from dashboard
2. consent is required
3. only one active CV is maintained
4. CV file is private
5. Celery task parses the CV through services
6. deterministic extraction gets text/contact/link/skills
7. profile and ProfileSkill rows are prefilled carefully
8. user can edit/confirm profile manually
9. user can delete CV safely

## Hard boundaries

Do not start Phase 7 or later.

Do not implement:

- matching
- quick match
- fit score
- recommendations
- saved jobs
- OpenRouter/LLM calls
- email digest
- unsubscribe
- account privacy deletion
- OCR
- public CV file serving
- France Travail live calls
- React, Next.js, Angular, FastAPI, SQLAlchemy, MongoDB, SPA architecture

## Architecture rules

- Django views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models do not call external APIs.
- CV files are private and must not be publicly exposed.
- `CVUpload.objects` must exclude soft-deleted CVs.
- `CVUpload.all_objects` is only for admin/privacy/deletion/internal/Celery tasks.
- No OpenRouter/LLM calls from Django views.
- LLM extraction service is a disabled shell only in Phase 6.
- Use Django ORM only.
- Use Django templates only.
- HTMX is allowed only for the CV parse status partial.

## Implementation requirements

Follow `tasks.md` ticket by ticket.

Important expected paths:

```text
apps/cvs/
apps/cvs/services/upload.py
apps/cvs/services/text_extraction.py
apps/cvs/services/deterministic_extractor.py
apps/cvs/services/llm_extraction.py
apps/cvs/services/parsing.py
apps/cvs/services/deletion.py
apps/cvs/tasks.py
apps/profiles/services/profile_update.py
apps/profiles/services/completeness.py
templates/dashboard/profile.html
templates/dashboard/cv_manage.html
templates/cvs/partials/cv_status.html
templates/cvs/partials/cv_parsed_summary.html
```

Use existing apps and URLs where appropriate. Do not create duplicate dashboard structure if it already exists.

## CV privacy requirements

- Do not expose `cv_upload.file.url` in any template.
- Do not create public download routes.
- Do not serve private media through public URLs.
- Do not log raw CV text.
- Do not commit sample real CVs or personal data.
- Tests may create synthetic PDF files only.

## Celery requirements

`parse_cv` task must look like a thin wrapper:

```python
@shared_task
def parse_cv(cv_upload_id: int) -> None:
    CVParsingService.parse_by_id(cv_upload_id)
```

No extraction logic in task body.

## LLM requirements

Create the shell service because the contract lists it, but keep it disabled:

- default `CV_LLM_EXTRACTION_ENABLED=False`
- no OpenRouter import
- no HTTP call
- return no-op metadata

Actual LLM extraction is Phase 9.

## Required checks before final report

Run:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.profiles --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Then run:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

Open changed Python files in the editor and confirm no red diagnostics remain.

Fill:

```text
docs/phases/phase_06_cv_upload_profile/agent_report.md
```

Do not commit. Do not merge. Do not push.
