# Phase 14K-12 Codex Report

## Final verdict

Pass. The recommendation cards, public job cards, CV page header, dashboard greeting, and account deletion copy were polished within the requested scope. No scoring, ranking, models, migrations, ingestion, LLM, CV parsing, URL config, settings, or deployment files were changed for this phase.

Note: the worktree already contained uncommitted Phase 14K-9/10/11 changes before this phase. Those were preserved and not reverted.

## Files changed for this phase

- `apps/dashboard/tests.py`
- `apps/dashboard/views.py`
- `apps/jobs/tests/test_views.py`
- `apps/recommendations/services/query.py`
- `apps/recommendations/tests/test_integration.py`
- `static/src/css/app.css`
- `static/css/app.css`
- `templates/dashboard/account.html`
- `templates/dashboard/cv_manage.html`
- `templates/dashboard/home.html`
- `templates/jobs/partials/job_card.html`
- `templates/recommendations/partials/recommendation_card.html`
- `docs/phases/phase_14k_12_cards_navigation_copy_polish/codex_report.md`

## Manual QA bugs and fixes

1. Recommendation cards must not show placeholder badges.
   - Fixed by hiding contract type, remote type, job type, and experience level badges when their value is missing or placeholder-like.
   - Verified no literal `Unknown` or `unknown` appears in `templates/recommendations` or `templates/jobs`.

2. Recommendation fit score must be prominent.
   - Moved the score out of the small status badge and into a large circular score ring on the recommendation card.
   - Preserved existing `fit_score`; no recalculation or scoring logic changed.

3. `Voir la compatibilité` must go to match detail.
   - `RecommendationQueryService` now attaches the newest existing owned `MatchResult.public_id` for each recommendation job.
   - The CTA links to `/dashboard/matches/<uuid>/` only when an existing match is available.
   - If no match exists, the compatibility CTA is hidden and the safe `Voir l'offre` job-detail CTA remains.

4. Job card/title should link to public job detail.
   - Public job card content area now links to `/jobs/<job.public_id>/`.
   - Recommendation card content/title area also links to `/jobs/<job.public_id>/`.
   - Existing buttons remain intact and use UUID routes.

5. Show job date on cards.
   - Public job cards and recommendation cards now show:
     - `Publié le ...` from `published_at`, else
     - `Vu le ...` from `first_seen_at`, else
     - `Vu le ...` from `last_seen_at`, else hidden.
   - No fake date is shown.

6. Color strong skills green.
   - Added `.tta-skill-chip-success` for green strong-skill chips with dark-mode styling.
   - Applied to recommendation card strong skills.
   - Matching detail already used green styling for strong skills and was left unchanged.

7. Fix CV page breadcrumb/title layout.
   - Back link is on its own compact line.
   - `Mon CV` eyebrow is a separate block.
   - `CV & Compétences extraites` remains normally aligned with no large extra spacing.

8. Dashboard greeting should use person name.
   - Dashboard view now computes `dashboard_display_name` as:
     1. `candidate_profile.full_name`
     2. `user.get_full_name()`
     3. `user.email`
   - Template uses that value instead of always using email.

9. Account page copy must be professional.
   - Replaced `Zone Dangereuse`.
   - New section title: `Suppression du compte`
   - New subtitle: `Action irréversible`
   - New button: `Supprimer définitivement mon compte`
   - Form behavior and delete-account flow were not changed.

## Tests added/updated

- Recommendation integration tests:
  - placeholder badges hidden
  - prominent score present
  - green strong-skill class present
  - missing skills still red
  - job date visible
  - match CTA uses existing `MatchResult.public_id`
  - match CTA hidden when no match exists
- Job view tests:
  - public job card hides placeholder badges
  - date label visible
  - public detail links use `public_id`
- Dashboard tests:
  - greeting uses profile full name before email
  - greeting uses account full name before email
  - account deletion copy is professional

## Required checks

```text
python manage.py check --settings=config.settings.local
System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
No changes detected

python manage.py test --settings=config.settings.local --parallel 1
Ran 448 tests in 72.147s
OK

npm run css:build
Done in 786ms
Note: Browserslist reported caniuse-lite is outdated.

python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
2 static files copied to staticfiles, 134 unmodified.

git diff --check
clean

git diff --cached --check || true
clean
```

## Route smoke results

Run with Django test client and `HTTP_HOST=localhost`.

```text
/: / -> 200
/jobs/: /jobs/ -> 200
real job detail: /jobs/76a28eb2-a0bf-4238-b1ba-9702d9484696/ -> 200
/dashboard/: /dashboard/ -> 200
/dashboard/cv/: /dashboard/cv/ -> 200
/dashboard/recommendations/: /dashboard/recommendations/ -> 200
/dashboard/saved-jobs/: /dashboard/saved-jobs/ -> 200
/dashboard/account/: /dashboard/account/ -> 200
owned match detail: /dashboard/matches/0c7d34ad-e361-4913-abdd-52d7a0ef490b/ -> 200
```

## Privacy/security grep classification

```text
grep -R "file.url|cv.file.url|upload.file.url|raw_text|raw_request_json|raw_response_text|raw_response_json" templates apps -n
```

Classification: no template exposure found. Matches are in backend services, admin exclusions, migrations, and tests.

```text
grep -R "<int:" apps templates config -n
```

Classification: no matches.

```text
grep -R "Unknown|unknown" templates/recommendations templates/jobs -n
```

Classification: no matches.

```text
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer ...|OPENROUTER_API_KEY=...|FRANCE_TRAVAIL_CLIENT_SECRET=...|EMAIL_HOST_PASSWORD=..."
OK: no obvious secrets in diff
```

## Browser verification

Local server used: `http://127.0.0.1:8001/` because port 8000 was already in use.

Created a local fake QA account/data set:

- user: `qa14k12@example.test`
- job public id: `a90a9e49-7096-4296-86b4-4c855a0428ec`
- match public id: `50dc1adb-9a03-4e3b-bfb8-a52344629426`

Rendered-page verification results:

- `/dashboard/recommendations/`: no placeholder badges, prominent `84%` score ring, green strong skills, red missing skill, job date visible, compatibility CTA opens match detail, job content opens public job detail.
- `/jobs/?q=Backend+Developer+Django+QA`: job date visible, no placeholder badges, card/title link opens public detail.
- `/dashboard/cv/`: main content renders the back link, `Mon CV` eyebrow, and title in the correct compact order. The sidebar also contains `Mon CV`, so automated string-position checks must scope to main content.
- `/dashboard/`: greeting renders `Bonjour, Amina QA !` and does not render the email greeting.
- `/dashboard/account/`: professional deletion copy renders and `Zone Dangereuse` is absent.
- Light/dark readability: score text uses `tta-score-ring-value`; strong-skill green dark styling is provided by `.tta-skill-chip-success`; missing-skill red dark styling remains on the chip utilities.

Playwright was not installed in the repo or virtualenv, and no new dependencies were added for this phase.

## Remaining risks/manual steps

- A human should still do final visual inspection in a real browser for exact spacing and subjective readability.
- The local fake QA user/data created for browser verification can be removed later if desired; it is not committed.
- Port 8000 was already occupied during verification, so the dev server was run on 8001.

## Commit recommendation

Do not commit yet. Review this Phase 14K-12 diff together with the existing uncommitted Phase 14K-9/10/11 changes, then commit from `dev` after human review.
