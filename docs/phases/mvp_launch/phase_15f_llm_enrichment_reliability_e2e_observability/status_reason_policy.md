# LLM Enrichment Status Reason Policy

## Goal

`JobEnrichment.status` and `JobEnrichment.status_reason` must tell the truth.

Avoid vague skipped rows. A skipped row with no clear reason is not useful during deployment debugging.

## Recommended statuses

Use existing status choices if possible. Avoid a migration unless necessary.

Preferred behavior:

```text
status = success
status = failed
status = skipped
status = validation_error
```

Use `status_reason` for detailed reason codes.

## Required `status_reason` codes

Use constants, not free-text strings.

```text
success
invalid_json
invalid_json_retry_success
invalid_json_retry_failed
schema_validation_error
provider_circuit_open
provider_rate_limited
provider_auth_error
provider_timeout
provider_5xx
provider_network_error
budget_limit_reached
non_it_role
low_confidence_non_it
not_enough_text
empty_skill_output
duplicate_payload
already_enriched
manual_force_skipped
```

The exact names may be adjusted to match current code style, but they must be consistent and tested.

## Circuit breaker rules

The provider circuit may open for provider availability failures:

```text
network error
timeout
HTTP 429 rate limit
HTTP 401/403 auth/config error
HTTP 5xx provider error
quota/credits unavailable
provider unavailable
```

The provider circuit must not open for normal model-quality failures:

```text
invalid JSON
schema validation error
LLM says is_it_role=false
LLM returns empty skills
LLM returns low confidence
job does not qualify
```

Those are row-level outcomes, not provider availability failures.

## Token interpretation

`total_tokens > 0` means the provider was called.

`total_tokens = 0` means either:

```text
pre-provider skip
provider circuit open before call
budget skip
already enriched / duplicate payload skip
local eligibility skip
```

Reports must separate these cases.

## Skipped rows with tokens

A row with `status=skipped` and `total_tokens > 0` is allowed only if the provider was called and the model result intentionally led to a skip, for example:

```text
non_it_role
low_confidence_non_it
empty_skill_output
```

It must not use `provider_circuit_open` as the reason if tokens were consumed.

## Provider circuit open rows

If `status_reason=provider_circuit_open`, then expected state is:

```text
status = skipped
prompt_tokens = 0
completion_tokens = 0
total_tokens = 0
raw_response_text empty/null
validated_output_json empty/null
```

## Invalid JSON rows

If the provider returned invalid JSON after retry/repair fails:

```text
status = failed or validation_error
status_reason = invalid_json_retry_failed
raw_response_text must be saved for admin/internal debugging
no public user output should use it
circuit must not open because of this alone
```
