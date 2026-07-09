# Codex Verification Prompt — Phase 14K-0 Approved UI/UX Design Docs Import

You are verifying Gemini's work for **Phase 14K-0 — Approved UI/UX Design Docs Import**.

Your role is verification only. Do not implement UI changes. Do not start Phase 14K-1.

## Read first

Read:

1. `AGENTS.md`
2. `docs/phases/phase_14k_0_design_docs_import/tasks.md`
3. `docs/phases/phase_14k_0_design_docs_import/acceptance.md`
4. `docs/design/approved_ui_ux/README_APPROVED.md`
5. `docs/design/approved_ui_ux/design_vision/README.md`
6. `docs/design/approved_ui_ux/static_ui_prototype/README.md`
7. `docs/design/approved_ui_ux/static_ui_prototype/prototype-map.html`

## Verification objective

Confirm that Gemini only imported the approved UI/UX design package and phase documentation.

This phase must not change application behavior.

## Required verification checks

Run:

```bash
git status --short
git diff --stat
git diff --name-only
find docs/design/approved_ui_ux -maxdepth 2 -type f | sort | head -120
find docs/phases/phase_14k_0_design_docs_import -maxdepth 1 -type f | sort
git diff --check
```

Check that changed or untracked files are limited to:

```text
docs/design/approved_ui_ux/**
docs/phases/phase_14k_0_design_docs_import/**
```

If any of these changed, mark BLOCKED unless the user explicitly confirms they were pre-existing changes:

```text
templates/**
static/**
apps/**
config/**
tailwind.config.js
package.json
package-lock.json
requirements*.txt
pyproject.toml
manage.py
.env
.env.*
```

Run these only if app files changed or if you want extra safety:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
npm run css:build
```

## PASS / BLOCKED / FAIL rules

PASS only if:

- approved design docs exist under `docs/design/approved_ui_ux/`
- static prototype exists under `docs/design/approved_ui_ux/static_ui_prototype/`
- phase files exist under `docs/phases/phase_14k_0_design_docs_import/`
- no app code changed in this phase
- no dependencies changed
- no `.env` or secret-like file was added/modified
- `git diff --check` passes
- Phase 14K-1 was not started

BLOCKED if:

- app code changed and it is unclear whether it was pre-existing
- docs are missing or incomplete
- generated files are in the wrong location
- `.env` or secrets appear in the diff

FAIL if:

- Gemini implemented UI changes
- Gemini changed backend behavior
- Gemini started another phase
- route/template/static files were modified as part of this docs import

## Final report

Use `docs/phases/phase_14k_0_design_docs_import/codex_report_template.md`.
