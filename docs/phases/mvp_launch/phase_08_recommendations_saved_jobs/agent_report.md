# Phase 8 — Recommendations and Saved Jobs — Agent Report

## Summary

Phase 8 implemented deterministic recommendations and saved jobs.

No Phase 9 work was implemented.

## Implemented Scope

- Added `apps.recommendations`.
- Added `JobRecommendation`, `RecommendationRun`, and `SavedJob`.
- Added deterministic recommendation generation using Phase 7 `MatchScoringService`.
- Added saved/unsaved job service logic.
- Added dashboard recommendations page.
- Added dashboard saved jobs page.
- Added save/unsave job routes using UUID `public_id`.
- Added save button integration on job detail.
- Added recommendation staleness hooks after:
  - profile update
  - CV upload
  - CV deletion
  - CV parsing
- Added Celery tasks that call services only.
- Added admin registration.
- Added Phase 8 tests.

## Final Local Verification

Passed locally:

- `python manage.py check --settings=config.settings.local`: OK
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`: OK
- `python manage.py migrate --settings=config.settings.local`: OK
- `python manage.py seed_skills --settings=config.settings.local`: OK
- `python manage.py seed_job_sources --settings=config.settings.local`: OK
- `python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local`: OK
- `python manage.py test apps.recommendations --settings=config.settings.local`: OK, 59 tests
- `python manage.py test apps.cvs --settings=config.settings.local`: OK, 16 tests
- `python manage.py test apps.jobs --settings=config.settings.local`: OK, 48 tests
- `python manage.py test apps.matching --settings=config.settings.local`: OK, 17 tests
- `python manage.py test --settings=config.settings.local`: OK, 171 tests

## Route Verification

Resolved successfully:

- `dashboard:recommendations`
- `dashboard:saved_jobs`
- `jobs:save`
- `jobs:unsave`

## Error Handling Verification

- Invalid, inactive, expired, or non-public job save requests return controlled 404 behavior.
- Save route no longer converts `Http404` into `ValueError`.
- Save route no longer produces HTTP 500 for inactive/non-public jobs.

## Boundary Confirmation

Confirmed:

- No Phase 9 work.
- No OpenRouter import.
- No LLM calls.
- No email digest.
- No unsubscribe flow.
- No live France Travail API calls.
- No `CVUpload.all_objects` in runtime recommendation code.
- No `objects.create_user` in tests.
- User job search remains local PostgreSQL-backed.
- Public job/saved-job routes use UUID `public_id`, not internal integer IDs.
- Views remain thin and call services.
- Celery tasks call services only.

## Final Status

Phase 8 implementation is ready for senior review.
