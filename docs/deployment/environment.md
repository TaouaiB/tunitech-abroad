# Deployment Environment Setup (Phase 14 Prep)

This document outlines the environment configuration required for deploying TuniTech Abroad to production.

## Environment Variables

The following environment variables must be securely configured in the production environment (e.g., via a `.env` file, hosting provider secrets, or orchestration secrets). **Do not commit these values to version control.**

### Core Settings
- `DJANGO_ENV=production`
- `DJANGO_SETTINGS_MODULE=config.settings.production`
- `DJANGO_SECRET_KEY` (Must be a secure, random string)
- `DJANGO_DEBUG=False` (Must be strictly `False` in production)
- `DJANGO_ALLOWED_HOSTS` (Comma-separated list, e.g., `tunitech-abroad.com,www.tunitech-abroad.com`)
- `SITE_URL` (e.g., `https://tunitech-abroad.com`)
- `CSRF_TRUSTED_ORIGINS` (e.g., `https://tunitech-abroad.com`)

### Database
- `DATABASE_URL` (PostgreSQL connection string)
  - Or alternatively: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`

### Redis and Celery
- `REDIS_URL` (e.g., `redis://redis:6379/0`)
- `CELERY_BROKER_URL` (usually same as `REDIS_URL`)
- `CELERY_RESULT_BACKEND` (usually same as `REDIS_URL`)

### Email Configuration
- `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST` (e.g., `smtp.sendgrid.net`)
- `EMAIL_PORT` (e.g., `587`)
- `EMAIL_USE_TLS=True`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL` (e.g., `TuniTech Abroad <noreply@tunitech-abroad.com>`)

### API Integrations
- `LLM_ENABLED=True`
- `OPENROUTER_API_KEY`
- `OPENROUTER_DEFAULT_MODEL`
- `FRANCE_TRAVAIL_CLIENT_ID`
- `FRANCE_TRAVAIL_CLIENT_SECRET`

### OAuth Providers
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`

## OAuth Redirect URL Updates

Before full deployment, ensure the OAuth callbacks are registered in your Google and GitHub developer consoles.
The redirect URIs should look like:
- `https://your-domain.com/accounts/google/login/callback/`
- `https://your-domain.com/accounts/github/login/callback/`

## Media Storage
- `MAX_CV_UPLOAD_SIZE_MB` (Optional override, defaults to 5)
- Ensure the production environment has a persistent volume attached for `private_media/` if not using S3/object storage.
