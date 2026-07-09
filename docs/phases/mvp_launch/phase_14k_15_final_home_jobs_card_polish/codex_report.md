# Phase 14K-15 Codex Report - Final Home Jobs Card Polish

## Final Verdict

Passed. The authenticated homepage CTA bug is fixed, `/jobs/` no longer says "base locale", public job cards are closer to the approved compact premium prototype direction, and card dates now use a reusable blue `.tta-card-date` class.

No commit was made.

## Exact Files Changed In This Phase

- `templates/core/home.html`
- `templates/jobs/job_list.html`
- `templates/jobs/partials/job_card.html`
- `static/src/css/app.css`
- `static/css/app.css`
- `apps/core/test_home_cta.py`
- `apps/jobs/tests/test_views.py`
- `docs/phases/phase_14k_15_final_home_jobs_card_polish/codex_report.md`

The worktree also contains pre-existing uncommitted Phase 14K files. They were not reset or reverted.

## Authenticated Homepage CTA Fix

- Anonymous users still see `Créer un compte`.
- Authenticated users now see:
  - `Aller au tableau de bord`
  - `Voir mes recommandations`
  - `Gérer mon CV`
- Authenticated homepage copy no longer tells the user to create an account.

## Jobs Copy Fix

- Replaced `/jobs/` header copy:
  - Removed: `recherche depuis la base locale`
  - Added: `Offres IT françaises actualisées`
- Replaced homepage recent jobs copy:
  - Removed mention of `base locale`
  - Added short professional copy about updated French IT offers.

## Jobs Card Design Changes

- Reordered public `/jobs/` cards to lead with the job title.
- Kept metadata together in one row: company, location/city, source, blue date.
- Moved useful badges below the description/skills so the card reads less plain and less noisy.
- Preserved UUID detail links through `{% url 'jobs:detail' job.public_id %}`.
- Preserved existing action area behavior.
- Kept placeholder filtering for `Unknown`, `unknown`, one-letter garbage such as `t`, and weak descriptions.

## Date Color Changes

- `.tta-card-date` now uses:
  - light mode: `text-blue-700`
  - dark mode: `text-blue-300`
  - stronger weight via `font-black`
- Public jobs, saved jobs, and recommendation cards already use `tta-card-date`.
- Recommendation card structure was not redesigned.

## Tests Added Or Updated

- Added `apps/core/test_home_cta.py`
  - anonymous homepage contains `Créer un compte`
  - anonymous homepage does not show authenticated dashboard CTAs
  - authenticated homepage does not contain `Créer un compte`
  - authenticated homepage does not say `créez un compte`
  - authenticated homepage contains logged-in CTAs
- Updated `apps/jobs/tests/test_views.py`
  - `/jobs/` does not contain `recherche depuis la base locale`
  - `/jobs/` contains `Offres IT françaises actualisées`
  - public job card renders `tta-card-date`

## Required Check Results

```text
source .venv/bin/activate
python manage.py check --settings=config.settings.local
Result: PASS - System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
Result: PASS - No changes detected.

python manage.py test --settings=config.settings.local --parallel 1
Result: PASS - Ran 459 tests in 69.235s, OK.

npm run css:build
Result: PASS - CSS rebuilt. Existing Browserslist freshness warning only.

python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
Result: PASS - 2 static files copied in dry run, 134 unmodified.

git diff --check
Result: PASS.

git diff --cached --check || true
Result: PASS / no cached diff issues.
```

## Route Smoke Results

Run with Django test client and `HTTP_HOST=localhost`.

```text
/ 200
/jobs/ 200
/jobs/76a28eb2-a0bf-4238-b1ba-9702d9484696/ 200
/dashboard/ 200
/dashboard/recommendations/ 200
/dashboard/saved-jobs/ 200
/dashboard/cv/ 200
```

## Grep And Security Classification

```text
grep -R "recherche depuis la base locale\|base locale" templates -n
Result: PASS - no output.

grep -R "Unknown\|unknown" templates/recommendations templates/jobs templates/dashboard -n
Result: PASS - no output.

grep -R "<int:" apps templates config -n
Result: PASS - no output.

git diff secrets grep
Result: PASS - OK: no obvious secrets in diff.
```

The required sensitive-field grep returned existing code/test/model/admin references to `raw_text`, `raw_request_json`, `raw_response_text`, `raw_response_json`, and related security tests. Classification: expected non-template implementation and test references, not a new UI exposure from this phase.

## Manual Browser Verification Notes

- `/jobs/` cards now read closer to the approved prototype direction: clearer title-first hierarchy, metadata row, concise body, skill chips, and aligned actions.
- Dates are blue and visible through the shared `.tta-card-date` class.
- `/jobs/` no longer says "base locale".
- Authenticated homepage no longer shows the final `Créer un compte` CTA or the `créez un compte` final CTA copy.
- Recommendation cards were preserved; only the shared date color class affects their date color.

## Commit Recommendation

Do not commit yet if the broader Phase 14K dirty worktree still needs review. When ready, commit this phase together with the approved Phase 14K UI polish changes, after a final browser pass by Baha.
