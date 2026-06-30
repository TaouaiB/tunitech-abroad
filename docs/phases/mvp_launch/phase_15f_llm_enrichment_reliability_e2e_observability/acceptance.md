# Phase 15F Acceptance Criteria

## Hard acceptance

Phase 15F passes only if all of the following are true.

## LLM JSON handling

- JSON wrapped in markdown code fences can be parsed safely.
- JSON with leading/trailing prose can be parsed safely when one JSON object is extractable.
- Empty/non-object output is rejected.
- Invalid JSON is retried once.
- Retry success is saved as success with a clear reason.
- Retry failure is saved as failed or validation_error with a clear reason.
- Raw LLM output is not exposed publicly.

## Circuit breaker

- Invalid JSON does not open provider circuit.
- Schema validation errors do not open provider circuit.
- Non-IT/empty skill result does not open provider circuit.
- Provider circuit opens only for provider availability/config failures.
- `provider_circuit_open` rows have zero tokens.

## Skipped reasons

- Every skipped row has a useful `status_reason`.
- Skipped rows with tokens > 0 must not use `provider_circuit_open`.
- Skipped rows with tokens = 0 must distinguish circuit/budget/duplicate/local eligibility.

## E2E command

- One management command exists for local E2E LLM testing.
- It can fetch/normalize France Travail data.
- It can force N local LLM provider attempts under local-only guardrails.
- It materializes LLM output into canonical `NormalizedJobSkill` rows.
- It runs seed/materialize/reconcile/recover/reclassify cleanup.
- It prints truthful counters.
- It fails when configured LLM target is not met.
- It fails when `PUBLIC_ZERO != 0`.
- It fails when `MATCHABLE_ZERO != 0`.
- It never prints real secrets.

## Tests

Required checks pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Targeted tests cover:

- invalid JSON retry success;
- invalid JSON retry failure;
- invalid JSON does not open circuit;
- provider outage opens circuit;
- skipped reason consistency;
- E2E command truthful counters;
- E2E command failure when LLM target not met;
- final public safety checks.

## Forbidden changes

The phase fails if it introduces:

- React, Next.js, Angular, Vue SPA, FastAPI, MongoDB, SQLAlchemy;
- OpenRouter calls from views/templates/models/admin display;
- France Travail live calls from public search;
- matching score formula changes;
- UI redesign;
- fake skill creation;
- bulk unmatched skill promotion;
- real secrets in docs/logs/tests;
- public integer IDs;
- CV privacy regressions.

## Manual local canary

After automated tests, run a small real-provider canary:

```bash
python manage.py run_llm_e2e_pipeline   --preset broad_it   --limit-per-keyword 2   --max-total 10   --force-llm-count 10   --force-provider-call   --min-llm-success 8   --apply   --settings=config.settings.local
```

Expected:

```text
provider attempted > 0
success > 0
PUBLIC_ZERO = 0
MATCHABLE_ZERO = 0
truthful PASS/PARTIAL/FAIL output
```

Then optionally run 100-job E2E locally.
