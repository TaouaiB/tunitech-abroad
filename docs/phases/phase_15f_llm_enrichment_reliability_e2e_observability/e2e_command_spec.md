# E2E LLM Pipeline Command Specification

## Required command

Add one local-only management command for controlled E2E testing.

Recommended name:

```bash
python manage.py run_llm_e2e_pipeline
```

Alternative names are acceptable if they follow project conventions.

## Required behavior

The command must run:

```text
France Travail broad IT ingestion
→ normalization
→ controlled LLM enrichment
→ LLM skill materialization
→ deterministic skill materialization
→ unmatched skill reconciliation
→ zero-skill recovery
→ public eligibility reclassification
→ final safety report
```

## Required flags

```text
--preset broad_it
--max-total 100
--limit-per-keyword 10
--max-pages-per-keyword 2
--force-llm-count 100
--force-provider-call
--apply
--dry-run
--min-llm-success 0..100
--settings=config.settings.local
```

`--force-provider-call` must be local-only. It must be blocked unless `settings.DEBUG is True` or unless an explicit safe local setting is enabled.

## Reporting counters

The command must print at least:

```text
selected_jobs
fetched_jobs
created_raw
updated_raw
normalized_jobs
llm_selected
llm_provider_attempted
auto_skipped_before_provider
success
failed
validation_error
invalid_json
invalid_json_retry_success
invalid_json_retry_failed
provider_circuit_blocked
budget_skipped
non_it_skipped
empty_skill_output
materialized_jobs
materialized_skill_rows
unmatched_candidates_created
public_visible
matchable
public_zero
matchable_zero
```

## Pass/fail behavior

The command must fail hard if:

```text
LLM config missing
OPENROUTER_API_KEY missing when real provider calls are requested
selected jobs < force_llm_count
llm_provider_attempted < requested count when --force-provider-call is used and provider is not unavailable
success < --min-llm-success
public_zero != 0
matchable_zero != 0
```

The command must not print “PASSED” if the LLM success target failed.

It may print separate verdicts:

```text
LLM_E2E: PASS / PARTIAL / FAIL
PUBLIC_SAFETY: PASS / FAIL
OVERALL: PASS / FAIL
```

## Dry-run mode

`--dry-run` must not create provider calls unless explicitly combined with a local test flag. Prefer default dry-run to inspect selected jobs only.

## No secrets

The command must never print:

```text
OPENROUTER_API_KEY
France Travail client secret
access tokens
raw auth headers
```

## Example target command

```bash
python manage.py run_llm_e2e_pipeline   --preset broad_it   --limit-per-keyword 10   --max-total 100   --max-pages-per-keyword 2   --force-llm-count 100   --force-provider-call   --min-llm-success 95   --apply   --settings=config.settings.local
```

For first verification, use a smaller run:

```bash
python manage.py run_llm_e2e_pipeline   --preset broad_it   --limit-per-keyword 2   --max-total 10   --force-llm-count 10   --force-provider-call   --min-llm-success 8   --apply   --settings=config.settings.local
```
