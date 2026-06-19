# Phase 14K-3 Acceptance Criteria

## Required final verdict

Accepted outcomes:

- `PASS`: no repair was needed and all checks passed.
- `REPAIRED_PASS`: one or more small in-scope issues were fixed and all checks passed.

Rejected outcomes:

- `BLOCKED`: only acceptable for real architecture/product/security/privacy/dependency/scope problems.
- `FAIL`: serious out-of-scope or forbidden implementation.

## Scope acceptance

Phase passes only if:

- Homepage/public front door templates are redesigned according to the approved design package.
- Existing auth/allauth templates in scope are redesigned or improved according to the approved design package.
- Existing form behavior, CSRF, hidden fields, allauth provider login tags, and error rendering are preserved.
- No backend views, models, services, tasks, forms, URLs, settings, migrations, dependencies, or tests are changed.
- No feature pages from future phases are redesigned.
- Phase 14K-4 is not started.

## Route acceptance

- All `{% url %}` tags resolve to existing URL names.
- No invented routes.
- No global `matching:quick_match` link without a job `public_id`.
- No `/dashboard/settings/` route added in nav or auth pages.
- No internal integer-ID public routes.

## Visual/design acceptance

- Uses `.tta-*` design-system classes from Phase 14K-1.
- Preserves Phase 14K-2 global shell.
- Homepage is search-first and France-first.
- Public copy is French and candidate-focused.
- Auth pages are polished, clear, and accessible.
- Mobile responsive layout is preserved.
- Adaptive system light/dark behavior remains intact.
- No external font/CSS/CDN dependency added.

## Privacy/security acceptance

- No CV file URL exposure.
- No raw CV text exposure.
- No raw provider payload exposure.
- No OpenRouter/LLM calls from views/templates.
- No France Travail API calls from public pages.
- No secrets printed or committed.
- No new dependency or forbidden frontend framework.

## Required commands

Run all commands from repo root:

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

All must pass.

The `Browserslist: caniuse-lite is outdated` warning is acceptable if the CSS build exits successfully.

## Required security/architecture greps

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Broad grep hits in existing skill/job/test data are not blockers if they are pre-existing and not introduced by this phase. They must be classified in the report.

## Manual/browser acceptance

At minimum, manually inspect in browser after implementation:

- `/`
- `/jobs/` only to confirm global shell still works, not to redesign jobs page
- login page
- signup page
- password reset page if present
- privacy page only to confirm Phase 14K-2 not broken
- terms page only to confirm Phase 14K-2 not broken

Check:

- desktop width
- mobile width
- light system theme
- dark system theme if easy
- keyboard focus on major CTAs and forms
- auth form errors still display

Manual checks can be performed by Gemini/Codex if browser tooling is available. If not available, they must document that the automated template/test checks passed and list what Baha should manually inspect.

## Commit acceptance

Commit only after Baha review.

Suggested commit message after PASS/REPAIRED_PASS:

```text
Complete Phase 14K-3 public front door and auth
```
