# Phase 14K-0 — Approved UI/UX Design Docs Import

## Purpose

Add the approved TuniTech Abroad UI/UX design source of truth to the repository so future Gemini implementation phases and Codex verification phases can reference the same stable files.

This is a documentation/import phase only. It does not implement UI changes.

## Source of truth being imported

The approved design package must live at:

```text
docs/design/approved_ui_ux/
```

Required contents:

```text
docs/design/approved_ui_ux/README_APPROVED.md
docs/design/approved_ui_ux/design_vision/*.md
docs/design/approved_ui_ux/static_ui_prototype/*.html
docs/design/approved_ui_ux/static_ui_prototype/assets/*
```

The static HTML prototype is visual reference only. It is not Django code and must not be copied blindly into templates.

## Scope

Allowed changes:

- Add `docs/design/approved_ui_ux/` files.
- Add this phase folder under `docs/phases/phase_14k_0_design_docs_import/`.
- Add documentation-only notes if needed.

Forbidden changes:

- Do not edit Django templates.
- Do not edit `static/src/css/app.css` or compiled CSS.
- Do not edit `tailwind.config.js`.
- Do not edit views, forms, URLs, models, services, tasks, admin, settings, migrations, package files, or dependencies.
- Do not add React, Next.js, Vue, Angular, SPA code, new JS libraries, django-widget-tweaks, django-crispy-forms, or Tailwind plugins.
- Do not create or modify `.env`.
- Do not print, inspect, or document secrets.
- Do not start Phase 14K-1.

## Required checks

Because this is docs-only, there should be no code changes. Still run basic safety checks:

```bash
cd ~/Projects/tunitech-abroad
git status --short
find docs/design/approved_ui_ux -maxdepth 2 -type f | sort | head -80
find docs/phases/phase_14k_0_design_docs_import -maxdepth 1 -type f | sort
git diff --check
```

Optional if the working tree already has app changes or the agent touched anything unexpected:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
npm run css:build
```

## Done when

- Approved design docs are present under `docs/design/approved_ui_ux/`.
- Static prototype is present under `docs/design/approved_ui_ux/static_ui_prototype/`.
- Phase 14K-0 files are present.
- No app code was changed.
- `git diff --check` passes.
- Agent report confirms this is docs-only.
