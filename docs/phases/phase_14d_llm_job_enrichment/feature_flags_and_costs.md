# Feature Flags and Cost Monitoring

## Required feature flags

Add to settings with env overrides:

```python
JOB_ENRICHMENT_ENABLED = env_bool("JOB_ENRICHMENT_ENABLED", False)
JOB_RECOMMENDATIONS_USE_ENRICHED_DATA = env_bool("JOB_RECOMMENDATIONS_USE_ENRICHED_DATA", False)
JOB_ENRICHMENT_MODEL = os.environ.get("JOB_ENRICHMENT_MODEL", "")
JOB_ENRICHMENT_DAILY_LIMIT = env_int("JOB_ENRICHMENT_DAILY_LIMIT", 50)
JOB_ENRICHMENT_MAX_CHARS = env_int("JOB_ENRICHMENT_MAX_CHARS", 6000)
JOB_ENRICHMENT_MAX_RETRIES = env_int("JOB_ENRICHMENT_MAX_RETRIES", 2)
```

Document in `.env.example` only. Never put real secrets.

## Behavior by flags

`JOB_ENRICHMENT_ENABLED=False`:

- management command must not enqueue LLM calls unless `--dry-run` or explicit override used for tests
- Celery task must exit safely with status `skipped` or no-op

`JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=False`:

- matching/recommendations ignore enrichment and use deterministic fallback
- useful for A/B testing and rollback

Both flags can be enabled independently in local `.env`.

## Token and cost logging

Every LLM enrichment call must record:

- job id
- source job id
- model
- prompt tokens
- completion tokens
- total tokens
- estimated cost USD
- status
- started/completed time

If the OpenRouter response includes usage metadata, use it. If not, estimate tokens conservatively or store zero with `status_reason` explaining usage metadata unavailable.

## Monthly cost estimation

Add a simple admin/service helper or management command output that can show:

```text
Today enrichment calls: X
Today tokens: Y
Today estimated cost: $Z
Month enrichment calls: X
Month estimated cost: $Z
```

This can be implemented by aggregating `JobEnrichment` rows. No external billing API is required.

## Daily limit

Before enqueuing or executing enrichment, check how many enrichment attempts were started today.

If limit reached:

- do not enqueue more tasks
- report limit reached in management command
- do not fail tests or crash
