# Phase 14K-10 Theme Toggle + Final Contrast Fix - Codex Report

## Final verdict

Passed. Theme control is now class-based, default light mode is preserved, a navbar toggle is available to anonymous and authenticated users, and browser screenshots show readable text across the target pages in both light and dark modes.

No commit was created.

## Exact files changed for this phase

- `tailwind.config.js`
- `templates/base.html`
- `templates/core/home.html`
- `templates/jobs/job_list.html`
- `templates/jobs/job_detail.html`
- `templates/jobs/partials/job_card.html`
- `templates/matching/partials/quick_match_result.html`
- `templates/dashboard/cv_manage.html`
- `static/src/css/app.css`
- `static/css/app.css`
- `docs/phases/phase_14k_10_theme_contrast_fix/codex_report.md`

Pre-existing uncommitted files from the prior phase were left intact and not reverted: `apps/accounts/adapters.py`, `apps/accounts/tests.py`, `templates/dashboard/home.html`, `templates/dashboard/sidebar.html`, and `docs/phases/phase_14k_9_visual_oauth_bugfix/`.

## Theme toggle implementation details

- Changed Tailwind from `darkMode: "media"` to `darkMode: "class"`.
- Added an early inline script in `templates/base.html` before CSS load:
  - Applies `.dark` only when `localStorage.getItem("tta-theme") === "dark"`.
  - Defaults to light mode when no preference exists.
  - Removes `.dark` on localStorage errors.
- Added visible theme toggle buttons in the global navbar:
  - Desktop: icon plus `Clair`/`Sombre` label.
  - Mobile: icon button.
  - Works for authenticated and anonymous nav states.
  - Persists preference to `localStorage`.
- Rebuilt `static/css/app.css` with `npm run css:build`.

## Contrast bugs fixed

- Added missing CSS custom properties used by older inline styles: `--border`, `--muted`, `--brand-*`, `--warning-*`, `--danger-*`, `--surface-sunken`, and `--text-muted`, with light and dark values.
- Made bare `.tta-badge` readable by default in both themes.
- Added explicit job card text classes:
  - `.tta-job-title`
  - `.tta-job-meta`
  - `.tta-job-desc`
  - `.tta-job-actions`
- Updated job cards and job detail badges/chips to use readable muted/border styles instead of undefined variables or unstyled badges.
- Updated job detail description, headings, sidebar test titles, optional skills, and language sections for dark-mode contrast.
- Updated quick match result partial dark-mode contrast because it can render inside the job detail page.
- Added broad card heading/strong contrast defaults for legacy cards.
- Preserved the removal of `Compatibilités` from nav/dropdown/sidebar while keeping `/dashboard/matches/` untouched.

## CV compactness

- Replaced the large no-CV empty state with a compact message above the upload form.
- Kept the upload form visible sooner.
- Preserved:
  - `method="post"`
  - `enctype="multipart/form-data"`
  - CSRF token
  - file input
  - consent field
  - validation errors
  - delete form/modal for active CV
  - HTMX CV status polling include

## Homepage whitespace

- Reduced homepage hero vertical padding.
- Further reduced vertical padding before `Offres récentes`.
- Kept search form, CTAs, chips, and recent offers section.

## Screenshots / manual browser verification notes

Used local Django server on `127.0.0.1:8010` and headless Google Chrome via DevTools protocol. Screenshots were written to `/tmp/tunitech_theme_screens/`.

Verified:

- Homepage light: `/tmp/tunitech_theme_screens/home-light.png`
- Homepage dark: `/tmp/tunitech_theme_screens/home-dark.png`
- Jobs list light: `/tmp/tunitech_theme_screens/jobs-light.png`
- Jobs list dark: `/tmp/tunitech_theme_screens/jobs-dark.png`
- CV page light: `/tmp/tunitech_theme_screens/cv-light.png`
- CV page dark: `/tmp/tunitech_theme_screens/cv-dark.png`
- Job detail light: `/tmp/tunitech_theme_screens/job-detail-light.png`
- Job detail dark: `/tmp/tunitech_theme_screens/job-detail-dark.png`
- Account dropdown over hero/card content: `/tmp/tunitech_theme_screens/dropdown-dark.png`

Observed results:

- Homepage hero title/subtitle readable in both modes.
- `Offres récentes` title/body readable in both modes.
- Jobs list title/count readable in both modes.
- Jobs filter panel labels/inputs/selects readable in both modes.
- Job cards show title, company, location, description, badges/chips, and CTA clearly in both modes.
- Job detail title, metadata, description, sidebar card, save button, and CTA readable in both modes.
- CV heading, compact no-CV message, upload form, consent block, and CTA readable in both modes.
- Account dropdown appears above hero/card content.
- Theme persistence after refresh returned `True`.

## Checks run and results

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
```

Result: passed, `System check identified no issues (0 silenced).`

```bash
python manage.py makemigrations --check --dry-run --settings=config.settings.local
```

Result: passed, `No changes detected`.

```bash
python manage.py test --settings=config.settings.local --parallel 1
```

Result: passed, `Ran 441 tests in 72.074s`, `OK`.

```bash
npm run css:build
```

Result: passed. Tailwind rebuilt `static/css/app.css`. Existing Browserslist warning appeared.

```bash
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
```

Result: passed. Dry-run reported 2 static files copied, 134 unmodified.

```bash
git diff --check
git diff --cached --check || true
```

Result: passed, no whitespace errors.

## Route smoke results

Used Django test client with `HTTP_HOST=localhost`.

- `/` -> 200
- `/jobs/` -> 200
- `/accounts/login/` -> 200
- `/accounts/signup/` -> 200
- `/dashboard/` -> 200
- `/dashboard/cv/` -> 200
- `/dashboard/recommendations/` -> 200
- `/dashboard/saved-jobs/` -> 200
- `/dashboard/account/` -> 200
- `/privacy/` -> 200
- `/terms/` -> 200
- `/jobs/6e6602df-00f6-482f-abb4-b26cd685661d/` -> 200

Note: first route-smoke helper attempt used the wrong model name (`JobPosting`) and was rerun with `NormalizedJob`. A second attempt hit a local test-user username uniqueness constraint and was rerun with a unique username. Final route smoke passed.

## Security grep classification

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
```

No hits.

```bash
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
```

Hits are expected job/skill taxonomy, fixtures, placeholders, tests, and matching/search examples. No React/Next/Vue/Angular/Vite app implementation was introduced.

```bash
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
```

No hits.

```bash
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
```

No hits.

```bash
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
```

Hits are in services, models, migrations, tests, and admin exclusions/security tests. No template exposure of CV file URLs or raw CV text was introduced.

```bash
grep -R "<int:" apps templates config -n 2>/dev/null || true
```

No hits.

```bash
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Result: `OK: no obvious secrets in diff`.

## Remaining manual checks

- Re-check in a normal interactive browser with Baha's existing logged-in account, especially if browser extensions or cached CSS are involved.
- Review the pre-existing Phase 14K-9 uncommitted files before committing this phase, because they are still present in the same worktree.

## Commit recommendation

Do not commit until Phase 14K-9 uncommitted changes are reviewed and either included intentionally or separated. Recommended eventual commit message for this phase's visual work:

```bash
git commit -m "Complete Phase 14K-10 theme toggle and contrast fix"
```
