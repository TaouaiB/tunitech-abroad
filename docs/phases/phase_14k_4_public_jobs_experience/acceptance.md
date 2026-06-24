# Acceptance — Phase 14K-4 Public Jobs Experience

## Required final verdict

Acceptable final verdicts:

- `PASS`
- `REPAIRED_PASS`

Unacceptable final verdicts:

- `BLOCKED`
- `FAIL`

`REPAIRED_PASS` is preferred over `BLOCKED` when the agent fixed small in-scope issues and all checks pass.

## Scope acceptance

The phase is accepted only if:

- Public jobs templates are polished according to the approved UI/UX package.
- No backend app code changed.
- No routes/settings changed.
- No dependencies changed.
- No tests changed unless Baha explicitly approved.
- No Phase 14K-5 work started.
- No dashboard/profile/CV/recommendations private-page redesign occurred.
- No job search/matching/scoring/ingestion/recommendation business logic changed.

## Allowed changed files

Expected changed files are limited to:

- `templates/jobs/**/*.html`
- `templates/jobs/*.html`
- directly included public job-detail quick-match visual partials under `templates/matching/partials/` only if necessary
- `static/css/app.css` if regenerated
- `docs/phases/phase_14k_4_public_jobs_experience/agent_report.md`
- `docs/phases/phase_14k_4_public_jobs_experience/codex_report.md`

Any other file must be clearly justified as a tiny in-scope repair. Backend code changes are not accepted.

## UI acceptance

Jobs list:

- Professional search-first header.
- Filters are clear on desktop.
- Mobile filters are usable.
- Existing filter names and behavior preserved.
- Existing HTMX behavior preserved where present.
- Job cards are readable and consistent with `.tta-*` design system.
- Metadata and skill chips are clean.
- Empty state exists and looks intentional.
- Pagination uses design-system styling.
- No fake metrics or fake jobs are inserted.

Job detail:

- Strong heading section.
- Clear metadata.
- Clear source/apply action.
- Skills/status states are readable.
- Save/quick-match panels preserved if they already exist.
- No invalid global `matching:quick_match` URL without `public_id`.
- No internal integer IDs exposed.

## Architecture acceptance

Must preserve:

- local PostgreSQL public job search
- UUID `public_id` links
- existing routes and URL names
- existing form field names
- existing method/action attributes
- CSRF tokens
- existing auth/permission behavior

Must avoid:

- France Travail API calls from views/templates
- OpenRouter/LLM calls from views/templates
- CV file URLs or raw CV text in templates
- raw provider payloads in templates
- React/Next/Vue/Angular/Vite implementation
- new npm/Python dependencies

## Required command acceptance

All must pass:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

Security greps must be run and classified. Existing domain/test/backend hits are acceptable only if they are not newly introduced by this phase and do not represent a public template exposure.

## Smoke acceptance

At least these must be smoke-checked:

- `/jobs/` returns a successful response.
- `/` still returns a successful response.
- login page still returns a successful response.
- if a local job exists, one job detail URL returns a successful response.

Use `HTTP_HOST='localhost'` if Django test client rejects `testserver` due `ALLOWED_HOSTS`.

## Report acceptance

The final report must include:

- PASS or REPAIRED_PASS
- exact files changed
- repairs made by the agent
- checks run and results
- route smoke results
- security grep classification
- confirmation no Phase 14K-5 work started
- final commit recommendation
