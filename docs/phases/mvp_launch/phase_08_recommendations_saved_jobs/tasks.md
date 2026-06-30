# Phase 8 — Recommendations and Saved Jobs — Tasks

## Phase Goal

Build the stored recommendation and saved-job layer on top of Phase 7 deterministic matching.

Phase 8 closes the MVP core loop:

```text
profile/CV -> deterministic match -> stored recommendations -> saved jobs
```

This phase must create:

- `apps/recommendations`
- `JobRecommendation`
- `RecommendationRun`
- `SavedJob`
- recommendation generation services
- dashboard recommendation query service
- saved/unsaved job service
- recommendation refresh Celery tasks
- dashboard recommendations page
- dashboard saved jobs page
- save/unsave buttons on job cards/detail pages
- tests proving ranking, staleness, idempotency, ownership, and phase boundaries

## Hard Boundary

The agent may work automatically through all Phase 8 tickets, but must not start Phase 9 or later.

Do **not** implement:

- OpenRouter or LLM calls
- LLM match explanations
- email digest
- transactional email
- unsubscribe pages
- privacy/account deletion flows
- admin observability dashboards
- deployment work
- React, Next.js, Angular, FastAPI, SQLAlchemy, MongoDB, or SPA architecture

Recommendations must be deterministic and must reuse the Phase 7 matching engine. The LLM must not rank, score, select, or explain recommendations in this phase.

## Required Architecture Rules

- Django only.
- Django ORM only.
- Django templates only.
- HTMX is allowed only for save/unsave and recommendation list partial updates.
- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data and do not call services or external APIs.
- No OpenRouter import or call.
- No France Travail live API call.
- Public URLs use UUID `public_id`, never internal integer IDs.
- User job search and recommendations read local PostgreSQL only.
- Saved jobs and recommendations are authenticated-user features.
- Saved jobs must be owner-scoped.
- Recommendation snapshots/results must not include raw CV text, CV file path, or CV file URL.

## Dependencies

Before Phase 8 starts, the following must be committed on `dev`:

- Phase 3 skill taxonomy
- Phase 4 job ingestion/normalization
- Phase 5 public jobs/search
- Phase 6 CV upload/profile completion
- Phase 7 deterministic matching/quick match

Preflight command:

```bash
git status --short
python manage.py test --settings=config.settings.local
```

Do not start Phase 8 if Phase 7 is uncommitted or tests are failing.

---

## TTA-0801 — Create `apps/recommendations` and register it

### Tasks

1. Create Django app:
   - `apps/recommendations`
   - `apps/recommendations/services/`
   - `apps/recommendations/tests/`
   - `apps/recommendations/tasks.py`
2. Register app in `INSTALLED_APPS`:
   - `apps.recommendations.apps.RecommendationsConfig`
3. Create a clean services package:
   - `apps/recommendations/services/recommendation.py`
   - `apps/recommendations/services/query.py`
   - `apps/recommendations/services/saved_jobs.py`
   - `apps/recommendations/services/active_users.py`
   - `apps/recommendations/services/staleness.py`
4. Do not create a generic API app.
5. Do not create DRF/API endpoints.

### Acceptance

- App imports cleanly.
- App is registered.
- `python manage.py check --settings=config.settings.local` passes.

---

## TTA-0802 — Create recommendation and saved-job models

### Tasks

Create models in `apps/recommendations/models.py`.

#### `JobRecommendation`

Required fields:

- `user = ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)`
- `profile = ForeignKey("profiles.CandidateProfile", on_delete=models.CASCADE)`
- `cv_upload = ForeignKey("cvs.CVUpload", null=True, blank=True, on_delete=models.SET_NULL)`
- `job = ForeignKey("jobs.NormalizedJob", on_delete=models.CASCADE)`
- `fit_score = PositiveSmallIntegerField()`
- `ranking_score = DecimalField(max_digits=6, decimal_places=2)`
- `rank = PositiveIntegerField()`
- `strong_skills_json = JSONField(default=list, blank=True)`
- `missing_skills_json = JSONField(default=list, blank=True)`
- `risk_flags_json = JSONField(default=list, blank=True)`
- `profile_signals_json = JSONField(default=list, blank=True)`
- `reason_summary = TextField(blank=True)`
- `recommendation_version = CharField(max_length=32, default="reco_v1")`
- `computed_at = DateTimeField()`
- `status = CharField(...)`
- `created_at`, `updated_at`

Statuses:

- `active`
- `stale`
- `dismissed`
- `expired_job`

Required constraints/indexes:

- unique `(user, job, recommendation_version)` for MVP
- indexes for user/status/ranking, user/rank, job/status, computed_at, recommendation_version

#### `RecommendationRun`

Required fields:

