# Phase 14F — Automated France Travail IT Ingestion

## Purpose

Phase 14F builds the production job inventory pipeline for TuniTech Abroad.

The goal is not to call France Travail live during user search. The goal is to keep a large, fresh, France-first IT job inventory inside local PostgreSQL, then search/recommend from PostgreSQL only.

## Default product decision

Default configuration for this phase:

- Broad IT preset is enabled.
- `limit_per_keyword = 50`.
- `max_total_per_run = 1000`.
- Nightly broad run max total is `2000`.
- Every fetched and normalized active IT job should be queued for enrichment by default.
- Admin can reduce/increase volume, frequency, and enrichment behavior.
- Expired/stale jobs are marked inactive automatically.

“Every fetched job is enriched” means every fetched job that passes the IT relevance/eligibility gates and is active/normalized gets an enrichment record or enrichment task. Do not intentionally enrich plumbers, restaurants, warehouse jobs, or obvious non-IT roles.

## Files in this package

- `prompt.md` — main implementation instructions.
- `scope.md` — exact scope.
- `boundaries.md` — hard architecture limits.
- `admin_config_design.md` — admin-configurable ingestion model design.
- `broad_it_preset.md` — broad IT keyword and role-family coverage.
- `automation_design.md` — scheduling, Celery/Cron, enrichment, expiry flow.
- `tasks.md` — ticket checklist.
- `acceptance.md` — acceptance criteria.
- `test_plan.md` — required automated tests.
- `regression_security_checks.md` — commands/checks.
- `codex_verify_prompt.md` — independent verification prompt.
- `agent_report_template.md` — required final report format.
