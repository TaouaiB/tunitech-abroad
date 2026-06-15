# Phase 6 — CV Upload, Parsing, and Profile Completion — Agent Report

## Summary

Phase 6 implemented authenticated private CV upload, deterministic PDF parsing, profile prefill, profile completion updates, CV management pages, safe CV deletion, and a disabled LLM extraction shell.

No Phase 7 work was implemented.

## Final Fixes Applied

- Moved `PyMuPDF` to `requirements/base.txt` as a runtime CV parsing dependency.
- Restored `requirements/local.txt` to local/dev dependencies only.
- Added `PRIVATE_MEDIA_ROOT` and `MAX_CV_UPLOAD_SIZE_MB`.
- Added `private_media/` to `.gitignore`.
- Added `CVUpload.objects` manager that excludes soft-deleted CVs.
- Kept `CVUpload.all_objects` only for admin/internal/parser use.
- Added `PrivateMediaStorage.url()` that raises `ValueError`, so CV files do not expose public URLs.
- Updated `CVUploadAdmin` to exclude the `file` field.
- Updated dashboard CV page to show only the active CV.
- Added private URL safety test.
- Fixed Phase 6 test typing by removing dynamic `create_user()` manager calls.
- Confirmed no OpenRouter/LLM network call is made.
- Confirmed no matching, recommendations, saved jobs, or Phase 7 features were added.

## Final Local Verification

Passed locally:

- `python manage.py check --settings=config.settings.local`: OK
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`: OK
- `python manage.py migrate --settings=config.settings.local`: OK
- `python manage.py seed_skills --settings=config.settings.local`: OK
- `python manage.py seed_job_sources --settings=config.settings.local`: OK
- `python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local`: OK
- `python manage.py test apps.cvs --settings=config.settings.local`: OK, 15 tests
- `python manage.py test apps.profiles --settings=config.settings.local`: OK, 3 tests
- `python manage.py test --settings=config.settings.local`: OK, 94 tests

## Phase Boundary

Confirmed:

- No matching.
- No quick match.
- No fit scoring.
- No recommendations.
- No saved jobs.
- No OpenRouter/LLM calls.
- No email digest.
- No public CV file serving.
- No deployment work.
- No Phase 7 work.

## Git Scope

Expected Phase 6 changes:

- `.env.example`
- `.gitignore`
- `apps/cvs/`
- `apps/dashboard/urls.py`
- `apps/dashboard/views.py`
- `apps/profiles/forms.py`
- `apps/profiles/services/`
- `config/settings/base.py`
- `requirements/base.txt`
- `requirements/local.txt`
- `templates/cvs/`
- `templates/dashboard/cv_manage.html`
- `templates/dashboard/profile.html`
- `docs/phases/phase_06_cv_upload_profile/`
