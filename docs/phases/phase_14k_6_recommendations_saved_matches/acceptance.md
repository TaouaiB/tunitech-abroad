# Phase 14K-6 Acceptance — Recommendations, Saved Jobs, Match History, Match Detail

## Verdict required

Phase 14K-6 is accepted only if Gemini and Codex end with either:

- `PASS`, or
- `REPAIRED_PASS`

`BLOCKED` or `FAIL` means the phase is not accepted.

## Scope acceptance

Must be true:

- Only recommendation/saved-job/match-history/match-detail templates and directly used small partials were changed.
- `static/css/app.css` may change only from `npm run css:build`.
- Phase docs/reports may be added.
- No backend Python changed.
- No URLs/settings/migrations/dependencies/tests changed.
- No Phase 14K-7 or future-phase work started.

Must not be touched except for accidental rollback/repair if already polluted:

- homepage
- auth/login/signup
- public jobs pages
- dashboard home/profile/CV/account/email preferences
- admin pages
- services/models/tasks/forms/views/urls/settings

## Behavior preservation

Must be true:

- Recommendation logic is not changed.
- Saved job logic/forms/HTMX behavior are preserved.
- Matching score logic is not changed.
- Match history/detail routes continue to render.
- All changed `{% url %}` tags use existing route names.
- All object URLs use `public_id`, not internal integer IDs.
- No global `matching:quick_match` link is introduced without a job `public_id`.

## Privacy/security acceptance

Must be true:

- No CV file URL exposed.
- No raw CV text exposed.
- No raw provider request/response exposed.
- No raw LLM output exposed.
- No secrets in diff.
- No France Travail live API call from templates/views/admin.
- No OpenRouter/LLM call from templates/views/admin.
- No React/Next/Vue/Angular/Vite frontend implementation.
- No `<int:` public route introduced.

## UI/UX acceptance

Must be true:

- Recommendations page is scannable, actionable, and uses real data only.
- Saved jobs page is scannable and preserves save/unsave actions.
- Match history page has clear cards/table and empty state.
- Match detail page clearly separates:
  - score summary
  - compatibilities
  - `Compétences requises manquantes`
  - `Compétences optionnelles à renforcer`
  - `Points de vigilance`
  - next action/CTA area
- Empty states exist where no data is available.
- Pagination, if present, is accessible and preserves filters/query parameters.
- Mobile/responsive layout is reasonable by inspection.
- Dark/light adaptive design is preserved.
- French copy follows approved dictionary labels where applicable.

## Required commands

All must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

## Security grep acceptance

Run and classify:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Existing taxonomy/test/backend matches are acceptable only if classified clearly and not introduced as implementation.

## Manual review note

Automated acceptance does not replace visual review. Baha should still check desktop/mobile and light/dark rendering locally after Codex passes.
