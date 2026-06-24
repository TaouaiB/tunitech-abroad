# Phase 15L Final Pre-Deploy Checklist

## 1. Environment & Secrets
Before deploying, the following environment variables must be securely populated in the production `.env`. Do NOT commit real secrets to the repository.

- [ ] `SECRET_KEY` (Strong, random string)
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS=tuniatlas.com,www.tuniatlas.com`
- [ ] `CSRF_TRUSTED_ORIGINS=https://tuniatlas.com,https://www.tuniatlas.com`
- [ ] `DATABASE_URL`
- [ ] `REDIS_URL`

**Email Provider**:
- [ ] `EMAIL_HOST`
- [ ] `EMAIL_PORT`
- [ ] `EMAIL_HOST_USER`
- [ ] `EMAIL_HOST_PASSWORD`

**France Travail API**:
- [ ] `FRANCE_TRAVAIL_CLIENT_ID`
- [ ] `FRANCE_TRAVAIL_CLIENT_SECRET`

**OpenRouter (If Enabled Later)**:
- [ ] `OPENROUTER_API_KEY`

## 2. LLM & Automatic Spending Safety
Ensure automatic spending is disabled by verifying `.env` or settings:
- [ ] `LLM_ENABLED=True` (If True, extractions might run. Usually kept off initially)
- [ ] `CV_LLM_EXTRACTION_ENABLED=False`
- [ ] `JOB_ENRICHMENT_ENABLED=False`
- [ ] `JOB_ENRICHMENT_MAX_PER_INGESTION_RUN=0`
- [ ] `JOB_ENRICHMENT_DAILY_LIMIT=0`
- [ ] `OPENROUTER_CIRCUIT_BREAKER_ENABLED=True`
- [ ] `OPENROUTER_ENRICHMENT_RATE_LIMIT=1/m`

## 3. Data Privacy
- [ ] Private Media (CVs) correctly configured to be protected (not served publicly via Caddy without auth).
- [ ] `MEDIA_ROOT` is outside of the public static path.

## 4. Backups
- [ ] Verify script or service for DB dumps and media backup is ready.
- [ ] Verify destination bucket/storage box credentials.

## 5. Deployment Execution (Phase 15M)
- [ ] Server provisioned.
- [ ] DNS configured for `tuniatlas.com` and `www.tuniatlas.com`.
- [ ] Git repository pulled to server.
- [ ] Virtual environment set up and packages installed.
- [ ] Migrations applied.
- [ ] Static files collected.
- [ ] systemd services enabled and started.
- [ ] Caddy started and HTTPS certificates issued.
