# Phase 8 — Recommendations and Saved Jobs — Agent Prompt

You are implementing Phase 8 for TuniTech Abroad.

Read `AGENTS.md` first. Then read this whole phase folder:

- `docs/phases/phase_08_recommendations_saved_jobs/tasks.md`
- `docs/phases/phase_08_recommendations_saved_jobs/acceptance.md`
- `docs/phases/phase_08_recommendations_saved_jobs/agent_report_template.md`

## Mission

Implement stored job recommendations and saved jobs on top of the Phase 7 deterministic matching engine.

Phase 8 must make the recommendation loop usable:

```text
profile/CV -> deterministic matching -> stored recommendations -> save jobs
```

## Current Product Context

TuniTech Abroad is a France-first job intelligence platform for Tunisian IT candidates, students, bootcamp graduates, internship seekers, and junior/mid-level developers.

The product is not a generic job board. The core flow is:

```text
Tunisian IT profile -> France IT jobs/internships -> CV/profile parsing -> job matching -> missing skill detection -> recommendations
```

Completed phases should already provide:

- auth/accounts
- `CandidateProfile` and `ProfileSkill`
- skill taxonomy and skill normalization
- local PostgreSQL job ingestion/normalization
- public local job search/detail pages
- private CV upload/parsing/profile completion
- deterministic match scoring and quick match

## Build Scope

Allowed:

- `apps/recommendations`
- recommendation models
- saved-job model
- deterministic recommendation generation
- ranking based on Phase 7 fit score plus deterministic boosts
- recommendation query service
- saved job service
- recommendation staleness service
- Celery refresh tasks
- dashboard recommendations page
- dashboard saved jobs page
- save/unsave buttons
- tests

Not allowed:

- OpenRouter or LLM calls/imports
- LLM explanations
- email digest
- transactional emails
- unsubscribe flows
- privacy/account deletion flows
- admin observability dashboards
- deployment work
- React/Next/Angular/FastAPI/SQLAlchemy/MongoDB/SPA
- live France Travail API calls

## Architecture Rules

- Views stay thin.
- Business logic goes in `apps/recommendations/services/`.
- Celery tasks call services only.
- Models do not call services or external APIs.
- Use Django ORM only.
- Use Django templates and HTMX only where useful.
- No OpenRouter import or call.
- No external network calls.
- No live France Travail calls.
- Public URLs use UUID `public_id`, never internal integer IDs.
- Saved jobs and recommendations are owner-scoped.
- Dashboard must read stored recommendations; it must not compute heavy recommendation refresh synchronously.

## Implementation Rules

1. Start from clean `dev` with Phase 7 committed.
2. Create `apps/recommendations`.
3. Add models and migrations.
4. Reuse Phase 7 `MatchScoringService`; do not duplicate match scoring.
5. Use active/private-safe CV access: `CVUpload.objects`, not `CVUpload.all_objects`, except admin/privacy/internal deletion tasks.
6. Use existing local public-job visibility logic where possible.
7. Save/unsave actions must use `job.public_id` only.
8. Recommendation generation must be deterministic.
9. Recommendation ranking must be deterministic.
10. No LLM can influence fit score or ranking.
11. Do not store raw CV text, CV file paths, or CV URLs in recommendations.
12. Do not hide failing tests by deleting them.

## Required Services

Create or adapt these services:

```text
apps/recommendations/services/recommendation.py
apps/recommendations/services/query.py
apps/recommendations/services/saved_jobs.py
apps/recommendations/services/active_users.py
apps/recommendations/services/staleness.py
```

### `RecommendationService`

Main contract:

```python
RecommendationService.refresh_for_user(user, trigger_type: str) -> RecommendationResult
```

Must:

- create `RecommendationRun`
- validate usable profile
- get active CV if available
- prefilter local active France-first jobs
- call Phase 7 matching service per candidate job
- calculate deterministic ranking score
- store top recommendations
- avoid duplicates
- mark old recommendations stale/update existing rows atomically
- complete run status honestly

### `RecommendationQueryService`

Main contract:

```python
RecommendationQueryService.get_dashboard_recommendations(user, limit: int = 20) -> RecommendationDashboardResult
```

Must:

- return stored recommendations
- enqueue refresh when none or stale
- not compute heavy refresh synchronously in dashboard view
- owner-scope all reads

### `SavedJobService`

Main contracts:

```python
SavedJobService.save_job(user, job_public_id)
SavedJobService.remove_saved_job(user, job_public_id)
SavedJobService.get_saved_jobs(user)
SavedJobService.is_saved(user, job_public_id)
```

Must:

- use job public UUID
- be idempotent
- be owner-scoped
- use existing public job visibility for new saves
- show expired saved jobs as saved history/status but do not newly save invisible jobs

### `ActiveUserRecommendationService`

Main contract:

```python
ActiveUserRecommendationService.get_active_users(days: int = 14)
```

Must:

- select users recently active
- require usable profile
- not send email

### `RecommendationStalenessService`

Main contract:

```python
RecommendationStalenessService.mark_user_recommendations_stale(user, reason: str) -> int
```

Must:

- mark active recommendations stale after profile/CV changes through services
- not be called from model methods

## Required Tasks

Create:

```text
apps/recommendations/tasks.py
```

Tasks:

```python
refresh_user_recommendations(user_id: int, trigger_type: str) -> dict
refresh_active_users_recommendations() -> dict
```

Rules:

- tasks call services only
- no recommendation logic in tasks
- no email
- no OpenRouter
- no France Travail

## Required Pages

Add dashboard pages:

```text
/dashboard/recommendations/
/dashboard/saved-jobs/
```

Add save actions:

```text
POST /jobs/<uuid:public_id>/save/
POST /jobs/<uuid:public_id>/unsave/
```

Templates:

```text
templates/dashboard/recommendations.html
templates/dashboard/saved_jobs.html
templates/recommendations/partials/recommendation_list.html
templates/recommendations/partials/recommendation_card.html
templates/jobs/partials/save_button.html
```

Update job detail page with save/unsave button.

## Required Tests

Cover:

- recommendation model constraints
- saved-job unique constraint
- recommendation generation for usable profile
- incomplete profile skip
- ranking formula behavior
- no duplicate recommendations
- stale refresh behavior
- dashboard query pending/stale behavior
- saved job idempotency
- save/unsave ownership
- expired saved job status
- UUID-only routes
- Celery task calls services
- no LLM/OpenRouter
- no live France Travail
- no email phase work

## Required Final Report

Create:

```text
docs/phases/phase_08_recommendations_saved_jobs/agent_report.md
```

Use `agent_report_template.md` and include exact command outputs.

## Required Commands

Run all:

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

Then run boundary checks:

```bash
grep -R "openrouter\|OpenRouter" apps/recommendations apps/jobs apps/dashboard -n || echo "OK no OpenRouter"
grep -R "francetravail\|FranceTravail\|api.francetravail" apps/recommendations apps/jobs apps/dashboard -n || echo "OK no live France Travail"
grep -R "email_digest\|unsubscribe\|send_mail" apps/recommendations apps/jobs apps/dashboard -n || echo "OK no email phase work"
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

## Completion Rule

You may work automatically through all Phase 8 tickets.

You must stop after Phase 8.

Do not start Phase 9 unless the user explicitly asks.
