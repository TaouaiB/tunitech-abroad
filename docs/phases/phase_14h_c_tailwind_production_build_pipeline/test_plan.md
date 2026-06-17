# Test Plan — Phase 14H-C

Run after implementation:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

npm run css:build

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.core apps.dashboard apps.cvs apps.jobs --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Manual browser smoke test:

```bash
python manage.py runserver --settings=config.settings.local
```

Open and visually inspect:
- `/`
- `/jobs/`
- `/dashboard/`
- `/dashboard/cv/`
- `/dashboard/recommendations/`
- `/dashboard/profile/`

Expected:
- Pages are styled, not plain unstyled HTML.
- Layout is not broken.
- Buttons/cards/spacing still resemble previous UI.
- HTMX polling and Alpine upload UX still work.
