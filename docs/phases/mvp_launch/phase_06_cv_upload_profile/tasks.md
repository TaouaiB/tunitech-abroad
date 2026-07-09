# Phase 6 — CV Upload, Parsing, and Profile Completion — Tasks

## Phase goal

Allow authenticated users to upload a private PDF CV, parse it deterministically, create/update profile skill data, show parse status, and manually complete their profile.

This phase connects the existing profile foundation, skill taxonomy, and public job system to the candidate CV/profile workflow. It does **not** implement matching, recommendations, saved jobs, email, or LLM extraction.

## Hard phase boundary

Phase 6 may implement:

- `apps/cvs`
- `CVUpload`
- `CVParsedData`
- private CV file storage
- PDF upload validation
- CV processing consent enforcement
- deterministic PDF text extraction
- deterministic contact/link/skill extraction
- `parse_cv` Celery task that calls services only
- profile edit page
- CV management page
- CV parse status partial
- profile completeness calculation/update
- basic `ProfileSkill` rows sourced from CV/manual input

Phase 6 must **not** implement:

- Phase 7 matching or quick match
- fit score calculation
- recommendations
- saved jobs
- OpenRouter/LLM extraction calls
- email digest
- unsubscribe flows
- privacy deletion/account deletion hardening beyond safe CV deletion
- OCR for scanned CVs
- live France Travail calls
- public exposure of CV files
- React/Next/Angular/FastAPI/SQLAlchemy/MongoDB/SPA architecture

## Required tickets

### TTA-0601 — Create `apps/cvs` application

Create a new Django app:

```text
apps/cvs/
```

Required structure:

```text
apps/cvs/
  __init__.py
  admin.py
  apps.py
  forms.py
  models.py
  tasks.py
  services/
    __init__.py
    upload.py
    text_extraction.py
    deterministic_extractor.py
    llm_extraction.py
    parsing.py
    deletion.py
    query.py
  management/
    __init__.py
    commands/
      __init__.py
  tests/
    __init__.py
    test_models.py
    test_services.py
    test_views.py
    test_tasks.py
```

Register `apps.cvs.apps.CVsConfig` in `INSTALLED_APPS`.

Do not leave placeholder `apps/cvs/tests.py` or `apps/cvs/views.py` if `startapp` creates them and they are unused.

### TTA-0602 — Add CV models and safe soft-delete manager

Create `CVUpload` with a safe default manager:

- `objects = ActiveCVManager()` returns only rows with `deleted_at IS NULL`
- `all_objects = models.Manager()` for admin/privacy/internal/deletion/Celery only

Required fields:

- `id` BigAutoField
- `public_id` UUIDField unique indexed, non-editable
- `user` ForeignKey to `settings.AUTH_USER_MODEL`
- `file` FileField with private upload path
- `original_filename` CharField
- `file_hash` CharField, SHA256
- `file_size` PositiveIntegerField
- `mime_type` CharField default/expected `application/pdf`
- `is_active` BooleanField
- `parse_status` CharField choices: pending, processing, parsed, parsed_with_warnings, failed, deleted
- `parse_error` TextField blank
- `text_extraction_status` CharField blank choices: pending, success, failed, too_little_text
- `extracted_text_length` PositiveIntegerField null/blank
- `uploaded_at` DateTimeField auto
- `parsed_at` DateTimeField null/blank
- `deleted_at` DateTimeField null/blank

Required constraints/indexes:

- unique `public_id`
- partial unique constraint for one active non-deleted CV per user:
  - `user`, condition `is_active=True AND deleted_at IS NULL`
- indexes for `user`, `public_id`, `file_hash`, `parse_status`, `is_active`, `uploaded_at`, `deleted_at`

Create `soft_delete()` method:

- set `is_active=False`
- set `deleted_at=timezone.now()`
- set `parse_status=deleted`
- save only changed fields

Create `CVParsedData`:

- `cv_upload` OneToOneField to `CVUpload`
- `raw_text` TextField blank
- `deterministic_json` JSONField default dict
- `llm_json` JSONField default dict
- `merged_json` JSONField default dict
- `extraction_method` choices: regex_only, regex_llm, manual, failed
- `llm_schema_version` CharField blank
- `extracted_name` CharField blank
- `extracted_email` EmailField blank
- `extracted_phone` CharField blank
- `extracted_location` CharField blank
- `extracted_linkedin_url` URLField blank
- `extracted_github_url` URLField blank
- `extracted_portfolio_url` URLField blank
- `estimated_years_experience` DecimalField null/blank
- `confidence_json` JSONField default dict
- `warnings_json` JSONField default list
- timestamps

