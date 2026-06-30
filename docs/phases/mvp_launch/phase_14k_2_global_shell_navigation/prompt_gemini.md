# Gemini Implementation Prompt — Phase 14K-2 Global Shell, Navigation, Messages, Error/Legal Pages

You are implementing **Phase 14K-2** for TuniTech Abroad.

You must work as a strict Django/Tailwind/HTMX engineer. Follow the project architecture and the approved UI/UX package exactly. Do not improvise a new design direction.

## 0. Non-negotiable commandment

This phase is **global shell only**.

You may improve the base layout, navigation, messages/toasts, footer, privacy/terms legal styling, and branded error pages.

You must not redesign feature pages yet.

Do not start Phase 14K-3.

## 1. Preflight — stop if not clean

Before editing anything, run:

```bash
git status --short
```

Expected: clean or only the newly added Phase 14K-2 docs directory.

If Phase 14K-0 or Phase 14K-1 files are still staged/uncommitted, stop and report BLOCKED. Phase 14K-0 and Phase 14K-1 must already be committed to `dev` before this phase starts.

Also confirm these files exist:

```bash
test -f docs/design/approved_ui_ux/README_APPROVED.md
test -d docs/design/approved_ui_ux/design_vision
test -f docs/design/approved_ui_ux/static_ui_prototype/prototype-map.html
test -f docs/phases/phase_14k_2_global_shell_navigation/tasks.md
test -f docs/phases/phase_14k_2_global_shell_navigation/acceptance.md
```

## 2. Read these files first

Read in this exact order:

1. `AGENTS.md`
2. `docs/phases/phase_14k_2_global_shell_navigation/tasks.md`
3. `docs/phases/phase_14k_2_global_shell_navigation/acceptance.md`
4. `docs/design/approved_ui_ux/README_APPROVED.md`
5. `docs/design/approved_ui_ux/design_vision/00_product_ux_principles.md`
6. `docs/design/approved_ui_ux/design_vision/01_brand_and_visual_identity.md`
7. `docs/design/approved_ui_ux/design_vision/02_theme_tokens_tailwind.md`
8. `docs/design/approved_ui_ux/design_vision/03_information_architecture_and_navigation.md`
9. `docs/design/approved_ui_ux/design_vision/04_components_specification.md`
10. `docs/design/approved_ui_ux/design_vision/09_accessibility_responsive_empty_states.md`
11. `docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md`
12. `docs/design/approved_ui_ux/design_vision/11_page_by_page_final_blueprint.md`
13. `docs/design/approved_ui_ux/design_vision/12_french_ux_copy_dictionary.md`
14. `docs/design/approved_ui_ux/static_ui_prototype/prototype-map.html`
15. `docs/design/approved_ui_ux/static_ui_prototype/component-states.html`
16. `docs/design/approved_ui_ux/static_ui_prototype/404.html`
17. `docs/design/approved_ui_ux/static_ui_prototype/500.html`
18. `docs/design/approved_ui_ux/static_ui_prototype/privacy.html`
19. `docs/design/approved_ui_ux/static_ui_prototype/terms.html`

Then inspect current project files:

```bash
find templates -maxdepth 3 -type f | sort
find config apps -maxdepth 3 -name 'urls.py' -type f | sort
sed -n '1,260p' templates/base.html
sed -n '1,220p' tailwind.config.js
sed -n '1,260p' static/src/css/app.css
```

Also inspect the existing legal/privacy/terms templates by searching:

```bash
grep -R "Confidentialité\|Privacy\|Conditions\|Terms\|Données personnelles" templates -n || true
```

## 3. Allowed files

You may edit/create only:

- `templates/base.html`
- `templates/404.html`
- `templates/500.html`
- existing privacy/legal templates under `templates/`
- existing terms/legal templates under `templates/`
- small global-shell partials only if the project already has a partial convention and only if they are included by `base.html` or legal/error templates
- `docs/phases/phase_14k_2_global_shell_navigation/agent_report.md`

CSS edits are discouraged. The Phase 14K-1 design-system classes should already exist. Only edit `static/src/css/app.css` and rebuild `static/css/app.css` if a required Phase 14K-1 class is genuinely missing or broken. If you do that, justify it in the report.

## 4. Forbidden files and actions

Do not edit:

- `apps/**`
- `config/**`
- `templates/jobs/**`
- `templates/dashboard/**`
- `templates/cvs/**`
- `templates/matching/**`
- `templates/recommendations/**`
- `templates/account/**` unless a tiny wrapper compatibility fix is absolutely unavoidable; avoid it
- `requirements*.txt`
- `pyproject.toml`
- `package.json`
- `package-lock.json`
- `.env`
- `.env.*`
- migrations
- models/views/services/tasks/admin/forms/urls

Forbidden actions:

- no React, Next.js, Vue, Angular, Vite, SPA architecture
- no Tailwind CDN
- no external Google Fonts import
- no new dependency
- no provider/API calls
- no OpenRouter/LLM calls
- no France Travail live call
- no CV file URL exposure
- no raw CV text exposure
- no raw LLM request/response exposure
- no route renaming
- no public integer IDs
- no deployment work

