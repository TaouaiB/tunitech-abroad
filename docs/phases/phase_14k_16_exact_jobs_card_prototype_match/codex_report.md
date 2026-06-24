# Phase 14K-16 Codex Report - Exact Public Job Card Prototype Match

## Final Verdict

Completed. The live `/jobs/` public cards now follow the approved prototype order and layout closely enough for this phase:

`badges -> title -> metadata -> description -> skills`, with a separate right-side freshness/actions column on desktop and a single-column layout on mobile.

No commit was made.

## Files Changed In This Phase

- `templates/jobs/partials/job_card.html`
- `templates/jobs/job_list.html`
- `static/src/css/app.css`
- `static/css/app.css`
- `apps/jobs/tests/test_views.py`
- `apps/jobs/tests/test_14j_job_card_skills.py`
- `docs/phases/phase_14k_16_exact_jobs_card_prototype_match/codex_report.md`

The worktree already contained unrelated uncommitted Phase 14K changes in other files; they were not reverted or reset.

## Card Structure Confirmation

`templates/jobs/partials/job_card.html` now renders:

- `<article class="tta-job-card">`
- left column: `<div class="tta-job-main">`
- main content link to `/jobs/<job.public_id>/`
- badge row before title
- title before metadata
- metadata before description
- skills below description
- right column: `<div class="tta-job-side">`
- freshness block before actions
- actions outside the main content link

The primary CTA also links to `/jobs/<job.public_id>/`. Internal integer IDs are not used in public card links.

## Desktop Two-Column Layout

`static/src/css/app.css` defines `.tta-job-card` as a grid:

- mobile: `grid-template-columns: minmax(0, 1fr)`
- desktop `lg`: `grid-template-columns: minmax(0, 1fr) minmax(10.5rem, auto)`

`.tta-job-side` is a flex column aligned to the right on desktop with `justify-between`, placing the freshness block at the top/right and the actions at the bottom/right.

## Date Styling

Date metadata follows the requested fallback order:

- `published_at` renders as `Publié le ...`
- else `first_seen_at` renders as `Vu le ...`
- else `last_seen_at` renders as `Vu le ...`
- else no date metadata is rendered

The date uses `.tta-card-date`, styled as bold blue in light mode and readable blue in dark mode. Company, location, and source remain neutral text.

## Freshness Block Behavior

The right-side `.tta-job-freshness` block always renders on job cards:

- apprenticeship/alternance jobs show `Alternance`
- internship/stage jobs show `Stage`
- expired jobs show `Ancienne offre`
- stale jobs show `Offre à vérifier`
- jobs with `published_at` show `Nouvelle offre`
- otherwise jobs show `Offre disponible`

This is presentation-only template logic. No job freshness business logic was changed.

## Action Block Behavior

The right-side `.tta-job-actions` block contains:

- primary `Voir l'offre` link to `/jobs/<job.public_id>/`
- existing save/unsave partial rendered as the secondary action

`Postuler sur la source` is not rendered on `/jobs/` cards. The source application CTA remains a detail-page concern.

## Tests Added Or Updated

Updated job card tests cover:

- public card structure classes: `tta-job-main`, `tta-job-side`, `tta-job-freshness`, `tta-job-actions`, `tta-card-date`
- prototype HTML order: badges before title, title before metadata, metadata before description, description before skills
- actions outside the main content link
- public UUID detail links and no internal integer detail link
- placeholder suppression for `Unknown`, `unknown`, and `>t<`
- published date and seen-date fallbacks
- empty skill fallback text: `Compétences en cours d'analyse`

Recommendation card tests were not modified for layout.

## Route Smoke Results

Run with Django test client and `HTTP_HOST=localhost`:

- `/jobs/ -> 200`
- `/jobs/a90a9e49-7096-4296-86b4-4c855a0428ec/ -> 200`
- `/dashboard/recommendations/ -> 302` for anonymous user, expected login redirect
- `/dashboard/saved-jobs/ -> 302` for anonymous user, expected login redirect

## Required Check Results

- `python manage.py check --settings=config.settings.local` -> pass, no issues
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local` -> pass, no changes detected
- `python manage.py test --settings=config.settings.local --parallel 1` -> pass, 461 tests
- `npm run css:build` -> pass; existing Browserslist currency warning only
- `python manage.py collectstatic --dry-run --noinput --settings=config.settings.local` -> pass; 2 static files copied in dry run, 134 unmodified
- `git diff --check` -> pass
- `git diff --cached --check || true` -> pass/no output

## Grep And Security Classification

- `base locale` grep in templates -> no matches
- `Unknown|unknown` grep in `templates/recommendations templates/jobs templates/dashboard` -> no matches
- `<int:` grep in `apps templates config` -> no matches
- sensitive template/app grep for CV file URLs/raw provider fields -> existing backend/admin/test references only; no template exposure introduced by this phase
- secrets grep in diff -> `OK: no obvious secrets in diff`

## Manual Browser Verification Notes

Dev server used: `http://127.0.0.1:8001/` because port 8000 was already in use.

Headless Chrome screenshots:

- desktop: `/tmp/tunitech-card-check/jobs-desktop-final.png`
- mobile: `/tmp/tunitech-card-check/jobs-mobile-final.png`

Desktop visual verification:

- badges appear at the top
- title appears under badges
- metadata row appears under title
- date is blue and bold in metadata
- description appears under metadata
- skills appear under description
- separate right-side column is visible
- freshness block is at top right
- actions are at bottom right
- no `Unknown`, `unknown`, `>t<`, or `base locale` in dumped live DOM

Mobile visual verification:

- card collapses to one column
- freshness block appears below skills
- actions stack/wrap cleanly below freshness
- metadata remains readable and date wraps cleanly when needed

## Commit Recommendation

Do not commit until Baha reviews the live `/jobs/` cards. Suggested eventual commit message:

`Complete Phase 14K-16 public job card prototype match`
