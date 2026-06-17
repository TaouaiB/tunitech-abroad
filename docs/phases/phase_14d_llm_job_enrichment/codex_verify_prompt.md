# Codex Verification Prompt — Phase 14D

Read and verify Phase 14D implementation only.

Do not commit.
Do not deploy.
Do not start any next phase.
Final verdict must be FAIL or BLOCKED_HUMAN_VISUAL_SIGNOFF.
Never write PASS before Baha manual Chrome approval.

## Read first

- `docs/phases/phase_14d_llm_job_enrichment/README.md`
- `docs/phases/phase_14d_llm_job_enrichment/scope.md`
- `docs/phases/phase_14d_llm_job_enrichment/boundaries.md`
- `docs/phases/phase_14d_llm_job_enrichment/llm_schema_contract.md`
- `docs/phases/phase_14d_llm_job_enrichment/data_model.md`
- `docs/phases/phase_14d_llm_job_enrichment/feature_flags_and_costs.md`
- `docs/phases/phase_14d_llm_job_enrichment/acceptance.md`
- `docs/phases/phase_14d_llm_job_enrichment/test_plan.md`
- `docs/phases/phase_14d_llm_job_enrichment/regression_security_checks.md`
- `docs/phases/phase_14d_llm_job_enrichment/agent_report.md` if present

## Verify

1. Confirm JobEnrichment status model exists.
2. Confirm raw LLM response and validated output are separate.
3. Confirm token/cost tracking exists.
4. Confirm feature flags exist and default safely.
5. Confirm LLM calls are service/Celery/management-command only, never views.
6. Confirm final fit score remains deterministic.
7. Confirm recommendations use enriched data only behind feature flag.
8. Confirm public/user templates do not show internal parser/debug labels.
9. Confirm tests cover Ciril Java, weak Web Developer, photography seller, and feature flags.
10. Run commands in `regression_security_checks.md`.

## If you find failures

Fix only Phase 14D scope. Do not redesign broadly.

## Final report

Return:

- files inspected
- failures found/fixed
- commands run and results
- remaining risks
- verdict: FAIL or BLOCKED_HUMAN_VISUAL_SIGNOFF
