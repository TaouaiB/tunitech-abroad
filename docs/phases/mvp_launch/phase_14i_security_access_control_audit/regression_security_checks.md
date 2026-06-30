# Phase 14I Regression and Security Checks

## Mandatory checks

```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

## Static/frontend checks if touched

```bash
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
```

## Celery checks if touched

```bash
python manage.py shell --settings=config.settings.local -c "from celery import current_app; print(sorted([name for name in current_app.tasks.keys() if name.startswith('apps.')])[:50])"
```

## Security greps

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|france_travail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

## Manual review targets

Inspect these manually even if tests pass:

```text
config/urls.py
apps/*/urls.py
apps/*/views.py
apps/*/services/**/*.py
apps/*/tasks.py
apps/*/admin.py
templates/**/*.html
settings files
new tests
new audit docs
```

## Common blockers

```text
view filters by object public_id but not by user/owner
HTMX partial endpoint lacks login_required
POST endpoint accepts object id from form and mutates without owner check
GET endpoint mutates state
admin list_display exposes raw_text or tokens
CV template uses file.url
view imports OpenRouter/FranceTravail client
public URL pattern uses <int:pk>
.env or real secrets appear in diff
```
