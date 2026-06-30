# Phase 15F Agent Report

## Verdict

Choose one:

```text
PASS
PARTIAL
BLOCKED
FAIL
```

Verdict:

## Summary

Briefly summarize what was implemented.

## Files changed

List changed files.

## Current LLM flow after changes

Describe:

```text
provider call path
JSON parsing path
retry path
validation path
circuit breaker path
materialization path
```

## Invalid JSON handling

- How invalid JSON is detected:
- Whether code fences/prose are handled:
- Retry behavior:
- Final status/reason on retry success:
- Final status/reason on retry failure:

## Circuit breaker behavior

- Failures that open circuit:
- Failures that do not open circuit:
- Tests proving invalid JSON does not open circuit:

## Skipped reason behavior

Explain how skipped rows are categorized.

Confirm:

```text
provider_circuit_open rows have zero tokens: YES/NO
skipped rows always have status_reason: YES/NO
skipped rows with tokens > 0 do not use provider_circuit_open: YES/NO
```

## E2E command

Command name:

Example command:

Counters printed:

Fail conditions:

Local-only guardrails:

## Tests run

Paste exact commands and results.

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

## Manual E2E result

If run, paste summary:

```text
selected_jobs:
provider_attempted:
success:
invalid_json:
validation_error:
skipped:
provider_circuit_open:
materialized_skill_rows:
PUBLIC_ZERO:
MATCHABLE_ZERO:
```

## Security/privacy checks

- Secrets in diff:
- Provider calls from views/templates/models:
- Public search external API calls:
- CV privacy touched:

## Remaining risks

List any remaining concerns.

## Blockers

List blockers, or `None`.
