# Phase 14K-13 Final Cards, Headers, Saved Jobs Polish - Codex Report

## Final verdict

Pass. The Phase 14K-13 fixes were implemented without model, migration, deployment, scoring formula, recommendation generation formula, ingestion, LLM, CV parsing, OAuth, or email changes.

The worktree already contained uncommitted Phase 14K-9/10/11/12 changes before this pass. I did not reset or revert them.

## Files changed for this phase

- `apps/recommendations/services/query.py`
- `apps/recommendations/tests/test_integration.py`
- `apps/recommendations/tests/test_services.py`
- `apps/jobs/tests/test_views.py`
- `templates/recommendations/partials/recommendation_card.html`
- `templates/jobs/partials/job_card.html`
- `templates/dashboard/saved_jobs.html`
- `templates/dashboard/cv_manage.html`
- `templates/dashboard/profile.html`
- `templates/dashboard/account.html`
- `static/src/css/app.css`
- `static/css/app.css`
- `docs/phases/phase_14k_13_final_cards_headers_polish/codex_report.md`

## Manual QA bugs and fixes

1. Recommendations default order
   - `RecommendationQueryService` now fetches active/stale recommendations through one ordering helper.
   - If ranks are meaningful, it sorts by `rank` ascending, then `fit_score`, `ranking_score`, and freshness.
   - If ranks are duplicated/missing and therefore not meaningful, it falls back to strongest first by `fit_score` descending, then `ranking_score` descending, then freshness.
   - No score formula or recommendation generation formula was changed.

2. Placeholder and garbage metadata
   - Job, saved-job, and recommendation cards suppress placeholder metadata at render time.
   - Suppressed values include empty values, the existing placeholder token assembled safely in templates, and one-character garbage such as `t`.
   - Missing company/location/source metadata is hidden instead of rendered as weak placeholder copy.
   - Description falls back to `Description disponible sur la source de l'offre.` only when the source description is unusable.

3. Public job cards
   - Cards are more compact when data is missing.
   - Title and main content link to `/jobs/<job.public_id>/`.
   - Metadata row is limited to clean company, location/city, source, and visible date.
   - Badges render only when useful.
   - Description is shorter and skills are shown as clean chips.
   - CTA row remains aligned and keeps the existing public job behavior.

4. Saved job cards
   - Saved cards now follow the same card pattern as public jobs.
   - No placeholder or one-letter metadata is rendered.
   - Date is visible when available.
   - The card/title links to job detail by UUID public id.
   - Existing unsave/remove behavior is preserved through `jobs/partials/save_button.html`.

5. Recommendation cards
   - Large score ring retained.
   - `Voir la compatibilité` links to `/dashboard/matches/<match_public_id>/` only when an owned match exists.
   - `Voir l'offre` links to `/jobs/<job_public_id>/`.
   - Strong skills remain green; missing skills remain red.
   - Placeholder and garbage metadata is suppressed.
   - Job date is visible where available.

6. Dashboard page headers
   - Added `.tta-page-header`, `.tta-page-kicker`, and `.tta-back-link`.
   - Applied to `/dashboard/cv/`, `/dashboard/profile/`, and `/dashboard/account/`.
   - Back link is now on its own neutral row.
   - Kicker and title are separate, compact, and no longer visually mixed.
   - Kicker text remains mixed case for `Mon CV` and `Profil`.

7. Dashboard greeting
   - Preserved existing order: profile full name, then user full name, then email.
   - Existing tests still pass.

8. Account copy
   - Professional copy remains: `Suppression du compte`, `Action irréversible`, `Supprimer définitivement mon compte`.
   - `Zone Dangereuse` remains absent.

## Tests added or updated

- `apps/recommendations/tests/test_services.py`
  - Added coverage for meaningful rank ordering.
  - Added coverage for fallback strongest-first ordering when ranks are tied.