- `user = ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)`
- `trigger_type = CharField(...)`
- `status = CharField(...)`
- `started_at = DateTimeField()`
- `finished_at = DateTimeField(null=True, blank=True)`
- `candidate_jobs_count = PositiveIntegerField(default=0)`
- `scored_jobs_count = PositiveIntegerField(default=0)`
- `stored_recommendations_count = PositiveIntegerField(default=0)`
- `error_message = TextField(blank=True)`
- `created_at`

Trigger types:

- `cv_uploaded`
- `cv_replaced`
- `profile_updated`
- `new_jobs_imported`
- `dashboard_stale_refresh`
- `nightly_refresh`
- `manual_admin`

Statuses:

- `running`
- `success`
- `partial_success`
- `failed`

#### `SavedJob`

Required fields:

- `user = ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)`
- `job = ForeignKey("jobs.NormalizedJob", on_delete=models.CASCADE)`
- `notes = TextField(blank=True)`
- `saved_at = DateTimeField(auto_now_add=True)`

Required constraints/indexes:

- unique `(user, job)`
- indexes for user, job, saved_at

### Rules

- Do not store raw CV text.
- Do not store CV file path.
- Do not store CV file URL.
- Do not add LLM fields in Phase 8.
- Public URLs should use `job.public_id`; no URL should expose recommendation/saved-job integer IDs.

### Acceptance

- Migrations are created.
- Constraints are tested.
- `makemigrations --check --dry-run` passes after migrations are created.

---

## TTA-0803 — Implement recommendation result dataclasses

### Tasks

Create deterministic service result dataclasses, for example:

```python
@dataclass(frozen=True)
class RecommendationResult:
    run_id: int | None
    recommendations_created: int
    recommendations_updated: int
    recommendations_marked_stale: int
    candidate_jobs_count: int
    scored_jobs_count: int
    stored_recommendations_count: int
    skipped_reason: str | None = None

@dataclass(frozen=True)
class RecommendationDashboardResult:
    recommendations: list[JobRecommendation]
    is_pending: bool
    is_stale: bool
    latest_run: RecommendationRun | None
```

Adjust names if needed, but keep service outputs explicit and testable.

### Acceptance

- Views do not infer complex recommendation states themselves.
- Services return structured results.

---

## TTA-0804 — Implement `RecommendationService.refresh_for_user()`

### Service location

`apps/recommendations/services/recommendation.py`

### Contract

```python
RecommendationService.refresh_for_user(user: User, trigger_type: str) -> RecommendationResult
```

### Required flow

1. Create `RecommendationRun(status="running")`.
2. Validate user has a usable profile.
3. Get active CV if available using `CVUpload.objects`, not `CVUpload.all_objects`.
4. Prefilter visible local jobs only.
5. For each candidate job, call Phase 7 `MatchScoringService.calculate(...)`.
6. Calculate deterministic `ranking_score`.
7. Store top recommendations.
8. Mark old active recommendations stale or update existing rows atomically.
9. Complete `RecommendationRun` as success/failed.

### Usable profile rule

Use existing Phase 6 profile completion/completeness logic where possible.

For MVP, a usable profile should have enough deterministic data for matching, for example:

- a `CandidateProfile`
- either active CV-derived/manual skills, or enough profile skills
- target role/job type where available

Do not invent a large onboarding system.

If the profile is not usable:

- create and complete a `RecommendationRun`
- store zero recommendations
- return `skipped_reason="profile_incomplete"`

### Job prefilter rules

Use existing Phase 5 public job visibility logic where possible.

Prefilter only local PostgreSQL jobs:

- source active
- job status active/open according to existing model fields
- not expired
- France-first jobs
- job type roughly matches profile target type where possible
- skill overlap exists where possible
- not dismissed by this user

Do **not** call France Travail or any external API.

### Ranking formula

Use the roadmap formula:

```text
ranking_score = fit_score + freshness_boost + target_type_boost + user_preference_boost - stale_job_penalty
```

Implementation rules:

- `fit_score` comes from Phase 7 deterministic matching.
- Boosts/penalties must be deterministic and documented in the service.
- Clamp or bound ranking output to a reasonable range.
- Do not let LLM influence ranking.
- Do not duplicate the Phase 7 scoring engine; reuse it.

### Storage rules

- Store top recommendations only; default limit can be 20.
- Assign rank starting at 1.
- Saving the same recommendation twice must not create duplicates.
- Refreshing twice must update/replace safely.
- Use a DB transaction when replacing active recommendations.
- Preserve dismissed recommendations as dismissed.
- Expired jobs must not remain active recommendations.

### Acceptance

- Recommendations are generated for a usable profile.
- Incomplete profile skips recommendations cleanly.
- Ranking score uses fit score plus deterministic boosts/penalties.
- Duplicate recommendations are not created.
- Refreshing twice is idempotent.
- Old active recommendations become stale when replaced.
- Expired jobs are marked `expired_job` or excluded from active recommendations.

