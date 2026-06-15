# Phase 13 — MVP Polish and Deployment Preparation

## Purpose

Phase 13 prepares TuniTech Abroad for first controlled external use. It is not production deployment. It polishes the MVP, fixes UX gaps, adds safe production-prep settings/documentation, and verifies critical flows before Phase 14.

## Files

- `tasks.md` — Phase 13 tickets and strict scope.
- `prompt.md` — Prompt to paste into Gemini/Antigravity implementation agent.
- `acceptance.md` — Exact acceptance commands and manual checks.
- `agent_report_template.md` — Report the implementation agent must fill.
- `codex_verify_prompt.md` — Strict verification prompt for Codex.
- `preflight.md` — Required environment preflight before implementation/verification.

## How to use

1. Commit Phase 12 first.
2. Add this folder to `docs/phases/phase_13_mvp_polish_deployment_prep/`.
3. Start implementation agent with `prompt.md`.
4. After implementation, run Codex verification from normal Warp using:

```bash
codex-tunitech
```

Then paste:

```text
Run docs/phases/phase_13_mvp_polish_deployment_prep/codex_verify_prompt.md.

Do not mark PASS unless PostgreSQL-backed migrate and manage.py test commands actually run and end with OK.
If Docker/PostgreSQL/Redis is blocked, report BLOCKED.
If tests run and fail, report FAIL.
```

## Secrets

No real secrets are needed for Phase 13. Agents may add or update `.env.example` with variable names only. Baha fills real production secrets manually later in Phase 14. Never print, commit, log, or document real secret values.
