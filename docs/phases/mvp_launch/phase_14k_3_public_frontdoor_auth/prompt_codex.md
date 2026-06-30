# Codex Verify + Repair Prompt — Phase 14K-3 Public Front Door and Auth

You are Codex acting as senior verifier AND repair agent for TuniTech Abroad.

You must verify Phase 14K-3 and fix any small in-scope issues yourself.

## Operating mode: verify + repair + enhance-within-scope + test loop

You are not verification-only.

Use this loop:

```text
inspect → verify → fix in-scope issues → improve only within approved design docs → test → re-check → repeat until PASS/REPAIRED_PASS
```

Do not block for:

- staged vs unstaged files
- mixed docs and implementation
- missing report file you can create
- trailing whitespace you can clean
- generated `static/css/app.css` changing after `npm run css:build`
- small copy/test mismatch you can safely fix
- small template route issue you can safely remove or redirect to an existing route

Block only if:

- the fix requires a new backend route/view/model/service/form/settings change
- the fix requires a new dependency
- the fix requires a product decision
- the fix risks CV privacy/security/secrets/internal IDs
- forbidden stack or architecture appears
- the implementation has broad out-of-scope changes
- tests still fail after reasonable in-scope repair

Do not commit.

## Read first

Read:

- `AGENTS.md`
- `docs/phases/phase_14k_3_public_frontdoor_auth/tasks.md`
- `docs/phases/phase_14k_3_public_frontdoor_auth/acceptance.md`
- `docs/phases/phase_14k_3_public_frontdoor_auth/agent_report.md` if present
- `docs/design/approved_ui_ux/README_APPROVED.md`
- `docs/design/approved_ui_ux/design_vision/03_information_architecture_and_navigation.md`
- `docs/design/approved_ui_ux/design_vision/04_components_specification.md`
- `docs/design/approved_ui_ux/design_vision/05_page_specs_public.md`
- `docs/design/approved_ui_ux/design_vision/08_forms_auth_cv_profile_spec.md`
- `docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md`
- `docs/design/approved_ui_ux/design_vision/12_french_ux_copy_dictionary.md`
- `docs/design/approved_ui_ux/static_ui_prototype/index.html`
- `docs/design/approved_ui_ux/static_ui_prototype/login.html`
- `docs/design/approved_ui_ux/static_ui_prototype/signup.html`

Then inspect current changed files:

```bash
git status --short
git diff --stat
git diff --name-only
```

Staging state is not a blocker. Use it only to understand what changed.

## Verification targets

Check that Phase 14K-3:

1. Redesigns the homepage/public front door only within approved design docs.
2. Redesigns/improves existing auth/allauth templates only within approved design docs.
3. Does not touch future feature pages: jobs list/detail, dashboard, profile, CV management, recommendations, matching.
4. Preserves allauth/CSRF/form behavior.
5. Uses only existing routes.
6. Does not use global `matching:quick_match` without `public_id`.
7. Does not invent `/cv-checker/` if no current route exists.
8. Does not add dependencies, views, routes, models, services, forms, settings, or tests.
9. Uses `.tta-*` design-system classes where appropriate.
10. Preserves adaptive light/dark and mobile responsiveness.

## Allowed repairs

You may directly repair these if found:

- Invalid `{% url %}` tag using a non-existing route or missing required argument.
- Small auth template issue that breaks allauth rendering.
- Missing `{% csrf_token %}`.
- Missing hidden redirect field if previously present.
- Broken form error rendering.
- Small copy/test mismatch.
- Trailing whitespace.
- Generated CSS mismatch after `npm run css:build`.
- Minor accessibility issue in changed templates.
- Missing report file.

Stay inside these file types/areas:

- existing public/home templates
- existing account/allauth/socialaccount templates
- `static/css/app.css` if generated
- `docs/phases/phase_14k_3_public_frontdoor_auth/codex_report.md`

Do not edit Python app code, URLs, settings, tests, migrations, dependencies, or future feature templates.

## Required commands

Run:

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

Then run:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

If a command fails, repair if safely in scope and rerun.

## Manual/browser check

If browser access is available, manually inspect:

- `/`
- login
- signup
- password reset if present
- `/jobs/` only to confirm global shell still renders, not to redesign it

If browser access is not available, state that and rely on template/tests/checks.

## Final report

Create/update:

`docs/phases/phase_14k_3_public_frontdoor_auth/codex_report.md`

Use:

`docs/phases/phase_14k_3_public_frontdoor_auth/codex_report_template.md`

Final verdict rules:

- `PASS`: no repair needed and all checks pass.
- `REPAIRED_PASS`: you fixed in-scope issues and all checks pass.
- `BLOCKED`: only real scope/product/security/dependency/architecture blocker remains.
- `FAIL`: serious forbidden/out-of-scope implementation.

Report must include:

- exact files changed by Codex
- command results
- route safety classification
- allauth/form behavior classification
- security grep classification
- whether any repairs were made
- final commit recommendation

Do not commit.
