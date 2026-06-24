# Production Environment Policy

This document outlines the mandatory environment variable configuration for the TuniTech Abroad production environment.

## Required Production Variables

The following variables must be set in the production environment to ensure security, stability, and cost control:

```env
# Django environment selector
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production

# Production domain and security
DJANGO_ALLOWED_HOSTS=tunitech-abroad.com,www.tunitech-abroad.com
CSRF_TRUSTED_ORIGINS=https://tunitech-abroad.com,https://www.tunitech-abroad.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# LLM Integration (MVP Mode)
# Keep LLM code available but disable automatic token spending by default.
LLM_ENABLED=True
CV_LLM_EXTRACTION_ENABLED=False
JOB_ENRICHMENT_ENABLED=False
JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=0
JOB_ENRICHMENT_DAILY_LIMIT=0
OPENROUTER_CIRCUIT_BREAKER_ENABLED=True
OPENROUTER_ENRICHMENT_RATE_LIMIT=1/m
```

## Policy Rules

1. **LLM usage**: User-facing search and matching must use local PostgreSQL and deterministic services. OpenRouter must not be called from views, templates, models, or admin displays during normal user flows.
2. **France Travail**: No live calls to France Travail API during public job searches. All searches read from the local database populated by the Celery ingestion tasks.
3. **Secrets Management**: Real secrets (`OPENROUTER_API_KEY`, `EMAIL_HOST_PASSWORD`, `FRANCE_TRAVAIL_CLIENT_SECRET`, database passwords) must only be injected via secure server environment variables or a tightly controlled `.env` file that is NEVER committed.

## `.env.example` Rule

The `.env.example` file in the repository must **always** use placeholders only. Never put real keys in it.
