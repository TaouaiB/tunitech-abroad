# Regression and Security Checks

Run after implementation:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.core apps.jobs apps.recommendations apps.privacy --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

Secret scan:

```bash
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

Architecture/security greps:

```bash
grep -R "FranceTravailClient\|france_travail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
grep -R "CELERY_BEAT_SCHEDULE = {}" config -n || true
```

Expected:

- No France Travail client usage in views/templates.
- No OpenRouter usage in views/templates.
- No CV file URL/raw text leaks.
- `CELERY_BEAT_SCHEDULE = {}` should no longer appear.
