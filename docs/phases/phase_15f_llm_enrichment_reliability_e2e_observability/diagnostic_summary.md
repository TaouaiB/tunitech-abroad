# Phase 15F Diagnostic Summary

## What happened

A real local 100-job test was run against fresh/updated France Travail data.

The user forced LLM enrichment on 100 active, non-excluded jobs. The final public safety checks passed:

```text
PUBLIC_VISIBLE: 206
MATCHABLE: 206
PUBLIC_ZERO: 0
MATCHABLE_ZERO: 0
```

However, the LLM-specific result was not clean:

```text
LATEST 100 ENRICHMENT STATUS:
failed: 2
skipped: 34
success: 64

LATEST 100 TOKEN GROUPS:
reached_llm_tokens_gt_0: 72
pre_skipped_tokens_0: 28

SKIPPED BREAKDOWN:
skipped_tokens_gt_0: 7
skipped_tokens_0: 27
failed: 2
success: 64
```

Many skipped rows had:

```text
STATUS_REASON: provider_circuit_open
TOKENS: 0
```

That means the provider was not called for those jobs.

## Main problem

`provider_circuit_open` appears to be triggered after provider/model-output failures, especially invalid JSON.

Invalid JSON is not the same as provider outage. It means:

```text
Provider responded
Model output was malformed or not parseable JSON
Application parser rejected it
```

This should not necessarily open the provider circuit and block later jobs.

## Why invalid JSON happens

LLM output can be invalid JSON when the model:

- wraps JSON in markdown fences;
- adds prose before/after JSON;
- returns trailing commas;
- returns unescaped quotes from the job description;
- truncates output;
- returns partial JSON;
- violates the requested schema;
- returns an empty or non-object response.

The app must treat this as an expected provider/model behavior and harden around it.

## What must be fixed

1. Add robust JSON extraction/repair before marking failure.
2. Retry invalid JSON once with a stricter JSON-only retry prompt.
3. Do not open the provider circuit for invalid JSON or schema validation failures.
4. Distinguish `provider_circuit_open` from `invalid_json`, `validation_error`, `non_it_skipped`, `budget_skipped`, and `duplicate_payload_skipped`.
5. Add one honest local E2E command with truthful counters.
6. Keep public safety checks passing.

## What is already good

- LLM config is enabled locally.
- OpenRouter key is present locally.
- Real OpenRouter calls are being made.
- Successful `JobEnrichment` rows are created.
- LLM output can materialize into `NormalizedJobSkill` rows.
- Public eligibility currently prevents zero-skill public/matchable jobs.
