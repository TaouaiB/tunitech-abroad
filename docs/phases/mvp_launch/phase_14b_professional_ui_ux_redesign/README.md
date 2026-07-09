# Phase 14B — Professional UI/UX Redesign and Browser QA

## Purpose

Phase 14B turns the backend-stabilized local MVP into a credible, modern, youth-oriented, France-first product interface.

This phase is frontend/UI/UX only. It must not change the product architecture, backend scoring authority, ingestion rules, LLM boundaries, privacy rules, or deployment setup.

## Current stage

Phase 14A is treated as complete before this phase starts:

- Django checks pass.
- Full test suite passed.
- Real OpenRouter smoke validation passed.
- Real France Travail small ingestion passed.
- Local database has normalized active jobs.
- Backend MVP spine works.

The weakness now is visual and UX quality.

## How to run this phase

From repo root:

```bash
cd ~/Projects/tunitech-abroad
unzip ~/Downloads/phase_14b_professional_ui_ux_redesign_package.zip
```

Then give Gemini/Antigravity only:

```text
Read and execute docs/phases/phase_14b_professional_ui_ux_redesign/prompt.md exactly.
```

## Files in this phase

- `scope.md` — exact phase scope.
- `boundaries.md` — hard architecture and product limits.
- `design_brief.md` — visual direction and UX goals.
- `tasks.md` — implementation tickets.
- `preflight.md` — required starting checks.
- `prompt.md` — exact autonomous agent prompt.
- `acceptance.md` — hard acceptance gates.
- `test_plan.md` — automated and browser QA plan.
- `page_checklist.md` — per-page redesign checklist.
- `component_checklist.md` — shared UI component checklist.
- `regression_security_checks.md` — security/privacy/architecture grep checks.
- `agent_report_template.md` — final report required from the agent.
- `codex_verify_prompt.md` — independent verification prompt after Gemini finishes.

## Strict result

After this phase passes:

```text
Backend-stabilized + UI-polished local MVP
Ready for final manual walkthrough
Not deployed yet
```