## 5. Implementation requirements

### 5.1 Base layout

Redesign `templates/base.html` as the global shell using the approved `.tta-*` classes.

Preserve:

- `{% load %}` statements that already exist
- all current blocks and their names
- all expected static asset links
- all required allauth/auth behavior
- `csrf_token` where forms exist
- existing messages behavior, transformed visually only
- current JS/CSS inclusion logic

Add/improve:

- accessible skip link to `#main-content`
- professional top header
- branded TuniTech Abroad identity
- responsive desktop/mobile nav
- `<main id="main-content">`
- footer with useful links
- adaptive light/dark system theme using existing CSS, no manual toggle

### 5.2 Route-safe navigation

You must inspect existing URL names before writing `{% url %}` tags.

Use existing route names only. Do not invent names.

Recommended nav labels if route exists:

Public:

- `Accueil`
- `Offres IT`
- `Test CV` or `Analyse CV`
- `Comment ça marche` as `/#comment-ca-marche` if appropriate
- `Connexion`
- `Créer un compte`

Authenticated:

- `Tableau de bord`
- `Offres`
- `Recommandations`
- `CV`
- `Profil`
- `Favoris`
- `Compte`
- logout using the existing current project/allauth pattern

If a route does not exist, skip that item. Do not change URL configuration.

Do not use `/dashboard/settings/`. If account/security exists, it should remain `/dashboard/account/` or the existing named route.

### 5.3 Mobile nav and dropdown behavior

First inspect whether Alpine is already locally available in the project/base template/package.

- If Alpine is already available locally, you may use small Alpine for mobile nav and dropdowns.
- If Alpine is not already available, do not add a CDN or dependency. Use accessible `<details>`/`<summary>` or a no-JS fallback.

The mobile nav must not block normal page content when closed. It must be keyboard usable.

### 5.4 Django messages as toasts

Render messages in `base.html` using:

- `.tta-toast-container`
- `.tta-toast`
- `.tta-toast-success`
- `.tta-toast-warning`
- `.tta-toast-error`

Message mapping:

- `success` => success toast
- `warning` => warning toast
- `error` or `danger` => error toast
- any other tag => neutral/info styling using available classes

If Alpine exists, add auto-dismiss around 4 seconds and a close button. If Alpine does not exist, show non-auto-dismiss accessible messages with close omitted or no-op.

Do not expose debug context or raw exception text.

### 5.5 Footer

Footer should be professional and compact.

Include only safe, existing links:

- home
- jobs
- privacy
- terms
- account/dashboard if authenticated and route exists

Do not invent legal copy or company addresses.

### 5.6 Legal pages

Find privacy and terms templates and apply `.tta-legal` layout/readability.

Do:

- keep French copy clear
- use headings/lists/sections
- keep existing legal meaning
- use the approved legal prototype as visual reference

Do not:

- invent legal promises
- mention cookies/trackers unless already true in the app
- claim full GDPR compliance beyond what the app actually supports

### 5.7 Error pages

Create or improve:

- `templates/404.html`
- `templates/500.html`

Use approved classes:

- `.tta-error-page`
- `.tta-error-code`
- `.tta-error-title`
- `.tta-error-body`
- `.tta-btn-primary`
- `.tta-btn-secondary` where useful

404 copy should be French and professional:

- page/offre introuvable
- may have expired, moved, or been removed
- link back to home/jobs if route exists

500 copy should not leak debug details.

Do not change settings to force error rendering.

## 6. What not to touch visually yet

Do not redesign these pages in their own templates yet:

- homepage content sections
- jobs list cards/filters
- job detail content
- login/signup forms
- dashboard cards
- profile form sections
- CV management content
- recommendations
- saved jobs
- match detail/history

They may visually inherit the new shell/header/footer, but do not rewrite their page content.

## 7. Commands to run

Run all:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Run security checks:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

Important: Broad greps may show existing skill taxonomy words like React/Next/Vite or existing internal raw-field references in models/tests. That is not automatically a failure. You must report whether this phase introduced any new forbidden pattern in the diff.

## 8. Manual browser checks

If practical, run the local server and inspect:

```bash
python manage.py runserver --settings=config.settings.local
```

Check:

- `/`
- `/jobs/`
- login page
- signup page
- authenticated dashboard page if available
- privacy page
- terms page
- non-existing URL to inspect 404 behavior if practical

Check both desktop and mobile width.

Focus only on shell/nav/messages/footer/legal/error behavior.

## 9. Report

Create:

```text
docs/phases/phase_14k_2_global_shell_navigation/agent_report.md
```

Use `agent_report_template.md`.

The report must include:

- status PASS/BLOCKED/FAIL
- changed files
- whether templates were limited to allowed shell/legal/error scope
- route names used for navigation
- Alpine/no-Alpine decision
- messages/toast implementation summary
- legal pages changed
- error pages created/changed
- commands run and results
- security grep results
- manual browser check notes
- risks/notes
- confirmation Phase 14K-3 was not started

Stop after writing the report.
