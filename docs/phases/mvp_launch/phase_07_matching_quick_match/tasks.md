# Phase 7 — Deterministic Matching and Quick Match — Tasks

## Phase Goal

Build the deterministic scoring engine and match-result workflow.

Phase 7 turns the existing local PostgreSQL job data, user profile data, profile skills, and active CV metadata into explainable match results.

This phase must create:

- `apps/matching`
- deterministic match scoring
- persisted authenticated match results
- anonymous quick match sessions
- match detail pages
- match history page
- job detail match actions
- quick match form/result partials
- tests proving score behavior, security, ownership, and phase boundaries

## Hard Boundary

The agent may work automatically through all Phase 7 tickets, but must not start Phase 8.

Do **not** implement:

- recommendations
- saved jobs
- recommendation ranking/storage
- email digest
- unsubscribe
- OpenRouter/LLM calls
- match explanation LLM endpoint
- CV upload/parsing changes except safe reads of existing Phase 6 models
- privacy/account deletion flows
- deployment work

LLM is not allowed in Phase 7. Final fit score must be deterministic.

## Required Architecture Rules

- Django only.
- Django ORM only.
- Django templates only.
- HTMX is allowed only for quick-match progressive enhancement.
- Views stay thin.
- Business logic goes in services.
- Celery tasks, if added, must call services only. Prefer no Celery work in this phase unless explicitly needed.
- No OpenRouter import or call.
- No France Travail live API call from matching, quick match, job detail, or match detail.
- Public URLs use UUID `public_id`, never internal integer IDs.
- Match detail must be owner-protected.
- Quick match must not require login.
- Quick match must expire.
- Quick match must be rate-limited by session/IP hash using local DB only.

## Dependencies

Before Phase 7 starts, the following should be committed on `dev`:

- Phase 3 skill taxonomy
- Phase 4 job ingestion/normalization
- Phase 5 public job search/pages
- Phase 6 CV upload/profile completion

## TTA-0701 — Create `apps/matching` and register routes

### Tasks

1. Create Django app:
   - `apps/matching`
   - `apps/matching/services/`
   - `apps/matching/tests/`
   - `apps/matching/urls.py`
2. Register app in `INSTALLED_APPS`:
   - `apps.matching.apps.MatchingConfig`
3. Include routes in `config/urls.py`:
   - `path("matches/", include("apps.matching.urls"))` for public quick/full match endpoints if needed
   - dashboard match routes may be added through `apps/dashboard/urls.py` if the existing dashboard app owns dashboard navigation
4. Do not create duplicate job search URLs.
5. Do not create `/matches/<int:id>/` or any internal-ID route.

### Acceptance

- `python manage.py check` passes.
- `apps.matching` imports cleanly.
- No Phase 8 files or models are created.

## TTA-0702 — Create matching models

### Required model: `MatchResult`

Create `apps.matching.models.MatchResult`.

Fields:

- `id`: BigAutoField default
- `public_id`: UUIDField, default uuid4, unique, editable False, db_index True
- `user`: FK to `settings.AUTH_USER_MODEL`, CASCADE, related name `match_results`
- `profile`: FK to `profiles.CandidateProfile`, PROTECT or CASCADE; prefer PROTECT if compatible with existing deletion strategy
- `cv_upload`: nullable FK to `cvs.CVUpload`, SET_NULL, blank True
- `job`: FK to `jobs.NormalizedJob`, PROTECT, related name `match_results`
- `profile_snapshot_json`: JSONField default dict
- `job_snapshot_json`: JSONField default dict
- `fit_score`: PositiveSmallIntegerField
- `technical_skills_score`: PositiveSmallIntegerField
- `experience_score`: PositiveSmallIntegerField
- `role_title_score`: PositiveSmallIntegerField
- `language_score`: PositiveSmallIntegerField
- `location_score`: PositiveSmallIntegerField
- `strong_skills_json`: JSONField default list, blank True
- `missing_required_skills_json`: JSONField default list, blank True
- `missing_optional_skills_json`: JSONField default list, blank True
- `risk_flags_json`: JSONField default list, blank True
- `profile_signals_json`: JSONField default list, blank True
- `recommended_actions_json`: JSONField default list, blank True
- `llm_explanation_status`: CharField choices, default `not_requested`
- `llm_explanation_text`: TextField blank True
- `scoring_version`: CharField default `score_v1`
- `created_at`: DateTimeField auto_now_add
- `updated_at`: DateTimeField auto_now

