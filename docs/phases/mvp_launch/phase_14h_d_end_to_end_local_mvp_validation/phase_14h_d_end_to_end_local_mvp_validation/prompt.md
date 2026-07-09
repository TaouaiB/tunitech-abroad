# Phase 14H-D Prompt — End-to-End Local MVP Validation

You are working on TuniTech Abroad.

Read these files first:

- AGENTS.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/README.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/scope.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/boundaries.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/tasks.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/test_plan.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/regression_security_checks.md
- docs/phases/phase_14h_d_end_to_end_local_mvp_validation/acceptance.md

## Mission

Validate the complete local MVP end-to-end after Phase 14H-C.

This is a validation and small bug-fix phase only.

## Strict rules

- Do not commit.
- Do not deploy.
- Do not start Phase 14I.
- Do not add new features.
- Do not redesign the UI.
- Do not change matching scoring.
- Do not change CV parsing logic unless a clear blocking bug is found.
- Do not change job ingestion/enrichment logic unless a clear blocking bug is found.
- Do not introduce React, Next.js, Vue, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.
- Do not make public job search call France Travail live.
- Do not call OpenRouter/LLM from Django views.
- Do not expose CV file URLs or raw CV text.
- Do not use internal integer IDs in public URLs.

## Work loop

1. Run preflight checks.
2. Run automated checks.
3. Perform/prepare browser E2E validation.
4. Fix only blocking bugs within this phase.
5. Re-run relevant checks after each fix.
6. Create/update `docs/validation/local_mvp_e2e_report.md`.

## Required final report

Report:

- Files changed
- Commands run
- Browser flows tested
- Bugs found
- Bugs fixed
- Remaining risks
- Exact final verdict

Final verdict must be one of:

```text
FINAL_VERDICT: FAIL
FINAL_VERDICT: BLOCKED_HUMAN_VISUAL_SIGNOFF
```
