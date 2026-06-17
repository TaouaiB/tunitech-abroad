# Phase 14B Test Plan

## Automated tests

Required:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Focused tests may run during loops:

```bash
python manage.py test apps.core --settings=config.settings.local
python manage.py test apps.jobs --settings=config.settings.local
python manage.py test apps.matching --settings=config.settings.local
python manage.py test apps.recommendations --settings=config.settings.local
python manage.py test apps.cvs --settings=config.settings.local
python manage.py test apps.accounts --settings=config.settings.local
```

## Browser QA

Start server:

```bash
python manage.py runserver 127.0.0.1:8000 --settings=config.settings.local
```

Check pages:

- `/`
- `/jobs/`
- one `/jobs/<uuid>/`
- quick match POST/result
- `/accounts/login/`
- `/accounts/signup/`
- `/accounts/password/reset/`
- `/accounts/password/change/`
- `/dashboard/`
- `/dashboard/profile/`
- `/dashboard/cv/`
- `/dashboard/recommendations/`
- `/dashboard/matches/`
- one `/dashboard/matches/<uuid>/` if data exists
- `/dashboard/saved-jobs/`
- `/dashboard/email-preferences/`
- `/dashboard/account/`
- `/dashboard/settings/delete-account/`
- `/privacy/`
- `/terms/`
- invalid URL under `DEBUG=False`

## Mobile QA

Use browser device toolbar or narrow viewport. Check at 390px, 768px, and desktop.

No horizontal scroll. Forms usable. Cards stack. CTAs remain visible. Job cards are not cramped. Match score block is readable.

## Visual QA

For each main page, record:

- looks polished: yes/no
- broken layout: yes/no
- placeholder text: yes/no
- clear next action: yes/no
- mobile acceptable: yes/no

## Regression QA

Run grep checks from `regression_security_checks.md`.
