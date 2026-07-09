# Gemini Prompt — Phase 14K-0 Approved UI/UX Design Docs Import

You are implementing **Phase 14K-0 — Approved UI/UX Design Docs Import** for TuniTech Abroad.

This is a documentation/import phase only.

## Read first

Read:

1. `AGENTS.md`
2. `docs/phases/phase_14k_0_design_docs_import/tasks.md`
3. `docs/phases/phase_14k_0_design_docs_import/acceptance.md`
4. `docs/design/approved_ui_ux/README_APPROVED.md`
5. `docs/design/approved_ui_ux/design_vision/README.md`
6. `docs/design/approved_ui_ux/static_ui_prototype/README.md`
7. `docs/design/approved_ui_ux/static_ui_prototype/prototype-map.html`

## Task

Verify that the approved UI/UX package is correctly present in the repository under:

```text
docs/design/approved_ui_ux/
```

Verify that the phase files are present under:

```text
docs/phases/phase_14k_0_design_docs_import/
```

Do not implement UI changes.

## Hard boundaries

You may only add or adjust documentation files if something is missing from this import phase.

Do not modify:

- `templates/`
- `static/`
- `apps/`
- `config/`
- `tailwind.config.js`
- `package.json`
- `package-lock.json`
- `requirements*`
- migrations
- `.env` or `.env.*`

Do not add dependencies.
Do not start Phase 14K-1.
Do not redesign anything.

## Verification commands

Run:

```bash
git status --short
find docs/design/approved_ui_ux -maxdepth 2 -type f | sort | head -80
find docs/phases/phase_14k_0_design_docs_import -maxdepth 1 -type f | sort
git diff --check
```

If any app code changed, stop and report it as a violation unless it was already present before you started.

## Final report

Use `docs/phases/phase_14k_0_design_docs_import/agent_report_template.md`.

Your report must clearly say:

- whether this stayed docs-only
- whether any app code changed
- where the approved UI/UX docs are located
- where the static HTML prototype is located
- which commands passed
- whether Phase 14K-1 was not started