- `apps/recommendations/tests/test_integration.py`
  - Added/kept card coverage for no placeholders, score ring, match CTA, job CTA, date, and skill colors.
  - Added page-order test proving strongest recommendation appears first when ranks are tied.
  - Added saved-job placeholder/garbage suppression coverage.
- `apps/jobs/tests/test_views.py`
  - Extended public job-card coverage to suppress placeholders and one-letter garbage while preserving date and UUID links.

## Required check results

```text
python manage.py check --settings=config.settings.local
System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
No changes detected

python manage.py test --settings=config.settings.local --parallel 1
Ran 452 tests in 68.680s
OK

npm run css:build
Done in 797ms / 798ms after final CSS adjustment
Browserslist warning only: caniuse-lite is outdated

python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
2 static files copied to staticfiles, 134 unmodified.

git diff --check
clean

git diff --cached --check || true
clean
```

## Route smoke results

Executed with Django test client and `HTTP_HOST=localhost`.

```text
/: / -> 200
/jobs/: /jobs/ -> 200
job detail: /jobs/a90a9e49-7096-4296-86b4-4c855a0428ec/ -> 200
/dashboard/: /dashboard/ -> 200
/dashboard/cv/: /dashboard/cv/ -> 200
/dashboard/profile/: /dashboard/profile/ -> 200
/dashboard/recommendations/: /dashboard/recommendations/ -> 200
/dashboard/saved-jobs/: /dashboard/saved-jobs/ -> 200
/dashboard/account/: /dashboard/account/ -> 200
match detail: /dashboard/matches/8935ce95-11c5-4a3a-ab79-d7b120fade3b/ -> 200
```

## Privacy and security grep classification

```text
grep -R "Unknown\|unknown" templates/recommendations templates/jobs templates/dashboard -n
clean

grep -R "<int:" apps templates config -n
clean

git diff secret scan
OK: no obvious secrets in diff
```

The broader raw-field grep returned references in models, services, admin exclusions, migrations, and tests. No template exposure of CV file URLs, raw CV text, provider payloads, or internal integer IDs was introduced.

## Manual browser verification notes

Used local Django server on `127.0.0.1:8001` and Google Chrome headless with a temporary authenticated session. Temporary browser data was cleaned afterward.

- `/dashboard/recommendations/`
  - Strongest recommendation (`92%`) rendered before weaker recommendation (`63%`).
  - No placeholder text in rendered body.
  - Large score rings visible.
  - Date visible.
  - Strong skills green and missing skills red.
  - Compatibility CTA links to match detail when an owned match exists.
  - Job CTA/title links to public job detail.
- `/jobs/`
  - Compact card layout rendered.
  - No placeholder text in rendered body.
  - Date visible.
  - Card/title links to public job detail.
  - Light and dark screenshots render readable cards.
- `/dashboard/saved-jobs/`
  - No placeholder text in rendered body.
  - Date visible.
  - Card/job link goes to public job detail.
  - Remove/unsave button present.
- `/dashboard/cv/`
  - Back link is separate from kicker and title.
  - Kicker renders as `Mon CV`.
- `/dashboard/profile/`
  - Back link is separate from kicker and title.
  - Kicker renders as `Profil`.
  - Skills section remains visible.
  - Save button remains visible.
- `/dashboard/`
  - Greeting rendered with profile full name: `Bonjour, Amina Browser !`.
- `/dashboard/account/`
  - Professional deletion copy rendered.
  - `Zone Dangereuse` absent.

Screenshots captured under `/tmp/tta-14k13-*.png` during verification.

## Remaining manual checks

- Baha should do one final visual pass in an interactive browser with real local data, especially mobile viewport scrolling and save/unsave clicks.
- Browser automation used Chrome headless via DevTools, not Playwright/Selenium, because no browser automation dependency exists in the project and no new dependency was added.

## Commit recommendation

Do not commit automatically. After Baha reviews the existing dirty Phase 14K-9/10/11/12 worktree plus this Phase 14K-13 pass, commit from `dev` with a phase-scoped message such as:

```bash
git commit -m "Complete Phase 14K-13 final cards and headers polish"
```
