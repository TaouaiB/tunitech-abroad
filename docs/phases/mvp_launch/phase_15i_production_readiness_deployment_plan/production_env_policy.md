# Production Environment Policy — TuniTech Abroad

This document belongs under `docs/deployment/production_env_policy.md` once implemented.

## Core rule

Production uses real secrets only in `.env` on the server. The repository stores placeholders only.

## LLM spend control

For MVP launch, keep LLM code available but disable automatic token spending:

```env
LLM_ENABLED=True
CV_LLM_EXTRACTION_ENABLED=False
JOB_ENRICHMENT_ENABLED=False
JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=0
JOB_ENRICHMENT_DAILY_LIMIT=0
OPENROUTER_CIRCUIT_BREAKER_ENABLED=True
OPENROUTER_ENRICHMENT_RATE_LIMIT=1/m
```

## Static/private media

Whitenoise may serve static assets. It must not serve CV/private media.

## Forbidden

Never commit real values for:

- `SECRET_KEY`
- `OPENROUTER_API_KEY`
- `FRANCE_TRAVAIL_CLIENT_SECRET`
- `EMAIL_HOST_PASSWORD`
- `GOOGLE_CLIENT_SECRET`
- `GITHUB_CLIENT_SECRET`
- database password
- Redis password, if any
