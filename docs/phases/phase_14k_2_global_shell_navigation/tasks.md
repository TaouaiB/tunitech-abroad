# Phase 14K-2 — Global Shell, Navigation, Messages, Error/Legal Pages

## 1. Phase goal

Apply the approved TuniTech Abroad UI/UX design system to the global Django shell only.

This phase creates the shared visual frame that later page phases will use:

- `base.html` / main layout shell
- public and authenticated navigation
- mobile navigation
- account/user dropdown, if supported by existing project structure
- Django messages rendered as branded toasts
- footer
- branded `404.html` and `500.html`
- privacy/terms legal page styling

This is not a page-redesign phase. Do not redesign homepage, jobs, auth, dashboard, CV, profile, recommendations, or matching pages yet.

## 2. Mandatory prerequisites

Before implementation:

1. Phase 14K-0 must already be committed to `dev`.
2. Phase 14K-1 must already be committed to `dev`.
3. `git status --short` must be clean except for the new Phase 14K-2 docs directory after unzipping this package.
4. The approved design source must exist at:
   - `docs/design/approved_ui_ux/README_APPROVED.md`
   - `docs/design/approved_ui_ux/design_vision/`
   - `docs/design/approved_ui_ux/static_ui_prototype/prototype-map.html`
5. The Phase 14K-1 `.tta-*` CSS classes must already exist in `static/src/css/app.css` and compiled `static/css/app.css`.

If prerequisites are not true, stop and report BLOCKED.

## 3. Required design references

Read these before editing:

- `docs/design/approved_ui_ux/README_APPROVED.md`
- `docs/design/approved_ui_ux/design_vision/00_product_ux_principles.md`
- `docs/design/approved_ui_ux/design_vision/01_brand_and_visual_identity.md`
- `docs/design/approved_ui_ux/design_vision/02_theme_tokens_tailwind.md`
- `docs/design/approved_ui_ux/design_vision/03_information_architecture_and_navigation.md`
- `docs/design/approved_ui_ux/design_vision/04_components_specification.md`
- `docs/design/approved_ui_ux/design_vision/09_accessibility_responsive_empty_states.md`
- `docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md`
- `docs/design/approved_ui_ux/design_vision/11_page_by_page_final_blueprint.md`
- `docs/design/approved_ui_ux/design_vision/12_french_ux_copy_dictionary.md`
- `docs/design/approved_ui_ux/static_ui_prototype/prototype-map.html`
- `docs/design/approved_ui_ux/static_ui_prototype/component-states.html`
- `docs/design/approved_ui_ux/static_ui_prototype/404.html`
- `docs/design/approved_ui_ux/static_ui_prototype/500.html`
- `docs/design/approved_ui_ux/static_ui_prototype/privacy.html`
- `docs/design/approved_ui_ux/static_ui_prototype/terms.html`

The static prototype is a visual reference only. Do not copy it blindly into Django templates. Preserve Django template blocks, URL names, context variables, CSRF, allauth tags, and existing behavior.

## 4. Allowed implementation scope

Allowed to edit/create:

- `templates/base.html`
- `templates/404.html`
- `templates/500.html`
- existing privacy/legal templates, wherever they currently live under `templates/`
- existing terms/legal templates, wherever they currently live under `templates/`
- small template partials only if the project already has a clear partials convention and the partials are used only by the global shell/legal/error pages

Allowed phase docs:

- `docs/phases/phase_14k_2_global_shell_navigation/agent_report.md`

Allowed only if absolutely necessary and justified in the report:

- a tiny CSS correction in `static/src/css/app.css` and regenerated `static/css/app.css` if Phase 14K-1 missed a class required by the approved design

Strong preference: no CSS changes in this phase. Use the `.tta-*` classes already created in Phase 14K-1.

## 5. Forbidden changes

Do not edit:

- `apps/**`
- `config/**`
- `templates/jobs/**`
- `templates/dashboard/**`
- `templates/cvs/**`
- `templates/matching/**`
- `templates/recommendations/**`
- `templates/account/**` except only if the current `base.html` structure forces a harmless block wrapper update; avoid this if possible
- `requirements*.txt`
- `pyproject.toml`
- `package.json`
- `package-lock.json`
- `.env`
- `.env.*`
- migrations
- models, views, services, tasks, forms, admin, URLs

Do not start Phase 14K-3.

## 6. Required behavior

