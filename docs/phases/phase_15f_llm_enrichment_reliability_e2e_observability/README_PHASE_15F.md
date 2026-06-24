# Phase 15F — LLM Enrichment Reliability and E2E Observability

## Purpose

Phase 15F hardens the real France Travail → normalization → LLM enrichment → skill materialization → public eligibility pipeline before deployment.

This phase exists because the 100-job local E2E test proved that the public pipeline stayed safe, but the LLM enrichment pipeline is not production-clean yet.

Observed local E2E result:

```text
100 selected jobs
72 reached the LLM provider because total_tokens > 0
64 finished as success
2 failed with: LLM response is not valid JSON
34 finished as skipped
28 were pre-skipped with total_tokens = 0
many pre-skips had status_reason = provider_circuit_open
PUBLIC_ZERO = 0
MATCHABLE_ZERO = 0
```

The public product safety checks passed, but the LLM observability and reliability are not acceptable yet.

## Phase goal

Make the LLM enrichment pipeline reliable, honest, and testable:

1. Invalid JSON must be retried or repaired safely.
2. Invalid JSON must not open the provider circuit breaker.
3. `skipped` must have clear, actionable reasons.
4. Forced local E2E testing must actually attempt provider calls when explicitly requested.
5. The E2E command must produce truthful counters and fail when LLM targets are not met.
6. Public search/matching safety must remain unchanged: no public/matchable zero-skill jobs.

## Non-goals

Do not redesign UI.
Do not change the matching score formula.
Do not change public job search architecture.
Do not add React, Next.js, FastAPI, MongoDB, SQLAlchemy, or SPA behavior.
Do not call OpenRouter from views, templates, models, or admin display methods.
Do not call France Travail live from public search.
Do not promote all unmatched skills automatically.
Do not fake skills just to make jobs matchable.
Do not remove circuit breaker protection in production.

## Critical architecture rules

- Views stay thin.
- Business logic stays in services.
- Celery tasks call services only.
- Models store data only and do not call providers.
- LLM provider calls stay inside LLM/job-enrichment services or Celery tasks.
- Public URLs continue using UUID `public_id`.
- Public search reads local PostgreSQL only.
- CV privacy rules must not be touched.
- `.env` is never read into docs, printed, logged, or committed.

## Expected final state

A local command can run a controlled E2E test such as:

```bash
python manage.py run_llm_e2e_pipeline   --preset broad_it   --max-total 100   --force-llm-count 100   --force-provider-call   --apply   --settings=config.settings.local
```

The exact command name may differ if the existing codebase has a better naming convention, but it must be a single management command and must print truthful counters.

A successful phase does not require 100/100 model success in all real-world conditions, because providers can return malformed output or fail. It does require that the report tells the truth and that invalid JSON does not incorrectly open the provider circuit.
