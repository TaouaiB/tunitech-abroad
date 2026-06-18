# Security Findings Report - Phase 14I

Audit date: 2026-06-18

Scope: verification of Gemini's Phase 14I implementation plus narrowly scoped Phase 14I security fixes. No Phase 14J work, deployment work, or unrelated product features were started.

## Defects Fixed

### FIXED - Unsubscribe GET Mutated Email Preferences

Finding: `notifications:unsubscribe` called `EmailPreferenceService.unsubscribe()` for every request, including GET. That violated Phase 14I dangerous GET mutation rules.

Fix:

- `apps/notifications/views.py` now renders a confirmation page on GET and calls the unsubscribe service only on POST.
- `apps/notifications/services/preferences.py` now exposes `token_exists()` for safe GET validation without mutation.
- `templates/notifications/unsubscribe_confirm.html` adds the CSRF-protected confirmation form.
- `apps/notifications/tests.py` covers GET non-mutation and POST mutation.

Result: FIXED. Targeted tests and full test suite pass.

### FIXED - Phase 14I Test Discovery Conflict

Finding: Phase 14I added `apps/core/tests/__init__.py` while `apps/core/tests.py` already exists. That broke Django test discovery with an import conflict.

Fix:

- Removed the package marker.
- Moved Phase 14I regression coverage to `apps/core/test_14i_security.py`.

Result: FIXED. Full test discovery now runs 359 tests successfully.

## Automated Coverage Added/Verified

`apps/core/test_14i_security.py` now covers:

- anonymous users blocked from dashboard/private routes
- authenticated users allowed on own private routes
- inactive user and logout session behavior
- public pages remain public
- two-user CV status/delete IDOR
- HTMX CV status ownership
- two-user match detail IDOR
- two-user saved-job view/mutation isolation
- email-preference mutation scoped to current user
- GET does not mutate save/unsave, CV delete, match create, quick match, or account deletion
- CV pages do not expose direct private media URLs or raw CV text
- `CVUpload.objects` excludes soft-deleted CVs while `all_objects` retains internal access
- integer URL routes for jobs, matches, and CV status return 404
- views/templates do not import or reference France Travail/OpenRouter client symbols

Existing suites also cover:

- admin normal-user denial and staff access
- social connection signed-token ownership checks
- CV upload validation and private storage URL behavior
- matching owner-filtered service access
- recommendation and saved-job service boundaries
- OpenRouter client usage restricted to service/task layers

## Required Check Results

Commands run from repo root with `.venv` active:

```text
python manage.py check --settings=config.settings.local
Result: PASS - System check identified no issues.

python manage.py makemigrations --check --dry-run --settings=config.settings.local
Result: PASS - No changes detected.

python manage.py test --settings=config.settings.local --parallel 1
Result: PASS - Ran 359 tests, OK.

git diff --check
Result: PASS - no whitespace errors.
```

Additional checks run because a template changed:

```text
npm run css:build
Result: PASS - Tailwind rebuilt successfully. Non-blocking Browserslist outdated notice shown.

python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
Result: PASS - dry-run completed.
```

Infrastructure note: `docker compose up -d postgres redis` could not bind Redis on host port 6380 because that port was already occupied. PostgreSQL on 5432 and Redis on 6380 were already listening, and all PostgreSQL/Redis-backed Django checks completed successfully against `config.settings.local`.

## Security Grep Results

### Tailwind CDN

Command:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
```

Result: no matches.

Verdict: SAFE - local compiled Tailwind CSS is used.

### React/Next/Vue/Angular/Vite

Command:

```bash
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
```

Result: non-empty matches in job-search placeholders, quick-match placeholders, skill taxonomy seed data, fixtures, classifier/relevance keywords, and tests.

Verdict: SAFE - matches are technology names inside job intelligence data, CV/job fixtures, matching examples, and tests. No React, Next.js, Vue, Angular, Vite, SPA bootstrapping, `createRoot`, or frontend framework runtime is used.

### France Travail Calls From Views/Templates

Command:

```bash
grep -R "FranceTravailClient\|france_travail" apps/*/views.py templates -n 2>/dev/null || true
```

Result: no matches.

Verdict: SAFE - public job search and templates do not call the live France Travail client.

### OpenRouter/LLM Calls From Views/Templates

Command:

```bash
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py templates -n 2>/dev/null || true
```

Result:

- `templates/matching/match_detail.html` reads `match.llm_explanation`.

Verdict: SAFE - the template displays stored database text only. There is no OpenRouter client import, setting read, or LLM execution in views/templates.

### CV File URL / Raw Text / Extracted Text

Command:

```bash
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
```

Result: non-empty matches in CV backend extraction/parsing services, models, migrations, admin exclusion, tests, and Phase 14I assertions.

Verdict: SAFE - user-facing templates do not render `file.url` or raw CV text. `PrivateMediaStorage.url()` raises `ValueError`; tests assert this. `CVParsedData.raw_text` remains backend-only. `apps/cvs/admin.py` excludes `raw_text`.

### Integer URL Patterns

Command:

```bash
grep -R "<int:" apps templates config -n 2>/dev/null || true
```

Result: no matches.

Verdict: SAFE - user-facing routes for jobs, matches, and CV status use UUID `public_id`.

### Secret Diff Grep

Command:

```bash
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

Result: `OK: no obvious secrets in diff`

Verdict: SAFE - no obvious secrets appear in the current diff.

## Remaining Risks / Manual Steps

- Baha must complete `docs/phases/phase_14i_security_access_control_audit/manual_browser_security_signoff.md` in Chrome/admin.
- Admin list/detail screens still require human review for sensitive data exposure before final acceptance.
- OAuth/allauth flows still require browser review.

## Final Verdict

`FINAL_VERDICT: BLOCKED_HUMAN_SECURITY_SIGNOFF`

Reason: all automated checks passed after Phase 14I fixes, but the phase explicitly forbids PASS until Baha completes documented human Chrome/admin security signoff.
