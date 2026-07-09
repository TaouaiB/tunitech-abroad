# Phase 15F Codex Verification Report

## Verdict

Verdict:

```text
REPAIRED_PASS
```

## What I reviewed

- `apps/llm/services/job_enrichment.py`
- `apps/llm/models.py`
- `apps/llm/admin.py`
- `apps/llm/tests/test_15f_enrichment_reliability.py`
- `apps/jobs/management/commands/run_llm_e2e_pipeline.py`
- `apps/jobs/tests/test_run_llm_e2e_pipeline.py`
- `apps/jobs/services/eligibility.py`
- Phase 15F docs: acceptance, status reason policy, E2E command spec, test plan, prompt.

## Architecture compliance

```text
No forbidden stack introduced: YES
No OpenRouter from views/templates/models/admin display: YES
No France Travail live from public search: YES
Views thin: YES
Services own LLM logic: YES
No matching formula change: YES
No UI redesign: YES
No secrets exposed: YES
```

Notes:

- LLM provider calls remain in `apps.llm.services.job_enrichment.enrich_job`.
- The E2E management command calls services/management commands; no provider calls were added to views/templates/models/admin display.
- Raw LLM response fields remain model-internal and are excluded from the `JobEnrichmentAdmin` form/list display.
- Diff secret scan result: `OK: no obvious secrets in diff`.

## Invalid JSON verification

- Parser handles code fences: YES, covered by `_extract_json`.
- Parser handles prose around JSON: YES, covered by `_extract_json`.
- Invalid JSON retry once: YES, invalid JSON triggers one corrective provider retry only.
- Retry success behavior: YES, saves `status=success` with `status_reason=invalid_json_retry_success`.
- Retry failure behavior: YES, saves `status=validation_error` with `status_reason=invalid_json_retry_failed`.
- Raw output storage: YES, raw response text is retained internally on `JobEnrichment.raw_response_text` and not exposed publicly.
- Tests: `apps.llm.tests.test_15f_enrichment_reliability` passed.

## Circuit breaker verification

```text
Invalid JSON does not open circuit: YES
Schema validation does not open circuit: YES
Non-IT/empty skills do not open circuit: YES
Provider outages can open circuit: YES
provider_circuit_open implies tokens=0: YES
```

Notes:

- Circuit failure reasons are restricted to provider/auth/quota/rate/outage style failures.
- `invalid_json_retry_failed` and schema `validation_error` are permanent non-provider failures and are not counted by the provider circuit query.
- `_mark_provider_circuit_open` now clears prompt/completion/total tokens, estimated cost, and raw response data.

## E2E command verification

Command name:

```text
run_llm_e2e_pipeline
```

Flags supported:

```text
--preset
--limit-per-keyword
--max-total
--max-pages-per-keyword
--force-llm-count
--force-provider-call
--min-llm-success
--apply
```

Counters printed:

```text
Selected N jobs for enrichment.
Enrichment Results: Success=X, Skipped=Y, Failed=Z
LLM provider attempted: N
Status reasons:
PUBLIC_ZERO: N
MATCHABLE_ZERO: N
```

Fail conditions verified:

- Fails if `success_count < --min-llm-success`.
- Fails if `--force-provider-call` is used and provider-attempted count is below selected enrichment count.
- Fails if `PUBLIC_ZERO != 0`.
- Fails if `MATCHABLE_ZERO != 0`.

Local-only guardrail verified:

- `--force-provider-call` exits with failure unless `settings.DEBUG` is true.
- `enrich_job(..., force_provider_call=True)` raises unless `settings.DEBUG` is true.

## Tests run

```text
python manage.py test apps.llm.tests.test_15f_enrichment_reliability apps.jobs.tests.test_run_llm_e2e_pipeline --settings=config.settings.local --parallel 1
Result: OK, 9 tests
```

```text
python manage.py check --settings=config.settings.local
Result: System check identified no issues (0 silenced).
```

```text
python manage.py makemigrations --check --dry-run --settings=config.settings.local
Result: No changes detected
```

```text
npm run css:build
Result: Done in 850ms.
Note: Browserslist reported caniuse-lite is outdated.
```

```text
python manage.py test --settings=config.settings.local --parallel 1
Result: OK, 532 tests
```

```text
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
Result: 2 static files copied to staticfiles, 134 unmodified.
```

```text
git diff --check
Result: passed with no output.
```

```text
git diff -- . ':!.env' ':!.env.*' | grep -iE "sk-or-|Bearer [A-Za-z0-9_.-]{20,}|OPENROUTER_API_KEY=.*[^=]|FRANCE_TRAVAIL_CLIENT_SECRET=.*[^=]|EMAIL_HOST_PASSWORD=.*[^=]" || echo "OK: no obvious secrets in diff"
Result: OK: no obvious secrets in diff
```

## Repairs made by Codex

- Hardened `provider_circuit_open` handling to force token/cost/raw-response fields to zero/empty on circuit skips.
- Added local-only `force_provider_call` support to `enrich_job`.
- Added safe JSON extraction for markdown fences and leading/trailing prose.
- Added one invalid-JSON repair retry with explicit `invalid_json_retry_success` and `invalid_json_retry_failed` reasons.
- Kept invalid JSON/schema validation out of the provider circuit breaker failure set.
- Reset stale enrichment error/reason fields when a new provider attempt begins.
- Repaired `run_llm_e2e_pipeline` to print truthful counters, call the full ingestion/materialization/reconcile/recovery/reclassification flow, enforce local-only provider forcing, and fail on target/provider/public health conditions.
- Rebuilt Tailwind CSS after removing the accidental arbitrary class artifact.

## Final health checks

```text
PUBLIC_ZERO: 0
MATCHABLE_ZERO: 0
latest targeted test result: OK, 9 tests
full test result: OK, 532 tests
```

## Remaining concerns

- The local E2E command was verified through mocked test coverage and command acceptance behavior. I did not run a real OpenRouter-backed 100-job E2E call because that would consume live provider quota and depends on local secrets.
- `npm run css:build` reports an outdated Browserslist database. This is advisory and did not fail the build.

## Commit recommendation

```text
APPROVE_COMMIT
```
