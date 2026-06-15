# Deployment Checklist

Follow these steps for a successful production deployment of TuniTech Abroad.

## 1. Pre-Deployment (Backup & Rollback Prep)
- [ ] **Database Backup**: Take a snapshot or pg_dump of the production database before applying any migrations.
- [ ] **Media Backup**: Ensure `private_media/` volume is backed up.
- [ ] **Rollback Plan**: Note the current stable commit hash. If deployment fails, be prepared to revert to this commit and restore the DB backup if migrations are destructive.

## 2. Infrastructure & Environment
- [ ] Provision PostgreSQL and Redis instances.
- [ ] Configure all required environment variables as defined in `environment.md` (no secrets in source control).
- [ ] Ensure the application runs with `DJANGO_SETTINGS_MODULE=config.settings.production` and `DJANGO_DEBUG=False`.

## 3. Application Setup
- [ ] Run database migrations:
  ```bash
  python manage.py migrate
  ```
- [ ] Collect static files (Whitenoise will handle serving them):
  ```bash
  python manage.py collectstatic --noinput
  ```
- [ ] Create a superuser (if not already done):
  ```bash
  python manage.py createsuperuser
  ```

## 4. Background Workers
- [ ] Start the Celery worker process:
  ```bash
  celery -A config worker -l INFO
  ```
- [ ] Start the Celery beat process (for scheduled tasks):
  ```bash
  celery -A config beat -l INFO
  ```

## 5. Security & Privacy Checks
- [ ] **Private Media Verification**: Verify that uploaded CVs in `private_media/` cannot be accessed via public static/media URLs (e.g., trying to access `/media/cvs/filename.pdf` should fail or return 404/403).
- [ ] **Email Provider Check**: Verify SMTP credentials are valid by testing a signup or password reset flow.

## 6. Post-Deployment Verification
- [ ] Execute the manual test plan (`manual_test_plan.md`) to verify critical workflows.
- [ ] Check the `/health/` endpoint to ensure DB and Redis are connected.
