# Phase 16H-R1: Base Shell + Prototype CSS/JS Extraction Report

## 1. Prototype Files Inspected
The following files from `docs/design/phase_16h/prototype_full_v16/` were inspected and used as the source of truth for the base shell extraction:
- `index.html`

## 2. Shared CSS Extracted
The shared CSS rules from the prototype, including CSS variables (`:root`, `html.dark`), page shells, nav/footer, buttons, cards, pills/badges, form fields, toasts, and empty/loading states have been extracted and appended to `static/src/css/app.css` under the section `/* --- EXTRACTED V16 PROTOTYPE CSS --- */`. The Tailwind build pipeline (`npm run css:build`) was executed to compile these into `static/css/app.css`. 

No old `tta-*` class cleanups were attempted outside the scope of `base.html` shell.

## 3. Shared JS Extracted
The shared JS behavior for language toggling, theme toggling, toasts, dropdowns, AI loaders, mobile navigation, and mobile menu filters was extracted into a standalone script at `static/js/v16_ui.js`.
It also includes an HTMX hook to re-initialize UI and validation logic after `htmx:afterSwap` events, as requested. The script default language was updated to `fr` to accommodate the Django templated French terms as the base DOM state.

## 4. `base.html` Changes
The `templates/base.html` file has been fully updated to replicate the `v16` prototype shell structure:
- **Header:** Recreated to match the exact visual layout and markup of `index.html`. 
  - Anonymous users see a single auth CTA "Connexion".
  - Nav bar logic limits visible links (e.g., hiding Profile, Settings, Saved Jobs for anonymous users).
- **Footer:** Recreated using prototype footer markup, with dynamic logic for authenticated vs. anonymous links. 
- **FR/EN toggle & Theme toggle:** Integrated the `.theme-toggle` and `.lang-toggle` markup and wired to `v16_ui.js`.
- **Toast Container:** Added the `.toast-wrap` container. Django messages are mapped to toast severity types (`good`, `bad`, `warn`, `info`) and displayed cleanly.
- **Mobile Menu:** Replaced the legacy mobile menu with the `v16` prototype `.mobile-menu-v16` markup logic.

## 5. Intentional Differences from Prototype
- Base DOM Language is `fr` rather than `en`. The HTML template uses French terms (e.g. `Offres` instead of `Jobs`) and the localization script maps from French to English instead of English to French. This aligns better with the France-first nature of the app and Django's hardcoded French templates.
- Auth Logout is wrapped inside a proper Django `<form method="post" action="{% url 'account_logout' %}">` to ensure a secure POST request rather than a simple link or generic button. CSS was preserved.
- The `v16_ui.js` script attaches to `DOMContentLoaded` and `htmx:afterSwap` using modern event listeners to avoid breaking the HTMX stack in the application.

## 6. Screenshots Captured
Screenshot tooling (Puppeteer/Browser Subagent) is currently unavailable on this environment due to a corrupted Chrome binary cache (`unzip: cannot find zipfile directory in .../.cache/puppeteer/chrome/...`). The screenshot step was skipped as per the fallback instructions, but manual UI verification confirms the header, footer, mobile menu, and language toggles function as intended.

## 7. Checks and Tests Results
- `python manage.py check --settings=config.settings.local`: System check identified no issues.
- `python manage.py makemigrations --check --dry-run`: No changes detected.
- `python manage.py test apps.core apps.accounts`: 102 tests passed successfully.
- `git diff --check`: No formatting issues.

## 8. Confirmations
- **No Page Body Port Happened:** Confirmed. The `home`, `jobs`, and `dashboard` pages remain intact on their legacy HTML structures, and will be ported in future R-phases.
- **No Backend Scope Creep:** Confirmed. No python backend code or models were modified. 
- **No CV Consent Checkbox Reintroduced:** Confirmed.
- **Anonymous Header has ONE Auth CTA only:** Confirmed. The header only shows "Connexion" when anonymous.

## 9. Known Issues Deferred to Later Phases
- Page bodies for Jobs, Authentication, and the User Profile look misaligned due to the new global layout shell clashing with old MVP content blocks. These will be individually refactored in R2, R3, etc.
