# Codex Final MVP Bug Audit Report - Phase 14K-8

## Final verdict

- Verdict: `PASS`
- Reason: No in-scope UI/template/CSS/HTMX/privacy bug was found. All required baseline checks passed, required route smoke passed, and security greps did not reveal a new forbidden surface.
- Repairs made: None.
- Commit performed: No.

## Exact files changed

- `docs/phases/phase_14k_8_final_mvp_bug_audit/codex_report.md`

No templates, CSS source, generated CSS, backend code, settings, URLs, dependencies, migrations, models, services, scoring logic, ingestion logic, LLM logic, or tests were changed.

## Bugs found and fixed

- No real in-scope bugs found.
- No repairs applied.
- A temporary Django smoke user was created for authenticated route checks and then deleted in the same audit session.

## Checks run and results

- `source .venv/bin/activate && python manage.py check --settings=config.settings.local`
  - Result: Passed.
  - Output: `System check identified no issues (0 silenced).`

- `source .venv/bin/activate && python manage.py makemigrations --check --dry-run --settings=config.settings.local`
  - Result: Passed.
  - Output: `No changes detected`.

- `source .venv/bin/activate && python manage.py test --settings=config.settings.local --parallel 1`
  - Result: Passed.
  - Output: `Ran 440 tests in 75.371s` / `OK`.
  - Notes: Expected negative-path test warnings appeared for 404, 405, health 503, mocked analytics, and mocked LLM/error cases.

- `npm run css:build`
  - Result: Passed.
  - Output: Tailwind rebuilt `static/css/app.css` successfully in 715ms.
  - Note: Non-blocking Browserslist warning: `caniuse-lite is outdated`.

- `source .venv/bin/activate && python manage.py collectstatic --dry-run --noinput --settings=config.settings.local`
  - Result: Passed.
  - Output: `2 static files copied ... 134 unmodified` in dry-run mode.

- `git diff --check`
  - Result: Passed.

- `git diff --cached --check || true`
  - Result: Passed.

## Route smoke results

All route smoke checks used Django test client with `HTTP_HOST=localhost`.

Public routes:

- `/` -> 200
- `/jobs/` -> 200
- `/accounts/login/` -> 200
- `/accounts/signup/` -> 200
- `/accounts/password/reset/` -> 200
- `/privacy/` -> 200
- `/terms/` -> 200

Private routes, authenticated:

- `/dashboard/` -> 200
- `/dashboard/profile/` -> 200
- `/dashboard/cv/` -> 200
- `/dashboard/recommendations/` -> 200
- `/dashboard/saved-jobs/` -> 200
- `/dashboard/matches/` -> 200
- `/dashboard/email-preferences/` -> 200
- `/dashboard/account/` -> 200

Object routes:

- Real job detail `/jobs/76a28eb2-a0bf-4238-b1ba-9702d9484696/` -> 200
- Real match detail as unrelated smoke user `/dashboard/matches/0c7d34ad-e361-4913-abdd-52d7a0ef490b/` -> 404, classified as expected owner/privacy boundary.
- Real match detail as match owner `/dashboard/matches/0c7d34ad-e361-4913-abdd-52d7a0ef490b/` -> 200

Error pages:

- Missing route `/this-url-does-not-exist-14k8/` with `DEBUG=False` -> 404, custom 404 content present.
- Direct `server_error` render for `/__500_smoke__/` with `DEBUG=False` -> 500, custom 500 content present.

## Security grep classification

- Tailwind CDN grep:
  - Command: `grep -R "cdn.tailwindcss.com" templates config static -n || true`
  - Result: Clean.

- Forbidden frontend stack grep:
  - Command: `grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true`
  - Result: No forbidden frontend framework implementation found.
  - Classification: Expected content/data/test hits only, including skill taxonomy entries, placeholder skill examples, fixture job descriptions, matching tests, and extraction tests.

- France Travail live/API usage grep:
  - Command: `grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true`
  - Result: Clean for checked admin/view/template surface.

- OpenRouter/LLM view/template usage grep:
  - Command: `grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true`
  - Result: Clean for checked admin/view/template surface.

- CV/raw/provider exposure grep:
  - Command: `grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true`
  - Result: No template exposure of CV file URLs, raw CV text, provider payloads, or secrets found.
  - Classification: Backend model/service/admin/test hits are expected storage, exclusion, and security-test code. `profile_url` hits are false positives from profile URL normalization. No fix needed.

- Internal integer route grep:
  - Command: `grep -R "<int:" apps templates config -n 2>/dev/null || true`
  - Result: Clean.

- Secrets-in-diff grep:
  - Command: `git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"`
  - Result: `OK: no obvious secrets in diff`.

## Direct template/static audit notes

- Public job links continue to use `job.public_id`.
- Save/unsave button HTMX attributes are present on the partial forms.
- Quick match form uses `job.public_id` and preserves `hx-post`, `hx-target`, and `hx-swap`.
- CV status polling uses `cv.public_id` and preserves `hx-get`, polling trigger, and `outerHTML` swap.
- Recommendation refresh partial preserves polling attributes and target.
- CV management delete hidden field uses `active_cv.public_id`.
- No `file.url`, `cv.file.url`, `upload.file.url`, or raw CV text exposure was found in templates.
- `templates/matching/match_detail.html` includes `match.job_snapshot_json.url` for the original external job URL; this is not a CV file URL and was not changed.

## Remaining manual checks

- Manual browser visual pass is still recommended for:
  - Desktop homepage
  - Mobile homepage
  - Jobs list and detail
  - Login and signup
  - Dashboard home
  - Profile and CV pages
  - Recommendations, saved jobs, match history, and match detail
  - Account, email preferences, privacy, terms, 404, and 500 pages
- Manual dark/light visual inspection was not performed in a browser during this audit.
- Manual mobile viewport inspection was not performed in a browser during this audit.

## Commit recommendation

- Commit recommendation: Commit allowed after Baha's manual browser visual spot-check.
- Suggested commit message: `Complete Phase 14K-8 final MVP bug audit`
- Do not include `.env` or any local secret files.
