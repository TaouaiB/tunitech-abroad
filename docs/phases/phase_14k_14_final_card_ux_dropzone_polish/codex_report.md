# Phase 14K-14 Codex Report

## Final verdict

Pass with one environment-limited manual item. The requested recommendation ordering, card CTA simplification, date visibility, card polish, warning copy, strong/missing skill colors, and CV upload dropzone markup were implemented without model, migration, scoring formula, ingestion, LLM, OAuth, email, settings, URL config, deployment, or commit changes.

Browser automation was not available because Playwright is not installed and no new dependencies were allowed. A live-render verification pass against the running Django app validated the page HTML and UI states; the physical OS file-picker opening from a real click remains a manual browser check.

## Exact files changed

- `apps/recommendations/services/query.py`
- `apps/recommendations/tests/test_integration.py`
- `apps/recommendations/tests/test_services.py`
- `apps/jobs/tests/test_views.py`
- `apps/cvs/tests/test_views.py`
- `templates/recommendations/partials/recommendation_card.html`
- `templates/jobs/partials/job_card.html`
- `templates/dashboard/saved_jobs.html`
- `templates/dashboard/cv_manage.html`
- `templates/matching/match_detail.html`
- `static/src/css/app.css`
- `static/css/app.css`
- `docs/phases/phase_14k_14_final_card_ux_dropzone_polish/codex_report.md`

## Recommendation sorting logic

`RecommendationQueryService` now sorts dashboard recommendations by:

1. `fit_score` descending
2. `ranking_score` descending
3. newest useful job date, using `published_at`, then `first_seen_at`, then `last_seen_at`, then recommendation `computed_at`

The previous user-facing preference for meaningful `rank` was removed from `/dashboard/recommendations/`. Rank remains stored/internal and was not recalculated.

## Recommendation button rule implemented

Recommendation cards now show:

- `Voir la compatibilité` only when `RecommendationQueryService` attaches an owned existing `MatchResult.public_id`.
- `Voir l'offre` always, linked to `/jobs/<job_public_id>/`.
- Save/unsave button through the existing `jobs/partials/save_button.html`.

`Postuler sur la source` and source URLs were removed from recommendation cards. Source application remains available from job detail.

## Date display rule implemented

Public job cards, recommendation cards, and saved-job cards display:

- `Publié le ...` when `published_at` exists.
- `Vu le ...` from `first_seen_at`.
- `Vu le ...` from `last_seen_at` when rendered with no `published_at` or `first_seen_at`.
- Nothing when no date exists.

Dates use the new `tta-card-date` component class, with stronger contrast in light and dark mode.

## Job card design changes

`templates/jobs/partials/job_card.html` now uses the shared card metadata/date classes. The design keeps compact spacing, title/detail links, placeholder suppression, useful badges, concise descriptions, skill chips, and aligned actions. No separate prototype stylesheet was copied.

## Saved-job card changes

`templates/dashboard/saved_jobs.html` now uses the same visible metadata/date treatment as public job cards and keeps title/card links to job detail. Save/remove behavior still uses the existing save button partial. The source application CTA was removed from saved-job cards to keep card actions compact.

## Warning copy changes

Recommendation card missing-required-skill copy changed to:

- Section title: `À renforcer`
- Message: `Certaines compétences obligatoires ne sont pas encore dans votre profil.`

The old recommendation card wording `Points de vigilance` and `Compétences obligatoires non détectées` no longer appears in recommendation card responses. Missing required skill chips use `tta-skill-chip-missing`.

## Strong-skill colors

Recommendation card strong skills continue to use `tta-skill-chip-success`. Matching detail strong skills now use the same success chip class. Missing required skills use `tta-skill-chip-missing`.

## Dropzone click-area fix

The CV upload dropzone is now a label-associated, keyboard-focusable click target:

- The full dropzone has `for="id_file"`, `role="button"`, and `tabindex="0"`.
- Enter/Space trigger the file input.
- Drag/drop updates the same file input and dispatches `change`.
- `method="post"`, `enctype="multipart/form-data"`, CSRF, consent checkbox, validation error display, delete form, and CV status include were preserved.
- No CV file URL or raw CV text was exposed.

## Tests added/updated

- Recommendation service tests:
  - score-first ordering over rank
  - ranking-score and date tie-breakers
- Recommendation integration tests:
  - highest visible `%` first on the dashboard page
  - compatibility CTA only with an owned match
  - job detail CTA always present
  - source application CTA absent from recommendation cards
  - new `À renforcer` copy and missing-skill chip class
