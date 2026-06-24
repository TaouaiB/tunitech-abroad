# Acceptance — Phase 14K-7 Final UI QA and Polish Freeze

## 1. Verdict required

Accepted verdict must be one of:

- `PASS`
- `REPAIRED_PASS`

`BLOCKED` or `FAIL` means do not commit until reviewed.

## 2. Scope acceptance

Accepted only if:

- no backend Python code changed
- no URLs/settings changed
- no migrations changed
- no tests changed
- no dependencies changed
- no `.env` changed
- no Phase 14K-8 or deployment work started
- no new feature was added
- all changes are UI/template/CSS/report-only and clearly in Phase 14K-7 scope

## 3. Product acceptance

Accepted only if the UI still supports the MVP flow:

```text
Tunisian IT profile -> France IT jobs/internships -> CV/profile -> matching -> missing skills -> recommendations
```

The app must still be France-first, candidate-intelligence focused, and not a generic job board.

## 4. Route acceptance

Accepted only if:

- `/` renders
- `/jobs/` renders
- job detail uses UUID `public_id`
- dashboard pages render for authenticated users
- match detail uses UUID `public_id`
- CV status/delete uses UUID `public_id`
- no invented `/dashboard/settings/`
- no fake `/cv-checker/` route unless route already exists
- no global quick match URL without job `public_id`
- no public integer IDs in links/routes

## 5. Form/behavior acceptance

Accepted only if existing behavior is preserved:

- login/signup forms still work structurally
- job filters still submit
- save/unsave button still uses existing partial/HTMX behavior
- quick match form remains job-scoped
- profile form preserves fields/errors/CSRF
- CV upload preserves file field, consent, enctype, CSRF, Alpine/HTMX status where used
- CV delete uses safe public ID
- email preferences form preserves checkbox fields and CSRF
- match explanation display does not alter score

## 6. Privacy/security acceptance

Accepted only if:

- no secrets appear in diff
- no `.env` committed
- no CV file URL exposed
- no raw CV text exposed in templates
- no raw provider payload exposed
- no OpenRouter API keys or calls in templates/views
- no France Travail live user-search call in templates/views
- no internal integer IDs in public/private route links

## 7. Visual acceptance

Accepted only if the major pages share consistent:

- navbar/footer
- dashboard sidebar
- cards
- buttons
- badges/chips
- form fields
- empty states
- alerts/messages
- score/progress elements
- responsive grid behavior
- adaptive light/dark behavior

Minor visual imperfections are acceptable if they are not functional, privacy, or architecture issues. They should be listed for manual review.

## 8. Required command acceptance

The final report must show these commands were run and passed:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

Browserslist/caniuse-lite warnings are non-blocking.

## 9. Manual review acceptance

Agent must include a short manual review checklist for Baha:

- desktop homepage
- mobile homepage
- jobs list/detail
- dashboard home
- CV upload page
- recommendations
- match detail
- account/privacy/legal pages

Manual browser review may happen after commit, but functional checks must pass before commit.
