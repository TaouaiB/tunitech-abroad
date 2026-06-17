# Phase 14B Preflight

Run before editing:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git branch --show-current
git status --short

docker compose up -d postgres redis || true

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Inspect templates:

```bash
find templates apps -path "*/templates/*" -type f | sort
find templates -type f | sort
grep -R "Phase 1 Note\|Lorem\|example.test\|future phase" templates apps -n || true
```

Inspect unsafe patterns:

```bash
grep -R "\.file.url\|cv.file.url\|raw_text" templates apps --exclude-dir="tests" -n || true
grep -R "FranceTravailClient\|search_offers" apps/jobs/views.py apps/jobs/services/search.py templates -n || true
grep -R "OpenRouter\|LLM" apps/*/views.py templates -n || true
```

Start server for browser QA:

```bash
python manage.py runserver 127.0.0.1:8000 --settings=config.settings.local
```

Preflight PASS means branch is `dev`, unrelated dirty files are understood, DB/cache are available, tests pass or known failures are documented, seeded jobs exist, and template inventory is understood.
