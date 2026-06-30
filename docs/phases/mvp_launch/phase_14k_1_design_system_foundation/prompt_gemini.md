# Gemini Prompt — Phase 14K-1 Design System Foundation

You are implementing **Phase 14K-1 — Design System Foundation** for TuniTech Abroad.

This is a controlled UI foundation phase. You must follow the approved UI/UX design package exactly and must not redesign pages yet.

## 0. Non-negotiable role and stack rules

Read and obey `AGENTS.md` first.

TuniTech Abroad stack is locked:

- Django
- Django templates
- Tailwind CSS
- HTMX
- Alpine.js only for small interactions where already appropriate
- PostgreSQL / Redis / Celery remain untouched in this phase

Forbidden:

- React
- Next.js
- Angular
- Vue SPA
- FastAPI
- MongoDB
- SQLAlchemy
- SPA architecture
- new UI dependency packages
- Tailwind CDN
- Google Fonts requirement
- `django-widget-tweaks`
- `django-crispy-forms`
- `@tailwindcss/typography`

## 1. Read order

Read these files before editing anything:

```text
AGENTS.md
docs/phases/phase_14k_1_design_system_foundation/tasks.md
docs/phases/phase_14k_1_design_system_foundation/acceptance.md
docs/design/approved_ui_ux/README_APPROVED.md
docs/design/approved_ui_ux/design_vision/00_product_ux_principles.md
docs/design/approved_ui_ux/design_vision/01_brand_and_visual_identity.md
docs/design/approved_ui_ux/design_vision/02_theme_tokens_tailwind.md
docs/design/approved_ui_ux/design_vision/04_components_specification.md
docs/design/approved_ui_ux/design_vision/09_accessibility_responsive_empty_states.md
docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md
docs/design/approved_ui_ux/static_ui_prototype/component-states.html
docs/design/approved_ui_ux/static_ui_prototype/assets/prototype.css
```

Then inspect current project files:

```text
tailwind.config.js
static/src/css/app.css
static/css/app.css
package.json
```

## 2. Phase boundary

Implement **Phase 14K-1 only**.

You are allowed to modify only:

```text
tailwind.config.js
static/src/css/app.css
static/css/app.css
docs/phases/phase_14k_1_design_system_foundation/agent_report.md
```

You may modify `package-lock.json` only if the existing CSS build command changes it automatically, but you must not install packages or change dependencies.

Do **not** modify:

```text
templates/**
apps/**
config/**
requirements*.txt
pyproject.toml
package.json
.env
.env.*
```

Do **not** create Phase 14K-2 or later.

Do **not** redesign:

- base layout
- navbar
- homepage
- jobs page
- job detail
- auth pages
- dashboard
- CV page
- profile page
- recommendations
- saved jobs
- matches
- legal pages

This phase only creates the reusable design-system CSS foundation.

## 3. Implementation objective

Create the CSS/Tailwind foundation that later phases will use.

You must:

1. Update `tailwind.config.js` with adaptive system dark mode:

```js
darkMode: "media"
```

2. Preserve existing Tailwind content paths and existing config unless unsafe.
3. Extend theme tokens with the approved brand/semantic palette.
4. Add reusable `.tta-*` component classes to `static/src/css/app.css`.
5. Regenerate `static/css/app.css` using the existing build command.
6. Preserve current app behavior. Since templates are not touched, all pages should continue to work as before.

## 4. Design-source discipline

Use the approved design package as source of truth.

Important:

- The static prototype is visual/reference material.
- Do not copy large static prototype HTML into Django templates.
- Do not invent a new design language.
- Do not introduce a forced black-only theme.
- Do not add a manual theme toggle.
- Use system adaptive dark mode only.

## 5. Required CSS classes

Implement source CSS classes for the component families below. Use the approved Tailwind values from the design docs wherever possible.

### 5.1 Layout and surfaces

```text
.tta-page
.tta-section
.tta-container
.tta-surface
.tta-surface-muted
.tta-card
.tta-card-hover
.tta-card-compact
.tta-panel
.tta-divider
```

### 5.2 Buttons

```text
.tta-btn
.tta-btn-primary
.tta-btn-secondary
.tta-btn-ghost
.tta-btn-danger
.tta-btn-outline
.tta-btn-sm
.tta-btn-lg
```

Button requirements:

- accessible `focus-visible` ring
- disabled state
- active/touch press feedback: `active:scale-[0.97]`
- transition that does not feel slow
- light/dark variants

### 5.3 Cards

```text
.tta-job-card
.tta-recommendation-card
.tta-dashboard-card
.tta-auth-card
.tta-stat-card
```

Card hover requirements:

- stronger visible hover than old MVP
- `hover:-translate-y-1`
- stronger shadow
- brand border on hover
- subtle mobile active state: `active:scale-[0.99]`

### 5.4 Badges, chips, score labels

```text
.tta-badge
.tta-badge-brand
.tta-badge-success
.tta-badge-warning
.tta-badge-danger
.tta-badge-muted
.tta-badge-info
.tta-skill-chip
.tta-skill-chip-required
.tta-skill-chip-optional
.tta-score-strong
.tta-score-good
.tta-score-partial
.tta-score-weak
```

Semantic color mapping:

- strong/success: emerald
- partial/warning: amber
- weak/danger: rose
- primary: brand blue/cyan
- neutral: slate/zinc

### 5.5 Forms

```text
.tta-form-group
.tta-label
.tta-input
.tta-select
.tta-textarea
.tta-checkbox
.tta-help-text
.tta-error-text
.tta-field-error
.tta-form-section
.tta-form-grid
.tta-sticky-save-bar
```

Form requirements:

- dark mode safe
- clear focus state
- error state
- no new form-rendering dependency
- no backend form changes

### 5.6 Drawer and dropdown helpers

```text
.tta-drawer-backdrop
.tta-drawer-panel
.tta-dropdown-menu
.tta-dropdown-item
```

Only CSS classes. Do not add drawer/dropdown markup to templates in this phase.

### 5.7 Progress, score ring helpers

```text
.tta-progress
.tta-progress-bar
.tta-score-ring
.tta-score-ring-sm
.tta-score-ring-md
.tta-score-label
.tta-score-caption
```

No chart libraries.

### 5.8 Toasts/messages

```text
.tta-toast-container
.tta-toast
.tta-toast-success
.tta-toast-warning
.tta-toast-error
.tta-toast-info
```

Only CSS classes. Do not change `base.html` messages yet.

### 5.9 Skeletons/loading

```text
.tta-skeleton
.tta-skeleton-line
.tta-skeleton-line-short
.tta-skeleton-badge
.tta-skeleton-card
```

Use `animate-pulse` and light/dark safe surfaces.

### 5.10 CV dropzone

```text
.tta-dropzone
.tta-dropzone-active
.tta-dropzone-error
```

### 5.11 Pagination

```text
.tta-pagination
.tta-pagination-link
.tta-pagination-current
.tta-pagination-disabled
```

### 5.12 Empty states

```text
.tta-empty
.tta-empty-icon
.tta-empty-title
.tta-empty-body
.tta-empty-actions
```

### 5.13 Legal/error pages

```text
.tta-legal
.tta-error-page
.tta-error-code
.tta-error-title
.tta-error-body
```

Add custom legal content styling without installing `@tailwindcss/typography`.

### 5.14 Alpine cloak utility

Add:

```css
[x-cloak] { display: none !important; }
```

## 6. Tailwind build considerations

Make sure the source CSS compiles.

If custom `.tta-*` classes in `@layer components` are not visible in compiled output until used, that is acceptable as long as:

- source CSS is correct
- templates in later phases will use the classes
- `npm run css:build` succeeds

Do not add random temporary templates just to force class generation.

## 7. Checks to run

Run these commands from project root:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Also run, if reasonable:

```bash
python manage.py test --settings=config.settings.local --parallel 1
```

If full tests are too slow, explain why in the report.

Run security/architecture greps:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|client.chat\|_make_request" apps/*/admin.py apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|raw_request_json\|raw_response_text\|raw_response_json" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
```

## 8. Final report

Create:

```text
docs/phases/phase_14k_1_design_system_foundation/agent_report.md
```

Use the template in `agent_report_template.md`.

Your report must include:

- status: PASS/BLOCKED/FAIL
- files changed
- exact commands run
- CSS build result
- Django check result
- whether full tests ran
- confirmation no templates/app code changed
- confirmation no dependencies added
- risks or notes

## 9. Stop condition

Stop after Phase 14K-1.

Do not continue to Phase 14K-2.

Do not start page redesign.