---

## TTA-0805 — Implement `RecommendationQueryService`

### Service location

`apps/recommendations/services/query.py`

### Contract

```python
RecommendationQueryService.get_dashboard_recommendations(user: User, limit: int = 20) -> RecommendationDashboardResult
```

### Required behavior

- Return active stored recommendations when fresh recommendations exist.
- If recommendations are stale, return existing stale recommendations and enqueue refresh.
- If none exist, enqueue generation and return pending state.
- Dashboard views must not compute heavy recommendations synchronously.
- Query service must use owner-scoped queries.

### Refresh enqueue rule

Use Celery task `refresh_user_recommendations.delay(...)` or `apply_async(...)` through a small wrapper if Pyright requires typing help.

Do not fail the page if enqueue fails. Log and return a safe pending/stale state.

### Acceptance

- Dashboard page does not block on heavy refresh.
- Missing recommendations enqueue generation.
- Stale recommendations enqueue refresh.
- Existing recommendations are returned while refresh is pending.

---

## TTA-0806 — Implement `SavedJobService`

### Service location

`apps/recommendations/services/saved_jobs.py`

### Contracts

```python
SavedJobService.save_job(user: User, job_public_id: UUID) -> SavedJob
SavedJobService.remove_saved_job(user: User, job_public_id: UUID) -> ServiceResult
SavedJobService.get_saved_jobs(user: User) -> QuerySet[SavedJob]
SavedJobService.is_saved(user: User, job_public_id: UUID) -> bool
```

### Required behavior

- Use `JobQueryService.get_public_job(job_public_id)` or equivalent Phase 5 visibility logic.
- Saving the same job twice returns the existing `SavedJob`.
- Removing a non-saved job is safe/idempotent.
- Saved jobs are always user-owned.
- Expired/inactive saved jobs remain visible on saved-jobs page with a status label, but cannot be newly saved if no longer public.
- Record `UserEventService.record("saved_job_created", ...)` if existing analytics service is available. Failure to record must not fail save.

### Acceptance

- Save is idempotent.
- Remove is idempotent.
- A user cannot affect another user's saved jobs.
- Expired saved jobs show status.
- No internal integer job ID is used in URLs.

---

## TTA-0807 — Implement `ActiveUserRecommendationService`

### Service location

`apps/recommendations/services/active_users.py`

### Contract

```python
ActiveUserRecommendationService.get_active_users(days: int = 14) -> QuerySet[User]
```

### Required behavior

Return users who:

- logged in recently where `last_login` exists
- have a usable profile
- have an active CV or enough manual profile data

This service is used by the bulk recommendation refresh task. It must not send email.

### Acceptance

- Active users can be selected for refresh.
- No digest/email logic is added.

---

## TTA-0808 — Implement recommendation staleness service and hooks

### Service location

`apps/recommendations/services/staleness.py`

### Contract

```python
RecommendationStalenessService.mark_user_recommendations_stale(user: User, reason: str) -> int
```

### Required behavior

- Mark active recommendations for the user as stale.
- Safe if the user has no recommendations.
- Do not enqueue refresh from model methods.
- If hooking into profile/CV service flows, call this from services only, not models.

### Required hooks

Where safe and existing services are available, mark recommendations stale after meaningful changes:

- profile update
- CV uploaded/replaced/parsed into profile skills
- CV soft delete

Do not overbuild event sourcing.

### Acceptance

- Profile update marks active recommendations stale.
- CV/profile skill changes mark recommendations stale where hooked.
- No model method calls recommendation services.

---

## TTA-0809 — Implement Celery recommendation tasks

### File

`apps/recommendations/tasks.py`

### Tasks

```python
refresh_user_recommendations(user_id: int, trigger_type: str) -> dict
refresh_active_users_recommendations() -> dict
```

### Rules

- Tasks call services only.
- Tasks do not contain recommendation logic.
- Tasks do not call OpenRouter.
- Tasks do not call France Travail.
- Tasks do not send email.
- Tasks handle missing users safely.

### Acceptance

- Single-user refresh task calls `RecommendationService.refresh_for_user`.
- Bulk refresh task calls `ActiveUserRecommendationService.get_active_users` and dispatches/executes single-user refresh safely.
- Tests cover missing user and service failure behavior.

---

## TTA-0810 — Add dashboard recommendations page

### URL

`/dashboard/recommendations/`

### View name

`dashboard:recommendations`

### Template

`templates/dashboard/recommendations.html`

### Required behavior

- Authenticated only.
- Calls `RecommendationQueryService.get_dashboard_recommendations(user)`.
- Does not compute heavy recommendations synchronously.
- Shows pending state if generation was enqueued.
- Shows stale state if old recommendations are shown while refresh is pending.
- Shows recommendation cards from stored `JobRecommendation` rows.
- Each recommendation links to job detail using `job.public_id`.
- Each recommendation can show save/unsave state.

