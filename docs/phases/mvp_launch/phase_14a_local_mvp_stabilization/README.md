# Phase 14A — Local MVP Stabilization and Real Integration Acceptance

This package is for a single autonomous agent run after the initial MVP build and before any new deployment attempt.

Purpose: stabilize the existing MVP locally, using real PostgreSQL-backed tests, service-level real LLM validation, small real France Travail ingestion validation when credentials exist, and deterministic no-browser route/template tests.

This is not a new product phase. It is a repair-and-acceptance phase over the already implemented MVP.

## Files in this package

```text
docs/phases/phase_14a_local_mvp_stabilization/
├── README.md
├── scope.md
├── boundaries.md
├── observed_issues.md
├── tasks.md
├── preflight.md
├── prompt.md
├── acceptance.md
├── test_plan.md
├── real_validation.md
├── agent_report_template.md
└── codex_verify_prompt.md
```

## How to run with Gemini / Antigravity / CLI agent

Start from repo root:

```bash
cd ~/Projects/tunitech-abroad
git checkout dev
```

Give the agent only this instruction:

```text
Read and execute docs/phases/phase_14a_local_mvp_stabilization/prompt.md exactly.
```

The agent must read all files in this phase folder before editing code.

## Success definition

The agent may report `PASS` only when all of these are true:

1. PostgreSQL-backed `migrate` runs successfully.
2. Full Django test suite runs and does not say `Found 0 test(s)`.
3. CV parsing extracts the full acceptance sample fields from a text-based PDF.
4. Recommendations generate stored recommendations for a usable profile and active jobs.
5. Quick match can be re-run with changed skills and does not return stale results.
6. Production-style 404 is safe and does not show Django URLconf debug data.
7. Real OpenRouter LLM validation runs successfully using environment credentials.
8. Small real France Travail ingestion validation runs successfully when credentials are present.
9. No secrets are printed, logged, committed, or copied into reports.

If PostgreSQL, Redis, OpenRouter, or France Travail credentials are unavailable, the agent must report `BLOCKED` for that exact external dependency and must not mark full `PASS`.

## No browser rule

No browser automation, no Playwright, no Selenium, no manual UI test requirement.

Use Django test client, RequestFactory, service tests, management command tests, template rendering tests, and static template assertions.