### 6.1 Base shell

The global shell must:

- use the approved adaptive light/dark design; do not add a manual theme toggle
- use existing loaded CSS only; no CDN Tailwind, no Google Fonts, no external UI dependencies
- keep a clean SaaS header with brand identity
- preserve existing Django `{% block %}` structure so all current pages still render
- preserve all existing page content blocks
- include an accessible skip link to main content
- set a clear `<main id="main-content">` region
- support anonymous and authenticated states
- keep footer links visible and professional
- not break Django admin

### 6.2 Navigation

Implement a professional nav using existing route names only.

Public/anonymous nav should prioritize:

- Accueil
- Offres IT
- Test CV or Analyse CV if the existing route exists
- `Comment ça marche` as `/#comment-ca-marche` if used
- Connexion
- Créer un compte

Authenticated nav should prioritize:

- Tableau de bord
- Offres
- Recommandations, if route exists
- CV, if route exists
- Profil, if route exists
- Favoris, if route exists
- Account/security access
- Logout using the existing project/allauth pattern

Rules:

- Do not invent URL names.
- Inspect current `urls.py` and templates before using `{% url %}`.
- If a named route does not exist, do not add that nav item.
- Do not rename routes.
- Do not add `/dashboard/settings/`; the approved route is `/dashboard/account/` if present.
- Do not use internal integer IDs in any URL.
- Use active nav styling where practical without adding backend logic.

### 6.3 Mobile navigation

Mobile nav must be usable and accessible.

Preferred approach:

- If Alpine is already locally available/loaded in the project, use small Alpine interactions for mobile nav and dropdowns.
- If Alpine is not available locally, do not add CDN or dependency. Use accessible HTML fallback such as `<details>`/`<summary>` or a minimal existing local JS pattern if already present.

Do not add a new frontend framework or CDN.

### 6.4 Django messages/toasts

Render Django messages in the base template using approved toast classes:

- `.tta-toast-container`
- `.tta-toast`
- `.tta-toast-success`
- `.tta-toast-warning`
- `.tta-toast-error`

Rules:

- Map Django message tags safely: success, warning, error/danger, info/default.
- Do not expose debug data.
- Do not require a new dependency.
- If Alpine is available, auto-dismiss after around 4 seconds and allow user dismissal.
- If Alpine is not available, show accessible toasts without auto-dismiss.
- Messages must not cover the main nav in the component demo behavior; on real pages they may use fixed top-right positioning as designed.

### 6.5 Legal pages

Apply `.tta-legal` styling to privacy and terms pages.

Rules:

- Preserve the legal meaning and existing links.
- Improve layout, headings, lists, and readability.
- Keep French copy clean.
- Do not invent unsupported privacy promises.
- Mention CV privacy only if the existing page already covers it or the text is generic and true: CV files are private and can be deleted by the user.

### 6.6 Error pages

Create or improve:

- `templates/404.html`
- `templates/500.html`

Rules:

- Use approved branded error-page classes.
- French copy.
- For 404: mention the offer/page may have expired, moved, or been removed.
- For 500: calm professional message; do not leak debug details.
- Include safe links back to home and/or jobs if routes exist.
- Do not change Django settings to force error pages.

## 7. Architecture and safety rules

- No model/view/service/task/admin changes.
- No provider calls.
- No France Travail live API call in public pages.
- No OpenRouter/LLM call in templates/views.
- No CV file URL exposure.
- No raw CV text exposure.
- No raw LLM request/response exposure.
- No React/Next/Vue/Angular/Vite.
- No Tailwind CDN.
- No Google Fonts external import.
- No new packages.
- No route renames.
- No public integer IDs.

## 8. Required commands

Run:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Run security greps from `acceptance.md`.

## 9. Required manual checks

At minimum, run the server and manually inspect:

- `/`
- `/jobs/`
- login page
- signup page
- dashboard page while authenticated, if available
- privacy page
- terms page
- a non-existing URL for 404 behavior with DEBUG disabled only if practical; otherwise confirm template exists and renders structurally

Manual checks should focus only on global shell/nav/messages/footer/legal/error behavior, not page-level redesign.

## 10. Stop condition

Stop after Phase 14K-2.

Do not begin:

- homepage redesign
- auth page redesign
- jobs page redesign
- dashboard redesign
- profile/CV redesign
- recommendations/matching redesign
- deployment
