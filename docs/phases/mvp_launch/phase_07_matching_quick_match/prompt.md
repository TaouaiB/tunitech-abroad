# Phase 7 — Deterministic Matching and Quick Match — Agent Prompt

You are implementing Phase 7 for TuniTech Abroad.

Read `AGENTS.md` first. Then read this whole phase folder:

- `docs/phases/phase_07_matching_quick_match/tasks.md`
- `docs/phases/phase_07_matching_quick_match/acceptance.md`
- `docs/phases/phase_07_matching_quick_match/agent_report_template.md`

## Mission

Implement deterministic candidate/job matching and anonymous quick match.

This phase creates the core scoring authority. The final fit score must be rule-based, deterministic, and explainable. No LLM may influence the score.

## Current Product Context

TuniTech Abroad flow:

```text
Tunisian IT profile -> France IT jobs/internships -> CV/profile parsing -> job matching -> missing skill detection -> recommendations
```

Completed phases should already provide:

- accounts/auth
- CandidateProfile and ProfileSkill
- skill taxonomy and SkillNormalizerService
- local PostgreSQL jobs and NormalizedJobSkill
- public job list/detail pages
- private CV upload/parsing/profile completion

## Build Scope

Allowed:

- `apps/matching`
- matching models
- deterministic scoring services
- full match creation for authenticated users
- anonymous quick match
- match history and match detail pages
- job detail match forms/buttons
- HTMX quick match partials
- tests

Not allowed:

- recommendations
- saved jobs
- OpenRouter/LLM calls/imports
- match explanation endpoint
- email digest
- unsubscribe
- privacy/account deletion
- new CV parsing logic beyond reading existing profile/CV state
- France Travail live API calls
- React/Next/Angular/FastAPI/SQLAlchemy/MongoDB/SPA

## Architecture Rules

- Views stay thin.
- Business logic goes in `apps/matching/services/`.
- Models store data only.
- No external network calls.
- No OpenRouter import.
- Public URLs use UUID `public_id`, never integer IDs.
- Owner-protect match details.
- Quick match stores hashed session/IP only.
- Quick match must not require login.
- Match snapshots must not include raw CV text, CV file path, or CV file URL.

## Implementation Rules

1. Create `apps/matching` cleanly.
2. Add models exactly within Phase 7 scope.
3. Use existing jobs/profile/CV models as read sources only.
4. Use `SkillNormalizerService` for quick match entered skills.
5. Use `NormalizedJobSkill` for job skills.
6. Use `ProfileSkill.normalized_name` for profile skills unless the current schema has a canonical skill relation.
7. If current Phase 6 profile skill schema is raw/normalized string only, do not refactor it into a canonical FK in Phase 7.
8. Do not change old migrations unless this phase is uncommitted and it is safe.
9. Add tests before final report.
10. Do not commit, merge, or push.

## Fit Score Formula

Use:

```text
fit_score =
technical_skills_score * 0.45
+ experience_score * 0.20
+ role_title_score * 0.15
+ language_score * 0.10
+ location_score * 0.10
```

Round to nearest integer and clamp to 0..100.

Each component must be deterministic and separately stored in `MatchResult`.

## Required Final Commands

Run:

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

## Final Report

Create:

```text
docs/phases/phase_07_matching_quick_match/agent_report.md
```

Use the template. Be honest. If DB-backed tests are blocked, say so. If red diagnostics remain, say so. Do not claim completion if tests fail.