LLM status choices:

- `not_requested`
- `disabled`
- `pending`
- `generated`
- `failed`

Phase 7 must only use `not_requested` or `disabled`.

Indexes:

- `public_id`
- `user`, `job`
- `user`, `created_at`
- `job`, `fit_score`
- `fit_score`
- `created_at`
- `llm_explanation_status`
- `scoring_version`

Do not add unique `(user, job)`. Users may recompute after profile/CV changes.

### Required model: `QuickMatchSession`

Create `apps.matching.models.QuickMatchSession`.

Fields:

- `id`: BigAutoField default
- `public_id`: UUIDField, default uuid4, unique, editable False, db_index True
- `session_key_hash`: CharField max_length 64, db_index True
- `ip_hash`: CharField max_length 64, blank True, db_index True
- `job`: FK to `jobs.NormalizedJob`, PROTECT, related name `quick_match_sessions`
- `entered_skills_json`: JSONField default list
- `normalized_skills_json`: JSONField default list, blank True
- `experience_level`: CharField max_length 50
- `french_level`: CharField max_length 50
- `estimated_fit_score`: PositiveSmallIntegerField
- `matched_skills_json`: JSONField default list, blank True
- `missing_skills_json`: JSONField default list, blank True
- `risk_flags_json`: JSONField default list, blank True
- `created_at`: DateTimeField auto_now_add
- `expires_at`: DateTimeField db_index True

Indexes:

- `public_id`
- `session_key_hash`
- `ip_hash`
- `job`
- `created_at`
- `expires_at`
- `estimated_fit_score`

### Acceptance

- Migrations are clean.
- `public_id` exists and is used for public/detail URLs.
- No internal integer ID URLs are introduced.

## TTA-0703 — Implement scoring result dataclasses

Create `apps/matching/services/scoring.py` with dataclasses:

```python
@dataclass(frozen=True)
class FitScoreResult:
    fit_score: int
    technical_skills_score: int
    experience_score: int
    role_title_score: int
    language_score: int
    location_score: int
    strong_skills: list[dict[str, str]]
    missing_required_skills: list[dict[str, str]]
    missing_optional_skills: list[dict[str, str]]
    risk_flags: list[str]
    profile_signals: list[str]
    recommended_actions: list[str]
    scoring_version: str = "score_v1"
```

Keep dataclasses serializable. Do not pass model instances inside JSON fields.

## TTA-0704 — Implement `MatchScoringService`

Location:

- `apps/matching/services/scoring.py`

Contract:

```python
MatchScoringService.calculate(
    profile: CandidateProfile,
    job: NormalizedJob,
    cv_upload: CVUpload | None = None,
) -> FitScoreResult
```

### Required deterministic formula

```text
fit_score =
technical_skills_score * 0.45
+ experience_score * 0.20
+ role_title_score * 0.15
+ language_score * 0.10
+ location_score * 0.10
```

Round to nearest integer and clamp all scores to `0..100`.

### Technical score rules

Use `ProfileSkill.normalized_name` and `NormalizedJobSkill.skill.canonical_name` / normalized canonical names.

- Required skills count for 80% of technical score.
- Optional skills count for 20% of technical score.
- If no required job skills exist, use all detected skills and add `low_confidence_job_skills` to profile signals.
- Missing required skills add `missing_required_skills` risk flag.
- Strong skills are matched canonical skill names.
- Missing required/optional skills are serializable dicts with at least `name` and `requirement_type`.

### Experience score rules

Use profile `years_experience`, `current_level`, and job `experience_level`.

Simple deterministic version:

- internship job: 100 if profile level internship/student/junior or years <= 1; otherwise 80
- junior job: 100 if years >= 0.5 or level junior/mid/senior; 60 if missing; 40 if only internship/student
- mid-level job: 100 if years >= 2; 70 if years >= 1; 40 if missing or less
- senior job: 100 if years >= 5; 60 if years >= 3; 30 otherwise and risk `experience_too_low`
- unknown job: 70

Add `experience_too_low` when clear mismatch.

### Role/title score rules

Use profile target roles and job title.

- 100 if any target role token appears in title.
- 75 if no target role exists but title is non-empty.
- 50 if target roles exist but no match.
- 60 fallback.

Do not call LLM.

### Language score rules

Use profile French/English fields and job language requirements JSON if available.

Minimum:

- If job appears France-first and profile `french_level` is blank, add `french_level_missing` and score 40.
- If job language requirements explicitly require English and profile `english_level` blank, add `english_level_missing` and score max 60.
- If French is present, score at least 80.
- If both relevant languages present, score 100.
- Unknown requirements fallback 70.

### Location score rules

Use profile `target_country`, `location`, `remote_preference`, `relocation_preference`, and job `country`, `remote_type`.

Minimum:

- remote job: 100 if profile accepts remote or remote preference blank; otherwise 80
- France target and France job: 90+
- relocation preference positive and France job: 80+
- unknown location: 70
- clear mismatch: 50

### Risk flags

Allowed Phase 7 risk flags:

- `experience_too_low`
- `missing_required_skills`
- `french_level_missing`
- `english_level_missing`
- `profile_incomplete`
- `job_may_be_expired`
- `internship_type_unclear`

If job `status` is not active or `expires_at` is in the past, add `job_may_be_expired`.

If profile completion score is below 50, add `profile_incomplete`.

If job is internship/apprenticeship but contract/title ambiguous, add `internship_type_unclear` only if logic is clear.

### Profile signals

Allowed Phase 7 profile signals:

- `profile_signal_missing_github`
- `profile_signal_missing_linkedin`
- `profile_signal_missing_portfolio`
- `low_confidence_job_skills`

Profile signals must not reduce score unless explicitly required by the job. In Phase 7, do not reduce score for these.

### Recommended actions

Deterministic list from missing skills/risk flags/signals. Examples:

- `Add missing required skills to your learning plan.`
- `Complete your French level.`
- `Add your GitHub profile.`
- `Complete your candidate profile.`

No LLM.

### Acceptance

- Score is deterministic.
- Score is 0-100.
- Required missing skills impact score.
- Profile signals do not reduce score.
- No OpenRouter or LLM import.

## TTA-0705 — Implement `MatchResultService`

Location:

- `apps/matching/services/match_result.py`

Contract:

```python
MatchResultService.create_match_result(user, job, cv_upload=None) -> MatchResult
MatchResultService.get_user_match(user, public_id) -> MatchResult
MatchResultService.list_user_matches(user) -> QuerySet[MatchResult]
```

Rules:

1. User must be authenticated.
2. Get `CandidateProfile` for user.
3. Verify job is visible/active using existing Phase 5 job query/search logic where possible.
4. If `cv_upload` is not supplied, use current active non-deleted CV only.
5. Call `MatchScoringService.calculate`.
6. Store `profile_snapshot_json` and `job_snapshot_json`.
7. Create `MatchResult`.
8. Record `UserEvent` with event name `match_generated`, but never let analytics failure break matching.
9. Do not own LLM explanation generation.

Snapshots must be JSON-serializable and must not include CV file path or CV text.

### Acceptance

- Authenticated user can create match.
- MatchResult is stored.
- Only owner can retrieve match.
- Another user receives 404/permission denied.
- Snapshot does not contain CV file URL/path or raw CV text.

## TTA-0706 — Implement `QuickMatchService`

Location:

- `apps/matching/services/quick_match.py`

Contract:

```python
QuickMatchService.run_quick_match(
    session_key: str,
    job: NormalizedJob,
    entered_skills: list[str],
    experience_level: str,
    french_level: str,
    ip_address: str | None = None,
) -> QuickMatchSession
```

Rules:

- Anonymous allowed.
- No CV upload.
- No account required.
- No LLM.
- Expires after 24 hours.
- Rate-limited per session/IP hash using local DB.
- Do not store raw IP or raw session key.
- Use salted SHA-256 helper based on `settings.SECRET_KEY`.
- Normalize entered skills through `SkillNormalizerService` or the same normalization logic.
- Compare entered skills to job required/optional skills.
- Create `QuickMatchSession` row.

Rate limit minimum:

- max 10 quick matches per session hash per hour
- max 20 quick matches per IP hash per hour if IP exists

If rate limit exceeded, raise a domain exception such as `QuickMatchRateLimitExceeded`.

### Acceptance

- Anonymous quick match works.
- Quick match does not require login.
- Quick match does not call LLM.
- Quick match stores no raw IP/session key.
- Quick match expires.
- Rate limit is tested.

## TTA-0707 — Create forms

Location:

- `apps/matching/forms.py`

Create `QuickMatchForm`:

Fields:

- `skills`: textarea or char field, required, max length sane limit
- `experience_level`: choices matching job/profile levels
- `french_level`: choices with blank/none/basic/intermediate/advanced/fluent

Rules:

- Split comma/newline-separated skills into clean list.
- Reject more than 30 entered skills.
- Reject skills over 80 chars each.
- No external calls.

## TTA-0708 — Create views and URLs

Location:

- `apps/matching/views.py`
- `apps/matching/urls.py`
- `apps/dashboard/urls.py` if needed

Views:

1. `CreateMatchView`
   - POST only
   - login required
   - URL: `/jobs/<uuid:public_id>/match/`
   - Gets job by job `public_id` using Phase 5 query service.
   - Calls `MatchResultService.create_match_result`.
   - Redirects to match detail.

2. `QuickMatchView`
   - POST only
   - anonymous allowed
   - URL: `/jobs/<uuid:public_id>/quick-match/`
   - Validates `QuickMatchForm`.
   - Calls `QuickMatchService.run_quick_match`.
   - Returns `templates/matching/partials/quick_match_result.html` for HTMX or normal render.

3. `MatchDetailView`
   - login required
   - URL: `/dashboard/matches/<uuid:public_id>/`
   - Owner-protected via `MatchResultService.get_user_match`.

4. `MatchHistoryView`
   - login required
   - URL: `/dashboard/matches/`
   - Lists current user's matches only.

Do not create `/dashboard/matches/<int:id>/` or `/matches/<int:id>/`.

### Acceptance

- Auth user can POST full match from job detail and gets redirected.
- Anonymous quick match works.
- Match detail is owner-protected.
- Internal IDs are not exposed in links or routes.

## TTA-0709 — Update job detail template with match actions

Update existing job detail template only.

Add:

- authenticated full match button posting to `matching:create`
- anonymous quick match form posting to `matching:quick_match`
- disabled/stub note for future recommendations/saved jobs, if already present, but do not implement them

Rules:

- Use job `public_id` only.
- Do not expose internal ID.
- Do not implement saved job/recommendation behavior.

## TTA-0710 — Create matching templates

Create:

- `templates/matching/match_detail.html`
- `templates/matching/match_history.html`
- `templates/matching/partials/quick_match_form.html`
- `templates/matching/partials/quick_match_result.html`
- optional score breakdown partial

Templates must display:

- fit score
- score label
- component scores
- strong skills
- missing required skills
- missing optional skills
- risk flags
- profile signals
- recommended actions

Do not show raw CV text.
Do not show CV file path or URL.

## TTA-0711 — Tests

Add tests for:

### Models

- `MatchResult.public_id` exists and is unique.
- `QuickMatchSession.public_id` exists and expires.
- No unique user/job constraint blocks recomputation.

### Scoring service

- Score formula returns 0-100.
- Required skills affect technical score more than optional skills.
- Missing required skills create `missing_required_skills` risk flag.
- French level missing creates `french_level_missing` risk flag.
- Profile signals do not reduce score.
- Expired job creates `job_may_be_expired`.
- No LLM imports/calls.

### MatchResultService

- Authenticated user can create stored match.
- Match stores snapshots.
- Snapshot excludes CV file path, CV URL, and raw CV text.
- Another user cannot retrieve match.
- Analytics failure does not break match creation.

### QuickMatchService

- Anonymous quick match creates session.
- Session/IP are hashed; raw values not stored.
- Quick match expires after 24 hours.
- Rate limiting works.
- No login required.
- No LLM calls.

### Views

- Full match POST route requires login.
- Full match route uses job UUID public_id.
- Quick match route works for anonymous user.
- Match detail requires owner.
- No `/jobs/<int:id>/match/` route exists.
- No `/dashboard/matches/<int:id>/` route exists.

## TTA-0712 — Acceptance command set

Run before final report:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_skills --settings=config.settings.local
python manage.py seed_job_sources --settings=config.settings.local
python manage.py ingest_job_fixtures apps/jobs/fixtures/france_travail_sample_jobs.json --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Run junk/scope check:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

Expected:

- tests pass
- no junk files
- no `task.md`
- no Phase 8 files/features
- no LLM/OpenRouter calls
- no public/internal integer ID match routes
- no CV file paths/URLs in snapshots or templates

## Stop Gate

Stop after Phase 7. Do not start recommendations/saved jobs. Phase 8 owns recommendations and saved jobs.
