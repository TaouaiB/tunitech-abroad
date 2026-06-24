# Acceptance — Phase 14K-1 Design System Foundation

Phase 14K-1 is accepted only when all conditions below are true.

## Scope acceptance

- [ ] Only Phase 14K-1 was implemented.
- [ ] Phase 14K-2 was not created or started.
- [ ] No page redesign happened.
- [ ] No templates were modified.
- [ ] No Django app code was modified.
- [ ] No models, migrations, views, services, tasks, URLs, forms, or settings changed.
- [ ] No dependencies were added.
- [ ] No `.env` or real secret file was touched.

Allowed implementation changes:

- [ ] `tailwind.config.js`
- [ ] `static/src/css/app.css`
- [ ] `static/css/app.css`

Allowed report changes:

- [ ] `docs/phases/phase_14k_1_design_system_foundation/agent_report.md`
- [ ] `docs/phases/phase_14k_1_design_system_foundation/codex_report.md`

## Design-system acceptance

- [ ] `tailwind.config.js` uses `darkMode: "media"`.
- [ ] Existing Tailwind content paths are preserved.
- [ ] Existing project Tailwind config is not destructively replaced.
- [ ] Brand/semantic colors are available or extended.
- [ ] System font stack is used; no external font requirement added.
- [ ] No Tailwind CDN added.
- [ ] No Tailwind plugin dependency added.

## Required CSS classes

`static/src/css/app.css` includes source definitions for these class families:

### Layout / surfaces

- [ ] `.tta-page`
- [ ] `.tta-section`
- [ ] `.tta-container`
- [ ] `.tta-surface`
- [ ] `.tta-surface-muted`
- [ ] `.tta-card`
- [ ] `.tta-card-hover`
- [ ] `.tta-card-compact`
- [ ] `.tta-panel`
- [ ] `.tta-divider`

### Buttons

- [ ] `.tta-btn`
- [ ] `.tta-btn-primary`
- [ ] `.tta-btn-secondary`
- [ ] `.tta-btn-ghost`
- [ ] `.tta-btn-danger`
- [ ] `.tta-btn-outline`
- [ ] `.tta-btn-sm`
- [ ] `.tta-btn-lg`

### Cards

- [ ] `.tta-job-card`
- [ ] `.tta-recommendation-card`
- [ ] `.tta-dashboard-card`
- [ ] `.tta-auth-card`
- [ ] `.tta-stat-card`

### Badges/chips/scores

- [ ] `.tta-badge`
- [ ] `.tta-badge-brand`
- [ ] `.tta-badge-success`
- [ ] `.tta-badge-warning`
- [ ] `.tta-badge-danger`
- [ ] `.tta-badge-muted`
- [ ] `.tta-badge-info`
- [ ] `.tta-skill-chip`
- [ ] `.tta-skill-chip-required`
- [ ] `.tta-skill-chip-optional`
- [ ] `.tta-score-strong`
- [ ] `.tta-score-good`
- [ ] `.tta-score-partial`
- [ ] `.tta-score-weak`

### Forms

- [ ] `.tta-form-group`
- [ ] `.tta-label`
- [ ] `.tta-input`
- [ ] `.tta-select`
- [ ] `.tta-textarea`
- [ ] `.tta-checkbox`
- [ ] `.tta-help-text`
- [ ] `.tta-error-text`
- [ ] `.tta-field-error`
- [ ] `.tta-form-section`
- [ ] `.tta-form-grid`
- [ ] `.tta-sticky-save-bar`

### Drawer/dropdown

- [ ] `.tta-drawer-backdrop`
- [ ] `.tta-drawer-panel`
- [ ] `.tta-dropdown-menu`
- [ ] `.tta-dropdown-item`

### Progress/score

- [ ] `.tta-progress`
- [ ] `.tta-progress-bar`
- [ ] `.tta-score-ring`
- [ ] `.tta-score-ring-sm`
- [ ] `.tta-score-ring-md`
- [ ] `.tta-score-label`
- [ ] `.tta-score-caption`

### Toast/skeleton/dropzone/pagination/empty/legal/error

- [ ] `.tta-toast-container`
- [ ] `.tta-toast`
- [ ] `.tta-toast-success`
- [ ] `.tta-toast-warning`
- [ ] `.tta-toast-error`
- [ ] `.tta-toast-info`
- [ ] `.tta-skeleton`
- [ ] `.tta-skeleton-line`
- [ ] `.tta-skeleton-line-short`
- [ ] `.tta-skeleton-badge`
- [ ] `.tta-skeleton-card`
- [ ] `.tta-dropzone`
- [ ] `.tta-dropzone-active`
- [ ] `.tta-dropzone-error`
- [ ] `.tta-pagination`
- [ ] `.tta-pagination-link`
- [ ] `.tta-pagination-current`
- [ ] `.tta-pagination-disabled`
- [ ] `.tta-empty`
- [ ] `.tta-empty-icon`
- [ ] `.tta-empty-title`
- [ ] `.tta-empty-body`
- [ ] `.tta-empty-actions`
- [ ] `.tta-legal`
- [ ] `.tta-error-page`
- [ ] `.tta-error-code`
- [ ] `.tta-error-title`
- [ ] `.tta-error-body`

## Build/check acceptance

These must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

`git diff --cached --check` must pass before commit if files are staged.

Full tests should pass if run:

```bash
python manage.py test --settings=config.settings.local --parallel 1
```

If full tests are not run, Gemini and Codex must say why.

## Security/architecture acceptance

- [ ] No new forbidden frontend stack usage.
- [ ] No Tailwind CDN.
- [ ] No France Travail calls added to public search/views/templates/admin.
- [ ] No OpenRouter calls added to views/templates/admin.
- [ ] No CV file URL/raw text exposure.
- [ ] No internal integer public routes added.
- [ ] No secrets in diff.

## Manual visual sanity acceptance

Because this phase does not apply classes to templates yet, manual visual changes should be minimal.

- [ ] Existing pages still load.
- [ ] No obvious broken CSS after build.
- [ ] Admin still loads or is unaffected.

## Codex acceptance

- [ ] Codex verification report exists.
- [ ] Codex verdict is PASS.