### TTA-0603 — Private CV file handling and settings

CV files are private. They must not be linked from templates as public media URLs.

Add settings only if missing:

```python
PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"
MAX_CV_UPLOAD_SIZE_MB = 5
CV_LLM_EXTRACTION_ENABLED = False
```

Rules:

- `.env.example` may document `MAX_CV_UPLOAD_SIZE_MB`, but do not add secrets.
- Do not create public URL patterns that serve CV files.
- Do not print/log full CV text.
- Do not expose file paths in templates.

### TTA-0604 — Implement CV upload form and service

Create `CVUploadForm` with:

- PDF file field
- required consent checkbox for CV processing

Implement `apps/cvs/services/upload.py`:

```python
CVUploadService.upload_cv(user: User, uploaded_file, *, consent_accepted: bool) -> CVUpload
```

Rules:

1. Validate authenticated user is provided.
2. Validate consent is accepted.
3. Validate file extension and MIME type as PDF.
4. Validate file size <= `MAX_CV_UPLOAD_SIZE_MB`.
5. Compute SHA256 file hash without exhausting the uploaded file stream.
6. Deactivate previous active CVs for the user.
7. Save the file under private media.
8. Create `CVUpload(parse_status=pending, is_active=True)`.
9. Record consent through existing `ConsentService` if available.
10. Record `UserEvent(cv_uploaded)` through existing analytics service if available.
11. Enqueue `parse_cv` task after transaction commit.

Do not call parsing directly from the view.

### TTA-0605 — Implement PDF text extraction service

Implement `apps/cvs/services/text_extraction.py`:

```python
CVTextExtractionService.extract_text(cv_upload: CVUpload) -> dict
```

Allowed libraries:

- PyMuPDF (`pymupdf` / `fitz`)
- pdfplumber as fallback

Rules:

- No OCR in MVP.
- Return structured dict, not raw exceptions.
- If extracted text is too short, return status `too_little_text` and success false.
- Update only via parsing service, not directly from views.
- Do not log full raw text.

### TTA-0606 — Implement deterministic CV extraction service

Implement `apps/cvs/services/deterministic_extractor.py`:

```python
CVDeterministicExtractorService.extract(raw_text: str) -> dict
```

Extract deterministically:

- email
- phone
- LinkedIn URL
- GitHub URL
- portfolio URL
- website URL
- simple candidate name guess if safe
- raw skills candidates using keyword/line heuristics

Rules:

- No LLM.
- Do not invent experience years, education hierarchy, project structure, or full work history.
- Return warnings when extraction is weak.
- Normalize extracted skill strings through Phase 3 `SkillNormalizerService` in the parsing service, not by ad hoc canonical creation.

### TTA-0607 — Add disabled LLM extraction shell

Implement `apps/cvs/services/llm_extraction.py` with a safe shell:

```python
CVLLMExtractionService.extract_structured(cv_upload: CVUpload, raw_text: str) -> dict
```

Rules:

- In Phase 6, `CV_LLM_EXTRACTION_ENABLED` defaults to `False`.
- The service must return disabled/no-op metadata when disabled.
- It must not import or call OpenRouter.
- It must not make network requests.
- It must not fail parsing when disabled.

Actual OpenRouter extraction belongs to Phase 9.

### TTA-0608 — Implement CV parsing orchestration and Celery task

Implement `apps/cvs/services/parsing.py`:

```python
CVParsingService.parse(cv_upload: CVUpload) -> CVParsedData
CVParsingService.parse_by_id(cv_upload_id: int) -> CVParsedData | None
```

Flow:

1. Use `CVUpload.all_objects` internally when parsing by id.
2. Abort safely if CV is deleted.
3. Set `parse_status=processing`.
4. Extract raw text.
5. If unreadable/too short, mark failed/too_little_text and store warning.
6. Run deterministic extraction.
7. Run disabled LLM shell only if configured; no network call.
8. Merge deterministic output and disabled LLM metadata.
9. Create/update `CVParsedData`.
10. Normalize extracted skills using `SkillNormalizerService`.
11. Create/update `ProfileSkill` rows from canonical skills without duplicating existing rows.
12. Prefill CandidateProfile fields where empty only.
13. Recalculate profile completeness.
14. Set `parse_status=parsed` or `parsed_with_warnings`.
15. Set `parsed_at`.