- Jobs view tests:
  - placeholder suppression and date class
  - `published_at` preferred
  - `last_seen_at` fallback rendered by the reused card partial
- CV view tests:
  - valid multipart upload form preserved
  - file input, associated dropzone label, keyboard role, drag/drop handler, CSRF, and consent preserved

## Required check results

```text
python manage.py check --settings=config.settings.local
System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
No changes detected

python manage.py test --settings=config.settings.local --parallel 1
Ran 457 tests in 71.383s
OK

npm run css:build
Done in 838ms
Browserslist warning only: caniuse-lite is outdated.

python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
2 static files copied to staticfiles, 134 unmodified.

git diff --check
clean

git diff --cached --check || true
clean / no cached diff
```

## Route smoke results

Final route smoke used Django test client with `HTTP_HOST=localhost` and an active smoke user:

```text
/: / -> 200
/jobs/: /jobs/ -> 200
/dashboard/: /dashboard/ -> 200
/dashboard/cv/: /dashboard/cv/ -> 200
/dashboard/profile/: /dashboard/profile/ -> 200
/dashboard/recommendations/: /dashboard/recommendations/ -> 200
/dashboard/saved-jobs/: /dashboard/saved-jobs/ -> 200
/dashboard/account/: /dashboard/account/ -> 200
/jobs/<job_public_id> (a90a9e49-7096-4296-86b4-4c855a0428ec): /jobs/a90a9e49-7096-4296-86b4-4c855a0428ec/ -> 200
```

No owned match existed for the route-smoke user during route smoke, so a route-smoke match detail URL was not included. A separate UI smoke dataset did verify match detail rendering for the `ui-smoke` user.

## Privacy/security grep classification

```text
grep -R "file.url|cv.file.url|upload.file.url|raw_text|raw_request_json|raw_response_text|raw_response_json" templates apps -n
```

Returned existing references in models, services, admin exclusions, migrations, and tests. No new template exposure of CV file URLs, raw CV text, provider payloads, secrets, or internal IDs was introduced.

```text
grep -R "<int:" apps templates config -n
```

No hits.

```text
grep -R "Unknown|unknown" templates/recommendations templates/jobs templates/dashboard -n
```

No hits.

```text
git diff -- . ':!.env' ':!.env.*' | grep -iE ...
OK: no obvious secrets in diff
```

## Manual/live verification notes

A local dev server was started on `http://127.0.0.1:8001` because port 8000 was already in use. A `ui-smoke` user with recommendations, saved job, parsed CV marker, and match detail was prepared in the local DB for verification.

Live-render verification passed:

- `/dashboard/recommendations/`: `92%` rendered before `63%`; no placeholder metadata; no source application CTA; compatibility CTA only on the matched recommendation; visible date; green strong skills; red missing skills; `À renforcer` copy present.
- `/jobs/`: job card classes and date class present; no placeholder metadata; public detail links use UUID public IDs.
- `/dashboard/saved-jobs/`: same card/date quality; no placeholder metadata; save/remove markup present.
- `/dashboard/cv/`: clean header; clickable/keyboard/drop markup present; multipart form, CSRF, consent preserved.
- `/dashboard/profile/`: clean header and skills/save content present.
- `/dashboard/account/`: professional delete-account copy present; `Zone Dangereuse` absent.
- Match detail: strong and missing skill chip classes present.

## Remaining manual checks

- Open `/dashboard/cv/` in a real browser and click empty space inside the dropzone to confirm the OS file picker opens.
- Drag a local PDF over the dropzone in a real browser and confirm the selected filename appears before submit.
- Do a final human visual pass in light and dark mode for spacing and contrast.

## Commit recommendation

Do not commit automatically. Recommended commit after human review:

```bash
git add apps/recommendations/services/query.py apps/recommendations/tests/test_integration.py apps/recommendations/tests/test_services.py apps/jobs/tests/test_views.py apps/cvs/tests/test_views.py templates/recommendations/partials/recommendation_card.html templates/jobs/partials/job_card.html templates/dashboard/saved_jobs.html templates/dashboard/cv_manage.html templates/matching/match_detail.html static/src/css/app.css static/css/app.css docs/phases/phase_14k_14_final_card_ux_dropzone_polish/codex_report.md
git commit -m "Polish final recommendation and job card UX"
```
