# Phase 7 — Deterministic Matching and Quick Match — Acceptance Criteria

## Required Result

Phase 7 is accepted only when deterministic matching works end-to-end and no Phase 8+ behavior is implemented.

## Functional Acceptance

### Matching app

- `apps.matching` exists and is registered.
- `MatchResult` exists and stores authenticated match calculations.
- `QuickMatchSession` exists and stores anonymous quick match calculations.
- All public/detail routes use UUID `public_id` only.
- No internal integer match/job routes exist.

### Deterministic scoring

- `MatchScoringService.calculate()` returns component scores and final score.
- Final score uses the required formula:

```text
technical * 0.45 + experience * 0.20 + role/title * 0.15 + language * 0.10 + location * 0.10
```

- All scores are clamped to `0..100`.
- Required skills affect technical score more than optional skills.
- Missing required skills create a risk flag.
- Missing French level creates a risk flag where relevant.
- Profile signals do not reduce score.
- No OpenRouter/LLM import or call exists.

### Authenticated full match

- Authenticated user can create a match from a job detail page.
- `MatchResult` is persisted.
- Match detail is visible only to the owner.
- Another user cannot view the match.
- Match history lists only the current user's matches.
- Snapshots exclude raw CV text, CV file path, and CV file URL.

### Anonymous quick match

- Anonymous user can run quick match from a job detail page.
- Quick match does not require login.
- Quick match stores no raw IP address and no raw session key.
- Quick match expires after 24 hours.
- Quick match is rate-limited by session/IP hash.
- Quick match does not call LLM.

### Templates/UI

- Job detail has full match action for authenticated users.
- Job detail has quick match form for anonymous users.
- Match detail shows score, component breakdown, strong skills, missing skills, risk flags, profile signals, and recommended actions.
- Quick match result shows estimated score, matched/missing skills, and signup/profile CTA.
- No saved-job or recommendation feature is implemented.

## Security and Privacy Acceptance

- No CV file path or URL appears in templates.
- No raw CV text appears in snapshots or templates.
- Match detail is owner-protected.
- Quick match stores hashed session/IP only.
- No OpenRouter key or API call exists.
- No France Travail live API call occurs in matching or quick match.

## Phase Boundary Acceptance

Must not create:

- recommendations app
- saved jobs
- recommendation models/services/tasks
- LLM match explanation endpoint
- email digest
- unsubscribe
- Phase 8+ files or features

## Required Commands

Run and pass:

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

Run and verify no output except acceptable `git status`/diff:

```bash
find . -type d -name "__pycache__" -print
find . -name "*.pyc" -print
find . -maxdepth 4 -name "task.md" -print
find . -maxdepth 3 -name "*.sqlite3" -print
find . -maxdepth 3 -name "celerybeat-schedule*" -print
git status --short
git diff --stat
```

## Review Package Requirements

After implementation and Codex verification, package for review with:

```bash
rm -f phase7_review_package.zip phase7_git_status.txt phase7_diff_stat.txt phase7_diff.patch

git status --short > phase7_git_status.txt
git diff --stat > phase7_diff_stat.txt
git diff > phase7_diff.patch

zip -r phase7_review_package.zip \
  apps/matching \
  apps/jobs \
  apps/dashboard \
  templates/matching \
  templates/jobs \
  templates/dashboard \
  config/urls.py \
  config/settings/base.py \
  docs/phases/phase_07_matching_quick_match \
  requirements \
  pyrightconfig.json \
  .vscode/settings.json \
  phase7_git_status.txt \
  phase7_diff_stat.txt \
  phase7_diff.patch \
  -x "*/__pycache__/*" \
  -x "*.pyc" \
  -x ".env" \
  -x ".venv/*" \
  -x ".git/*" \
  -x "media/*" \
  -x "private_media/*" \
  -x "staticfiles/*" \
  -x "celerybeat-schedule*"
```

Verify:

```bash
unzip -l phase7_review_package.zip | grep -E "__pycache__|\.pyc|\.env|celerybeat|task.md|\.sqlite3|private_media|media/|docs/phases/phase_07_matching_quick_match/docs/" || echo "zip clean"
```

Expected:

```text
zip clean
```
