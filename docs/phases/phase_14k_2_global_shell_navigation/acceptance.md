# Acceptance Criteria — Phase 14K-2 Global Shell, Navigation, Messages, Error/Legal Pages

Phase 14K-2 is accepted only if all criteria below pass.

## 1. Scope acceptance

Changed files must be limited to:

- `templates/base.html`
- `templates/404.html`
- `templates/500.html`
- existing privacy/legal templates under `templates/`
- existing terms/legal templates under `templates/`
- optional small shell/legal/error partials under `templates/` if clearly justified
- `docs/phases/phase_14k_2_global_shell_navigation/agent_report.md`
- `docs/phases/phase_14k_2_global_shell_navigation/codex_report.md`

CSS changes are accepted only if very small, justified, and limited to:

- `static/src/css/app.css`
- `static/css/app.css`

Forbidden changed files:

- `apps/**`
- `config/**`
- feature page templates outside shell/legal/error scope
- `requirements*.txt`
- `pyproject.toml`
- `package.json`
- `package-lock.json`
- `.env` / `.env.*`
- migrations

## 2. Design acceptance

- Uses approved `.tta-*` design system from Phase 14K-1.
- Uses adaptive system light/dark mode; no manual theme toggle added.
- No Tailwind CDN.
- No Google Fonts external import.
- No new frontend framework.
- No new dependency.
- Global shell is professional, responsive, and consistent with approved prototype.
- Feature page content is not redesigned yet.

## 3. Navigation acceptance

- Public/anonymous nav works.
- Authenticated nav works.
- Mobile nav works or has accessible fallback.
- User/account/logout area preserves existing auth behavior.
- No invented URL names.
- No route renames.
- No `/dashboard/settings/` introduced.
- No internal integer IDs introduced in public URLs.

## 4. Message/toast acceptance

- Django messages render through branded toast UI.
- success/warning/error/default states are mapped safely.
- No debug/raw data exposed.
- If auto-dismiss is implemented, it uses existing local Alpine or existing local JS only.
- If no JS is available, messages remain visible and accessible.

## 5. Legal/error acceptance

- Privacy and terms pages use `.tta-legal` styling.
- Legal pages preserve existing meaning and avoid fake legal promises.
- `templates/404.html` exists and is branded.
- `templates/500.html` exists and is branded.
- 500 page does not leak debug details.

## 6. Architecture/security acceptance

- No app code changed.
- No views/services/models/tasks/admin/forms/urls changed.
- No provider/API calls added.
- No OpenRouter/LLM calls in views/templates.
- No France Travail live API calls from public pages.
- No CV file URL exposure.
- No raw CV text exposure.
- No raw LLM request/response exposure.

## 7. Required commands

All must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

## 8. Required security greps

Run:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Broad grep hits from existing domain data/tests/internal model fields must be explained. New forbidden hits from this phase are blocking.

## 9. Manual browser acceptance

Manual checks should verify:

- `/` loads with new shell.
- `/jobs/` loads with new shell and old page content still works.
- login/signup pages still load.
- dashboard page still loads when authenticated.
- privacy page readable.
- terms page readable.
- 404 and 500 templates exist and are structurally safe.
- mobile width nav usable.
- dark/light system mode is acceptable.

## 10. Stop acceptance

- Phase 14K-3 was not started.
- Homepage/auth/jobs/dashboard/CV/recommendations/matching page redesigns were not started.
