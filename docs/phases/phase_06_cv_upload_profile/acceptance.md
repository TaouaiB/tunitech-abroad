# Phase 6 — CV Upload, Parsing, and Profile Completion — Acceptance Criteria

Phase 6 is accepted only when all items below are true.

## Scope acceptance

- `apps/cvs` exists and is registered.
- CV models, services, forms, tasks, admin, tests, and templates are implemented.
- Dashboard profile and CV management pages exist.
- No Phase 7+ matching/recommendations/saved jobs/LLM/email features are implemented.
- No public CV download/serving route exists.

## Model acceptance

- `CVUpload` has `public_id` UUID.
- `CVUpload.objects` excludes rows where `deleted_at` is not null.
- `CVUpload.all_objects` includes soft-deleted rows.
- one active non-deleted CV per user is enforced at DB level.
- `CVUpload.soft_delete()` sets:
  - `is_active=False`
  - `deleted_at` timestamp
  - `parse_status=deleted`
- `CVParsedData` is one-to-one with `CVUpload`.
- migrations are clean and deterministic.

## Private file acceptance

- CV upload path stores files under private media.
- No template exposes `cv.file.url`.
- No public URL serves CV files.
- `.gitignore` or existing ignore rules exclude private media files.
- Full raw CV text is not logged.

## Upload acceptance

- authenticated user can upload a PDF CV.
- unauthenticated user is redirected to login.
- non-PDF is rejected.
- oversized file is rejected.
- missing consent is rejected.
- previous active CV is deactivated when a new CV is uploaded.
- `parse_cv` is enqueued after upload.
- user event is recorded if analytics service is available.

## Parsing acceptance

- `parse_cv` task calls `CVParsingService.parse_by_id()` only.
- parser uses `CVUpload.all_objects` internally and aborts if the CV is deleted.
- parse status transitions pending -> processing -> parsed/parsed_with_warnings/failed.
- PDF text extraction works on a synthetic sample PDF.
- too-little-text PDFs are handled safely and marked failed/too_little_text.
- deterministic extractor finds email, phone, LinkedIn, GitHub, portfolio/website where present.
- no OCR is attempted.
- no OpenRouter/LLM network call is made.
- disabled LLM shell returns safe no-op metadata.

## Profile acceptance

- parsing creates/updates `CVParsedData`.
- extracted skills are normalized through `SkillNormalizerService`.
- `ProfileSkill` rows are created/updated without duplicates.
- `CandidateProfile` empty fields are prefilled from parsed CV data.
- non-empty user-entered profile fields are not overwritten by CV parsing.
- user can manually edit profile.
- profile completeness score updates.

## CV deletion acceptance

- user can delete own CV.
- user cannot delete another user's CV.
- deletion soft-deletes the CV.
- deletion removes the physical private file where possible.
- deletion deletes/clears parsed data.
- deleted CVs do not appear through `CVUpload.objects`.

## View acceptance

- `/dashboard/profile/` requires authentication.
- `/dashboard/cv/` requires authentication.
- `/dashboard/cv/status/<uuid:public_id>/` requires authenticated owner.
- CV status partial returns partial HTML.
- parsed summary displays safe extracted fields only.
- no file path or public CV URL is rendered.

## Test acceptance

The following must pass:

```bash
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

Junk/scope checks must show no unwanted files:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

## Rejection conditions

Reject Phase 6 if any of these are true:

- CV files are publicly accessible.
- `CVUpload.objects` returns soft-deleted CVs.
- `CVUpload.all_objects` is used in normal user views.
- view contains parsing/business logic instead of calling services.
- Celery task contains parsing logic instead of calling service.
- OpenRouter or any LLM API is called.
- matching/recommendations/saved jobs are implemented.
- user can access another user's CV status or delete another user's CV.
- tests call live external APIs.
- red diagnostics remain in changed Python files.
- `task.md`, pyc, cache, sqlite, celerybeat, review zip files are present.