### Partials

- `templates/recommendations/partials/recommendation_list.html`
- `templates/recommendations/partials/recommendation_card.html`

### Acceptance

- User sees stored recommendations.
- No heavy synchronous refresh in view.
- Only current user's recommendations are shown.

---

## TTA-0811 — Add dashboard saved jobs page

### URL

`/dashboard/saved-jobs/`

### View name

`dashboard:saved_jobs`

### Template

`templates/dashboard/saved_jobs.html`

### Required behavior

- Authenticated only.
- Calls `SavedJobService.get_saved_jobs(user)` or a dedicated query method.
- Lists only current user's saved jobs.
- Links to job detail with `job.public_id`.
- Expired/inactive jobs show status label.
- User can remove saved job.

### Acceptance

- User sees saved jobs.
- User cannot see another user's saved jobs.
- Expired saved jobs show status.
- Remove action works.

---

## TTA-0812 — Add save/unsave job actions

### URLs

Use UUID public IDs only:

```text
POST /jobs/<uuid:public_id>/save/
POST /jobs/<uuid:public_id>/unsave/
```

Recommended view names:

- `jobs:save`
- `jobs:unsave`

### Views

Add thin views in `apps/jobs/views.py` or another existing URL owner if the project already has a cleaner route convention.

### Required behavior

- Authenticated only.
- Use `SavedJobService`.
- Support normal POST redirect.
- Support HTMX partial response where existing template convention allows it.
- Never accept internal integer job IDs.

### Partial

`templates/jobs/partials/save_button.html`

### Acceptance

- Save button appears on job detail and recommendation card.
- Save is idempotent.
- Unsave is idempotent.
- HTMX updates button state if HTMX is used.

---

## TTA-0813 — Update job detail and dashboard navigation

### Tasks

1. Add save/unsave control to `templates/jobs/job_detail.html`.
2. Add recommendations and saved jobs links to dashboard navigation if a dashboard nav exists.
3. Add recommendation preview to dashboard home only if existing dashboard structure supports it cleanly:
   - `templates/dashboard/partials/recommendation_preview.html`

### Rules

- Do not redesign the full UI.
- Do not introduce Alpine unless strictly needed.
- Do not introduce React or SPA behavior.
- Do not add email preferences/digest UI.

### Acceptance

- Navigation is usable.
- Job detail save/unsave works.
- Dashboard pages are discoverable.

---

## TTA-0814 — Add admin registrations

### Tasks

Add admin classes for:

- `JobRecommendation`
- `RecommendationRun`
- `SavedJob`

### Rules

- Read-only or safe admin fields for computed data.
- No admin action that calls external APIs.
- No Phase 12 observability dashboard.

### Acceptance

- Admin imports cleanly.
- Admin does not expose secrets or raw CV content.

---

## TTA-0815 — Add tests

### Required tests

Add tests for:

#### Models

- `SavedJob` unique `(user, job)`.
- `JobRecommendation` unique `(user, job, recommendation_version)`.
- `RecommendationRun` status/trigger values.

#### Recommendation service

- Recommendations generated for usable profile.
- Incomplete profile skips recommendations.
- Ranking score uses fit score plus deterministic boosts/penalties.
- Duplicate recommendations are not created.
- Refreshing twice does not duplicate rows.
- Old active recommendations are marked stale when replaced.
- Expired jobs are excluded or marked `expired_job`.
- No raw CV text/path/url is stored in recommendation JSON.

#### Query service

- Dashboard returns active recommendations.
- No recommendations enqueues refresh and returns pending state.
- Stale recommendations enqueue refresh and return existing stale rows.
- Dashboard query is owner-scoped.

#### Saved jobs

- Save is idempotent.
- Remove is idempotent.
- User cannot remove another user's saved job.
- Expired saved jobs are listed with status.
- Save/unsave routes use UUID public_id.
- Internal integer routes do not exist.

#### Celery tasks

- `refresh_user_recommendations` calls `RecommendationService`.
- Missing user is handled safely.
- `refresh_active_users_recommendations` uses `ActiveUserRecommendationService`.
- Tasks contain no business logic beyond calling services.

#### Boundary tests

- No OpenRouter import/call in recommendations.
- No France Travail live API call in recommendations/saved jobs/dashboard.
- No email digest/unsubscribe code.
- No Phase 9+ files/features.

### Acceptance

- Tests are meaningful.
- Do not delete existing tests to pass.
- Full suite passes.

---

## TTA-0816 — Run acceptance commands and write report

### Required commands

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

### Junk checks

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

### Required report

Create:

```text
docs/phases/phase_08_recommendations_saved_jobs/agent_report.md
```

Use the template in `agent_report_template.md` and paste exact command results.