Create `apps/cvs/tasks.py`:

```python
@shared_task
def parse_cv(cv_upload_id: int) -> None:
    CVParsingService.parse_by_id(cv_upload_id)
```

Celery task must call service only. No parsing logic in the task.

### TTA-0609 — Implement CV deletion service

Implement `apps/cvs/services/deletion.py`:

```python
CVDeletionService.delete_cv(user: User, cv_public_id: UUID) -> ServiceResult
```

Rules:

- Verify ownership.
- Use `CVUpload.objects` for normal user flows.
- Remove physical file if it exists.
- Soft-delete `CVUpload`.
- Delete or clear `CVParsedData`.
- Remove unconfirmed `ProfileSkill` rows sourced from that CV if the current `ProfileSkill` model supports enough source fields.
- Record `UserEvent(cv_deleted)` if available.
- Do not hard-delete CVUpload in normal flow.

### TTA-0610 — Implement profile update/completeness services

Create/update profile services:

```text
apps/profiles/services/profile_update.py
apps/profiles/services/completeness.py
```

Implement:

```python
ProfileUpdateService.update_profile(user, cleaned_data) -> CandidateProfile
ProfileCompletenessService.calculate(profile: CandidateProfile) -> int
```

Rules:

- Views must call services.
- Profile completeness should be deterministic and simple.
- Update `CandidateProfile.profile_completion_score`.
- Do not implement recommendations stale flags yet.
- Do not implement matching.

### TTA-0611 — Implement authenticated dashboard CV/profile pages

Implement URLs/pages matching the page map:

- `/dashboard/profile/`
  - view name: `dashboard:profile`
  - template: `templates/dashboard/profile.html`
- `/dashboard/cv/`
  - view name: `dashboard:cv`
  - template: `templates/dashboard/cv_manage.html`
- `/dashboard/cv/status/<uuid:public_id>/`
  - view name: `dashboard:cv_status`
  - partial: `templates/cvs/partials/cv_status.html`

The project may already have dashboard URLs/views. Extend existing dashboard routes if appropriate.

Rules:

- Authenticated only.
- Only owner can view CV status/delete CV.
- Views stay thin.
- Upload view calls `CVUploadService` only.
- Delete view calls `CVDeletionService` only.
- Status partial never exposes file path or CV download URL.
- Profile page calls profile services.
- Basic HTMX status partial is allowed.

### TTA-0612 — Add admin registrations

Register:

- `CVUpload`
- `CVParsedData`

Admin rules:

- Use `CVUpload.all_objects` in admin if needed to see deleted rows.
- Do not expose file download links unless they are staff-only and safe.
- Do not print raw full text in list display.
- Include parse status, user, active/deleted flags, parsed timestamp.

### TTA-0613 — Add tests

Required tests:

Models:

- `CVUpload.objects` excludes deleted CVs.
- `CVUpload.all_objects` includes deleted CVs.
- one active CV per user enforced.
- `soft_delete()` sets `deleted_at`, `is_active=False`, `parse_status=deleted`.
- `CVParsedData` one-to-one works.

Services:

- PDF upload accepted.
- non-PDF rejected.
- file size limit enforced.
- consent required.
- upload deactivates previous active CV.
- parse task is enqueued after upload.
- text extraction works on a sample PDF.
- too-little-text failure path works.
- deterministic extractor extracts email/phone/links.
- parsing creates/updates `CVParsedData`.
- parsing creates ProfileSkill rows from canonical skills.
- parsing pre-fills empty CandidateProfile fields only.
- deletion soft-deletes CV and removes/clears parsed data.

Views:

- unauthenticated users redirected to login.
- authenticated users can access profile and CV pages.
- PDF upload works through page.
- non-PDF upload rejected.
- consent missing rejected.
- user cannot view/delete another user's CV status.
- status partial returns partial HTML.

Tasks:

- `parse_cv` task calls `CVParsingService.parse_by_id`.
- task aborts safely for deleted CV.

Boundary tests:

- no matching imports/features.
- no recommendations app work.
- no OpenRouter/API calls.
- no public CV file URL.

## Required final checks

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

Run junk/scope checks:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

Final report must be written to:

```text
docs/phases/phase_06_cv_upload_profile/agent_report.md
```
