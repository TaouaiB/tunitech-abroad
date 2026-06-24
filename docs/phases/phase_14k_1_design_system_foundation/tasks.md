# Phase 14K-1 — Design System Foundation

## Status

Ready for Gemini implementation after Phase 14K-0 has been committed to `dev`.

## Phase goal

Create the reusable Tailwind/CSS design foundation for the approved TuniTech Abroad UI/UX redesign.

This phase is **not a page redesign phase**. It must prepare the design system only:

- Tailwind theme configuration
- system adaptive light/dark mode
- reusable `.tta-*` component classes
- reusable form/card/badge/button/progress/toast/skeleton/dropzone/error/legal classes
- compiled CSS output

Later phases will apply these classes to actual pages. This phase should make that possible without touching page templates.

## Source of truth

Gemini and Codex must use the imported approved design package:

```text
docs/design/approved_ui_ux/README_APPROVED.md
docs/design/approved_ui_ux/design_vision/02_theme_tokens_tailwind.md
docs/design/approved_ui_ux/design_vision/04_components_specification.md
docs/design/approved_ui_ux/design_vision/09_accessibility_responsive_empty_states.md
docs/design/approved_ui_ux/design_vision/10_backend_safety_and_template_guardrails.md
docs/design/approved_ui_ux/static_ui_prototype/component-states.html
docs/design/approved_ui_ux/static_ui_prototype/assets/prototype.css
```

The static prototype is a **visual reference**, not production code to copy blindly.

## Allowed files to modify

Allowed:

```text
tailwind.config.js
static/src/css/app.css
static/css/app.css
```

Allowed only if the project already requires it for CSS build metadata and the change is strictly generated/necessary:

```text
package-lock.json
```

But this phase should normally **not** modify `package.json` or install packages.

Required report files:

```text
docs/phases/phase_14k_1_design_system_foundation/agent_report.md
docs/phases/phase_14k_1_design_system_foundation/codex_report.md
```

## Forbidden files / areas

Do not modify:

```text
templates/**
apps/**
config/**
static/js/**
requirements*.txt
pyproject.toml
.env
.env.*
```

Do not create:

```text
docs/phases/phase_14k_2_*
docs/phases/phase_14k_3_*
```

Do not start global shell, homepage, jobs, dashboard, auth, CV, matching, recommendations, or legal page implementation. Those are later phases.

## Required implementation tasks

### TTA-14K1-01 — Tailwind dark mode and theme tokens

Update `tailwind.config.js` to support the approved design system.

Required:

- Set `darkMode: "media"`.
- Preserve existing content paths.
- Preserve existing plugins and project-specific config unless clearly obsolete.
- Extend, do not destructively replace, existing theme values.
- Add the approved brand palette and semantic colors if missing.
- Add approved radius/shadow/font tokens if practical and safe.
- Do not add Google Fonts.
- Do not install new Tailwind plugins.
- Do not add `@tailwindcss/typography`.

Typography decision:

- Use system font stack now.
- Do not require external Inter loading.
- Optional stack in Tailwind/config CSS may include `Inter` first as fallback only:

```css
Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

### TTA-14K1-02 — Base CSS organization

Update `static/src/css/app.css` cleanly.

Required:

- Keep existing Tailwind directives.
- Preserve any existing project CSS unless unsafe/duplicated.
- Add clear sections/comments for:
  - base tokens
  - layout helpers
  - buttons
  - cards
  - badges
  - forms
  - dropdown/drawer support
  - progress/score helpers
  - toast/messages
  - skeleton loading
  - dropzone
  - empty states
  - legal pages
  - error pages
  - accessibility helpers
- Prefer `@layer components` and `@layer utilities` where appropriate.

### TTA-14K1-03 — Component classes

Create source CSS classes for these approved components.

#### Layout / surfaces

Required classes:

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

Behavior:

- Light mode: clean off-white/slate page background, white cards, readable slate text.
- Dark mode: slate/zinc dark surfaces, not pure black everywhere.
- Support focus/hover/active states where relevant.

#### Buttons

Required classes:

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

Required behavior:

- consistent height, radius, font weight
- `focus-visible` ring
- `disabled` state
- `active:scale-[0.97]` touch feedback
- dark mode variants

#### Cards

Required classes:

```text
.tta-job-card
.tta-recommendation-card
.tta-dashboard-card
.tta-auth-card
.tta-stat-card
```

Required behavior:

- `tta-card-hover` uses stronger hover: `hover:-translate-y-1`, enhanced shadow, brand border on hover, and subtle `active:scale-[0.99]`.

#### Badges / chips

Required classes:

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

Semantic colors:

- success / strong: emerald
- warning / partial: amber
- danger / weak: rose
- primary / brand: blue/cyan brand palette
- muted: slate

#### Forms

Required classes:

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

Required behavior:

- light/dark compatible
- focus-visible ring
- invalid/error state
- sticky mobile save bar with `backdrop-blur-sm`
- no new dependency like `django-widget-tweaks` or `crispy-forms`

#### Filter drawer / dropdown support

Required classes:

```text
.tta-drawer-backdrop
.tta-drawer-panel
.tta-dropdown-menu
.tta-dropdown-item
```

Do not implement page-specific drawer markup in this phase; just provide classes.

#### Progress / score

Required classes:

```text
.tta-progress
.tta-progress-bar
.tta-score-ring
.tta-score-ring-sm
.tta-score-ring-md
.tta-score-label
.tta-score-caption
```

Required behavior:

- progress bars usable for profile completeness and score breakdown
- responsive score ring sizing: mobile `w-24 h-24`, desktop `md:w-32 md:h-32` where used later
- do not add chart libraries

#### Toast / messages

Required classes:

```text
.tta-toast-container
.tta-toast
.tta-toast-success
.tta-toast-warning
.tta-toast-error
.tta-toast-info
```

Required behavior:

- top-right fixed container for real pages
- dark mode variants
- no JS implementation required in this phase
- future base template will add Alpine auto-dismiss

#### Skeleton loading

Required classes:

```text
.tta-skeleton
.tta-skeleton-line
.tta-skeleton-line-short
.tta-skeleton-badge
.tta-skeleton-card
```

Required behavior:

- `animate-pulse`
- light/dark compatible
- suitable for job cards and recommendation cards

#### CV dropzone

Required classes:

```text
.tta-dropzone
.tta-dropzone-active
.tta-dropzone-error
```

Required behavior:

- dashed border
- hover/drag-over state via `.tta-dropzone-active`
- dark mode compatible

#### Pagination

Required classes:

```text
.tta-pagination
.tta-pagination-link
.tta-pagination-current
.tta-pagination-disabled
```

#### Empty states

Required classes:

```text
.tta-empty
.tta-empty-icon
.tta-empty-title
.tta-empty-body
.tta-empty-actions
```

#### Legal and error pages

Required classes:

```text
.tta-legal
.tta-error-page
.tta-error-code
.tta-error-title
.tta-error-body
```

Legal pages should support headings, paragraphs, lists, and links without installing typography plugin.

### TTA-14K1-04 — Accessibility helpers

Add or confirm CSS support for:

- `focus-visible` rings on buttons, links, form controls, dropdown items
- reduced motion respect if existing project has patterns
- readable contrast in light/dark
- tap target friendly button heights
- `x-cloak` support if Alpine exists in the current project

Example required utility:

```css
[x-cloak] { display: none !important; }
```

### TTA-14K1-05 — Build compiled CSS

Run the existing CSS build command and commit the generated `static/css/app.css` if the project tracks it.

Do not manually edit `static/css/app.css` directly unless the project already requires direct edits. Source of truth should be `static/src/css/app.css`.

## Testing requirements

At minimum run:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

If tests are affordable, also run:

```bash
python manage.py test --settings=config.settings.local --parallel 1
```

If full tests are too slow, explain clearly in the report and run at least relevant smoke checks.

## Security / architecture grep checks

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

Expected:

- No new forbidden stack usage.
- No new CDN Tailwind.
- No new provider calls from views/templates/admin.
- No CV file/raw-text exposure.
- No internal integer route changes.
- No secrets.

## Acceptance summary

Phase 14K-1 is accepted only if:

- Tailwind supports `darkMode: "media"`.
- Design-system CSS classes exist in source CSS.
- Compiled CSS is regenerated successfully.
- No templates/pages are redesigned yet.
- No app code changed.
- No dependencies added.
- Automated checks pass.
- Codex verification returns PASS.
