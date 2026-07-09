# Phase 8 — Recommendations and Saved Jobs — Acceptance Criteria

## Required Result

Phase 8 is accepted only when stored deterministic recommendations and saved jobs work end-to-end without introducing Phase 9+ behavior.

## Functional Acceptance

### Recommendations app

- `apps.recommendations` exists and is registered.
- `JobRecommendation` exists.
- `RecommendationRun` exists.
- `SavedJob` exists.
- Migrations are present and valid.
- Admin registrations import cleanly.

### Recommendation models

- `JobRecommendation` stores:
  - owner user
  - profile used
  - optional active CV used
  - recommended job
  - fit score
  - ranking score
  - rank
  - strong skills
  - missing skills
  - risk flags
  - profile signals
  - deterministic reason summary
  - recommendation version
  - computed timestamp
  - status
- `RecommendationRun` stores trigger/status/counts/error details.
- `SavedJob` stores owner user, job, optional notes, and saved timestamp.
- Unique constraints prevent duplicate saved jobs and duplicate MVP recommendations.

### Recommendation generation

- `RecommendationService.refresh_for_user(user, trigger_type)` exists.
- It creates a `RecommendationRun`.
- It skips incomplete/unusable profiles cleanly.
- It uses the active CV if available through `CVUpload.objects`.
- It prefilters local active France-first jobs.
- It does not call France Travail live API.
- It calls Phase 7 deterministic matching service for candidate jobs.
- It does not duplicate match scoring logic.
- It calculates deterministic ranking score.
- It stores top recommendations.
- It does not create duplicate recommendations on repeated refresh.
- It marks old active recommendations stale or updates existing rows safely.
- It handles expired jobs by excluding them from active recommendations or marking old rows `expired_job`.
- It never stores raw CV text, CV file path, or CV file URL.

### Ranking

- Ranking is deterministic.
- Ranking uses:

```text
ranking_score = fit_score + freshness_boost + target_type_boost + user_preference_boost - stale_job_penalty
```

- `fit_score` comes from Phase 7 deterministic matching.
- Boosts/penalties are documented in code or service comments.
- LLM does not influence ranking.

### Recommendation query/dashboard

- `RecommendationQueryService.get_dashboard_recommendations(user, limit=20)` exists.
- Dashboard reads stored recommendations only.
- Dashboard does not compute heavy recommendations synchronously.
- If no recommendations exist, query service enqueues generation and returns pending state.
- If recommendations are stale, query service returns existing rows and enqueues refresh.
- Only current user's recommendations are returned.
- `/dashboard/recommendations/` exists and is authenticated.
- Page shows pending/stale states.
- Recommendation cards link to jobs with `job.public_id` only.

### Saved jobs

- `SavedJobService.save_job(user, job_public_id)` exists.
- `SavedJobService.remove_saved_job(user, job_public_id)` exists.
- `SavedJobService.get_saved_jobs(user)` or equivalent query exists.
- `SavedJobService.is_saved(user, job_public_id)` exists.
- Save is idempotent.
- Remove is idempotent.
- User cannot remove or list another user's saved jobs.
- Newly saving an invisible/expired job is blocked by existing public job visibility logic.
- Previously saved expired/inactive jobs remain visible on the saved jobs page with a status label.
- `/dashboard/saved-jobs/` exists and is authenticated.
- Save/unsave URLs use UUID `public_id`, not integer IDs.

### Save/unsave UI

- Job detail page has save/unsave control for authenticated users.
- Recommendation cards have save/unsave control.
- Optional HTMX response updates `templates/jobs/partials/save_button.html`.
- Non-HTMX POST redirects safely.
- Anonymous users are redirected to login or shown login CTA.

### Staleness and refresh

- `RecommendationStalenessService.mark_user_recommendations_stale(user, reason)` exists.
- Profile update marks recommendations stale through services.
- CV upload/replacement/parsing/delete marks recommendations stale where safely hooked through services.
- No model method calls recommendation services.
- Celery task `refresh_user_recommendations` exists and calls services only.
- Celery task `refresh_active_users_recommendations` exists and calls services only.
- Bulk refresh does not send email.

## Security and Privacy Acceptance

- No raw CV text appears in recommendation rows, snapshots, templates, or tests.
- No CV file path or URL appears in recommendation rows, snapshots, templates, or tests.
- Saved jobs and recommendations are owner-scoped.
- No internal integer IDs are exposed in public URLs.
- No OpenRouter key or import exists.
- No live France Travail API call exists.
- Dashboard pages require authentication.

## Phase Boundary Acceptance

Must not create or implement:

- OpenRouter client usage
- LLM recommendation explanations
- LLM ranking/scoring
- email digest
- transactional email sending
- unsubscribe pages
- privacy/account deletion flows
- admin observability dashboards
- deployment configuration
- React/Next/Angular/FastAPI/SQLAlchemy/MongoDB/SPA

## Required Commands

The phase is not accepted until these pass locally:

```bash
source .venv/bin/activate
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

## Required Boundary Checks

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

## Required Review Package

After implementation, prepare a review package named:

```text
phase8_review_package.zip
```

Include:

```text
apps/recommendations
apps/jobs/views.py
apps/jobs/urls.py
apps/jobs/tests
apps/dashboard/views.py
apps/dashboard/urls.py
apps/dashboard/tests.py if changed/created
apps/cvs/services if changed
apps/profiles/services if changed
config/settings/base.py
config/urls.py if changed
templates/dashboard/recommendations.html
templates/dashboard/saved_jobs.html
templates/dashboard/partials if changed
templates/recommendations
templates/jobs/job_detail.html
templates/jobs/partials/save_button.html
docs/phases/phase_08_recommendations_saved_jobs
phase8_git_status.txt
phase8_diff_stat.txt
phase8_diff.patch
```

Exclude:

```text
.env
.venv/
.git/
__pycache__/
*.pyc
media/
private_media/
staticfiles/
celerybeat-schedule*
*.sqlite3
```
