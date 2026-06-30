# Test Plan

## Required automated checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
python manage.py test apps.core apps.accounts apps.dashboard apps.cvs apps.jobs apps.matching apps.recommendations apps.privacy --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

## Optional targeted checks

```bash
python manage.py cv_worker_check --settings=config.settings.local
python manage.py shell --settings=config.settings.local -c "from django.conf import settings; print(settings.CELERY_BEAT_SCHEDULE.keys())"
```

## Browser pages

Hard refresh after Tailwind build:

```text
/
/jobs/
/dashboard/
/dashboard/profile/
/dashboard/cv/
/dashboard/recommendations/
/dashboard/account/connections/
/dashboard/email-preferences/ or actual email preferences URL
```

## Manual status labels

Use:

```text
PASS_VISUAL
FAIL_VISUAL
NOT_TESTED
BLOCKED_ENV
```

The final phase verdict still must be `BLOCKED_HUMAN_VISUAL_SIGNOFF` unless a blocker is found.
