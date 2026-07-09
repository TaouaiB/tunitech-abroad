# Phase 14B.3R — Data-correct UI Refinement with Multi-CV Coverage

## Purpose

This phase repairs the failed Phase 14B / 14B.1 / 14B.2 UI passes by forcing the product flow to be correct before more visual polish is accepted.

The goal is not to redesign the whole product again. The goal is to make the current local MVP credible in Chrome:

- CV extraction must extract realistic fields from multiple CV shapes, not only one test CV.
- Profile application must use extracted values safely.
- Profile completion must be truthful.
- Recommendations must show either real recommendations or exact blocked reasons.
- The UI must use a coherent modern style inspired by the provided reference, without copying React/Vite or adding forbidden stack.
- The phase cannot pass from the agent's self-report alone. Human Chrome sign-off by Baha is required.

## Agent entry point

Give the coding agent only this instruction:

```text
Read and execute docs/phases/phase_14b3r_data_correct_ui_refinement/prompt.md exactly.
```

## Package files

- `README.md` — phase overview
- `scope.md` — exact in/out scope
- `boundaries.md` — hard technical and architecture boundaries
- `observed_issues.md` — bugs found from manual QA
- `visual_reference_analysis.md` — visual direction from the attached design reference, stack-safe
- `multi_cv_fixture_requirements.md` — required extractor fixture coverage beyond one CV
- `tasks.md` — implementation tasks
- `preflight.md` — required preflight commands
- `prompt.md` — main autonomous agent prompt
- `acceptance.md` — hard acceptance gates
- `test_plan.md` — automated + browser + manual verification
- `regression_security_checks.md` — privacy/security greps
- `human_signoff.md` — manual approval checklist for Baha
- `agent_report_template.md` — required final report
- `codex_verify_prompt.md` — independent verifier prompt

## Stage after PASS

If this phase passes, the project moves from:

```text
Backend-stabilized but UI/product flow unreliable
```

to:

```text
Data-correct, visually coherent local MVP candidate ready for final manual walkthrough.
```

Do not deploy after this phase automatically.
