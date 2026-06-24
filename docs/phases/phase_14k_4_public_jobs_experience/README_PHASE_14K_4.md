# README — Phase 14K-4 Public Jobs Experience

This package adds the phase instructions for public jobs UI polish.

## Files

- `tasks.md`
- `prompt_gemini.md`
- `prompt_codex.md`
- `acceptance.md`
- `agent_report_template.md`
- `codex_report_template.md`

## Workflow

1. Make sure previous phases are committed or intentionally left as current working tree changes.
2. Give Gemini `prompt_gemini.md`.
3. Gemini must implement and repair until PASS/REPAIRED_PASS.
4. Give Codex `prompt_codex.md`.
5. Codex must verify and repair until PASS/REPAIRED_PASS.
6. Baha reviews browser visuals.
7. Commit to `dev` only after review.

## Important rule

Do not block on staged/unstaged/mixed working tree noise. Agents should fix in-scope template/CSS/report issues directly and rerun checks.

Block only for real architecture, product, privacy, security, dependency, or out-of-scope problems.
