# Phase 15F Tasks — LLM Enrichment Reliability and E2E Observability

## Ticket 15F-01 — Inspect current LLM enrichment flow

Inspect the current code paths for:

- `apps/llm/services/job_enrichment.py`
- OpenRouter client/service code
- JSON parsing/validation code
- provider circuit breaker code
- Celery enrichment tasks
- ingestion command integration
- `JobEnrichment` model fields and status choices
- materialization from LLM output

Document the current path in the agent report.

Do not rewrite architecture before understanding the existing code.

## Ticket 15F-02 — Add explicit status reason constants

Add centralized constants/enums for LLM enrichment status reasons.

Prefer a constants module or service-local constants. Do not add a DB migration unless absolutely necessary.

Required reason groups:

- success
- invalid JSON
- schema validation
- provider circuit open
- provider transport/auth/rate/5xx/network failures
- budget/rate local skips
- non-IT/low-confidence skips
- duplicate/already enriched skips
- not enough text
- empty skill output

Replace free-text string comparisons where practical.

## Ticket 15F-03 — Harden JSON parsing

Add robust JSON parsing for LLM responses:

- strip markdown code fences;
- extract the first JSON object if the response includes prose;
- reject empty/non-object output;
- keep raw response saved internally;
- never expose raw response publicly.

Do not silently accept malformed data that cannot be parsed safely.

## Ticket 15F-04 — Add one retry for invalid JSON

If the first provider response is invalid JSON:

1. Record the first parse error internally.
2. Retry once with a stricter JSON-only repair prompt or stricter generation prompt.
3. If retry succeeds, save `success` with reason `invalid_json_retry_success`.
4. If retry fails, save failed/validation-error with reason `invalid_json_retry_failed`.

Do not retry endlessly.

## Ticket 15F-05 — Fix provider circuit breaker behavior

Invalid JSON and schema validation failures must not open the provider circuit.

The circuit may open only for provider availability/config failures:

- timeout;
- network error;
- rate limit / 429;
- provider 5xx;
- auth/forbidden config error;
- quota/credits unavailable.

Add tests proving invalid JSON does not open the circuit.

## Ticket 15F-06 — Clarify skipped semantics

Ensure skipped rows are explainable.

Required behavior:

- `provider_circuit_open` rows must have zero tokens.
- skipped rows with tokens must have a model-result reason such as non-IT, low confidence, empty skills, etc.
- no skipped row should have `provider_circuit_open` if it actually consumed tokens.

## Ticket 15F-07 — Add local-only force provider mode

Add a safe local-only mechanism for E2E testing that attempts provider calls even when normal cache/skip logic would skip.

Options:

- `enrich_job(..., force=True, force_provider_call=True)`; or
- service options object; or
- management command flag `--force-provider-call`.

Guardrail:

- only allowed when `settings.DEBUG is True` or a clearly local-only setting is enabled;
- never used by views/templates/admin display;
- never default in production.

## Ticket 15F-08 — Add one E2E LLM pipeline command

Create one management command that can run the full local test in one command.

Recommended name:

```bash
python manage.py run_llm_e2e_pipeline
```

The command must perform:

1. France Travail broad IT ingestion.
2. Normalization.
3. Controlled LLM enrichment for N selected jobs.
4. LLM materialization.
5. Seed skills.
6. Deterministic materialization.
7. Reconcile unmatched candidates.
8. Zero-skill recovery.
9. Reclassification.
10. Final public safety health report.

The command must be honest: do not print PASS when the LLM target failed.

## Ticket 15F-09 — Add tests

Add focused tests for:

- parsing JSON wrapped in code fences;
- parsing JSON with leading/trailing prose;
- invalid JSON first response + valid retry response;
- invalid JSON retry failure;
- invalid JSON does not open circuit;
- provider timeout/rate limit does open circuit;
- skipped reason consistency;
- E2E command counters with mocked provider;
- E2E command fails when success target is not met;
- public safety remains `PUBLIC_ZERO=0`, `MATCHABLE_ZERO=0` in representative cases.

Tests must mock provider calls. Unit tests must not call OpenRouter.

## Ticket 15F-10 — Run verification

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Also run targeted tests for the LLM service and new command.

## Ticket 15F-11 — Manual local E2E canary

After automated tests pass, run:

```bash
python manage.py run_llm_e2e_pipeline   --preset broad_it   --limit-per-keyword 2   --max-total 10   --force-llm-count 10   --force-provider-call   --min-llm-success 8   --apply   --settings=config.settings.local
```

Then, only if clean, run the 100-job local E2E test.

Do not run real-provider E2E in automated tests.
