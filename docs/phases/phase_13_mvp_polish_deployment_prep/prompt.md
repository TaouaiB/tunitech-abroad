# Phase 13 Implementation Prompt — MVP Polish and Deployment Preparation

You are implementing Phase 13 only for TuniTech Abroad.

Read first:

1. `AGENTS.md`
2. `docs/phases/phase_13_mvp_polish_deployment_prep/preflight.md`
3. `docs/phases/phase_13_mvp_polish_deployment_prep/tasks.md`
4. `docs/phases/phase_13_mvp_polish_deployment_prep/acceptance.md`
5. Relevant planning docs in `docs/planning/`, especially Implementation Roadmap, PRD, Working Agreement, Service Contracts, Page/URL/View Map.

## Mission

Prepare the MVP for first controlled external use by polishing user-facing pages, safe error/empty states, French wording, responsive layout, production-prep settings, static/private media readiness, seed/fixture docs, and deployment documentation.

This is not production deployment. Do not start Phase 14.

## Preflight

Run the preflight from `preflight.md`. If PostgreSQL-backed migrate or cache check is blocked, report BLOCKED and stop. Do not continue with SQLite-only validation.

## Implementation rules

- Implement all tickets in `tasks.md`.
- You may work automatically through all Phase 13 tickets.
- Do not ask for approval between tickets.
- Do not implement Phase 14.
- Do not deploy.
- Do not add external SaaS monitoring.
- Do not add new product features outside polish/prep.
- Do not add React/Next/Angular/FastAPI/MongoDB/SQLAlchemy/SPA architecture.
- Keep Django templates + HTMX + Tailwind.
- Views stay thin.
- Use forms/services for validation/business logic.
- No OpenRouter calls from views/admin/templates.
- No France Travail live calls during user search.
- Use public UUID `public_id` for public URLs.
- Keep CV files private.
- Never print, commit, log, or document real secrets.

## Autonomous repair loop

After each logical block:

1. run targeted tests/checks
2. inspect failures
3. fix root cause
4. rerun failed command
5. continue

At the end, run the full acceptance suite in `acceptance.md`.

You may perform up to 8 repair loops. Stop only when acceptance passes or when a real blocker remains.

## Strict PASS/BLOCKED/FAIL policy

- PASS only if PostgreSQL-backed `migrate` and required tests actually run and end with OK.
- BLOCKED if Docker/Podman/PostgreSQL/Redis/cache is inaccessible and prevents verification.
- FAIL if tests run and fail.
- SQLite smoke tests are not final acceptance.
- `Found 0 test(s)` is failure.
- Hidden HTTP 500 in test logs is failure unless explicitly expected/tested.
- Stale `agent_report.md` claiming the wrong status is failure.

## Reporting

Create:

`docs/phases/phase_13_mvp_polish_deployment_prep/agent_report.md`

Use `agent_report_template.md` exactly.

Include:

- completed tickets
- files created/changed
- settings/env variables added to `.env.example`
- commands run
- exact test counts and final status
- manual checks still needed
- screenshots not required
- risks/blockers

Stop after Phase 13.
