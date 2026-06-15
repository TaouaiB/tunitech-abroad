# Phase 8 — Recommendations and Saved Jobs — Agent Report

## 1. Summary

Briefly summarize what was implemented.

## 2. Tickets Completed

- [ ] TTA-0801 — Create `apps/recommendations` and register it
- [ ] TTA-0802 — Create recommendation and saved-job models
- [ ] TTA-0803 — Implement recommendation result dataclasses
- [ ] TTA-0804 — Implement `RecommendationService.refresh_for_user()`
- [ ] TTA-0805 — Implement `RecommendationQueryService`
- [ ] TTA-0806 — Implement `SavedJobService`
- [ ] TTA-0807 — Implement `ActiveUserRecommendationService`
- [ ] TTA-0808 — Implement recommendation staleness service and hooks
- [ ] TTA-0809 — Implement Celery recommendation tasks
- [ ] TTA-0810 — Add dashboard recommendations page
- [ ] TTA-0811 — Add dashboard saved jobs page
- [ ] TTA-0812 — Add save/unsave job actions
- [ ] TTA-0813 — Update job detail and dashboard navigation
- [ ] TTA-0814 — Add admin registrations
- [ ] TTA-0815 — Add tests
- [ ] TTA-0816 — Run acceptance commands and write report

## 3. Files Created

List new files.

## 4. Files Changed

List modified existing files and why.

## 5. Models and Migrations

List:

- models created
- fields
- choices
- constraints
- indexes
- migration files

## 6. Recommendation Generation Details

Document:

- usable profile rule
- active CV selection rule
- job prefilter rule
- how Phase 7 matching is reused
- ranking formula
- boost/penalty values
- top recommendation limit
- stale replacement behavior
- duplicate prevention behavior
- expired job behavior

## 7. Saved Jobs Details

Document:

- save behavior
- unsave behavior
- idempotency behavior
- expired/inactive saved-job display behavior
- ownership protections
- UUID route confirmation

## 8. Staleness and Tasks

Document:

- profile/CV hooks added
- staleness service behavior
- Celery tasks added
- what each task calls
- confirmation tasks contain no business logic beyond service calls

## 9. Pages and Templates

List:

- dashboard recommendation page
- dashboard saved jobs page
- save/unsave partials
- job detail changes
- dashboard nav changes

## 10. Security and Privacy

Confirm:

- no raw CV text in recommendations/templates
- no CV file path/URL in recommendations/templates
- `CVUpload.objects` used for active CV access, not `CVUpload.all_objects`
- saved jobs are owner-scoped
- recommendations are owner-scoped
- URLs use UUID public IDs only
- no internal integer IDs in public URLs

## 11. LLM / External API / Phase Boundary

Confirm:

- no OpenRouter import
- no LLM call
- no LLM ranking/scoring
- no France Travail live API call
- no email digest
- no transactional email
- no unsubscribe
- no privacy/account deletion
- no deployment work
- no Phase 9+ work

## 12. Test Results

Paste exact results for:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## 13. Boundary and Junk Checks

Paste exact results for:

```bash
grep -R "openrouter\|OpenRouter" apps/recommendations apps/jobs apps/dashboard -n || echo "OK no OpenRouter"
grep -R "francetravail\|FranceTravail\|api.francetravail" apps/recommendations apps/jobs apps/dashboard -n || echo "OK no live France Travail"
grep -R "email_digest\|unsubscribe\|send_mail" apps/recommendations apps/jobs apps/dashboard -n || echo "OK no email phase work"
grep -R "CVUpload.all_objects" apps/recommendations -n || echo "OK no all_objects in recommendations"
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

## 14. Known Issues / Follow-ups

List only real known issues. Do not claim blocked DB checks if local commands were not run. Do not hide failures.

## 15. Phase 8 Completion Statement

Write one clear statement:

```text
Phase 8 is complete. The agent did not start Phase 9.
```
