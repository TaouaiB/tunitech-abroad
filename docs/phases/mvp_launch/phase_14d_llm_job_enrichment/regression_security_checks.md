# Regression and Security Checks

Run from repo root.

## Django checks

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.matching apps.recommendations apps.llm --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## Secret diff check

```bash
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|Bearer |EMAIL_HOST_PASSWORD|SECRET_KEY" || echo "OK: no obvious secrets in diff"
```

If grep returns only environment variable names in `.env.example` or safe settings references, report as reviewed. If any real value appears, FAIL.

## No LLM calls in views/templates

```bash
grep -R "OpenRouter\|OPENROUTER\|llm\|LLM\|job_enrichment\|enrich_job" apps -n --include='*.py' | grep -i view || true
```

Also check view packages:

```bash
find apps -path '*/views/*.py' -o -name 'views.py' | xargs grep -n "OpenRouter\|OPENROUTER\|llm\|LLM\|job_enrichment\|enrich_job" 2>/dev/null || true
```

Expected: no view-triggered LLM calls.

## No live France Travail calls in user paths

```bash
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/jobs apps/matching apps/recommendations apps/dashboard templates -n 2>/dev/null || true
```

Allowed only in ingestion clients/management commands/tasks. Public views must not call live France Travail.

## Raw private data check

```bash
grep -R "raw_text\|file.url\|cv.file.url" templates apps -n 2>/dev/null || true
```

Expected: no template exposes raw CV text or private CV file URL.

## Raw internal flag leak check

```bash
grep -R "non-IT\|IT signal\|skill_signal_quality\|match_confidence\|generic_only\|excluded_non_it\|no_required_skills_extracted\|low_confidence_job_skills\|validation_error\|raw LLM" templates -n 2>/dev/null || true
```

Expected: no user-facing template renders these internal terms. Admin/internal templates may be reviewed separately.

## Frontend stack check

```bash
grep -R "nextjs\|vite\|lucide-react\|material-ui\|bootstrap" package.json templates static apps -n 2>/dev/null || true
```

Expected: no new forbidden frontend stack. Skill names like React/Angular/Vue inside job data/tests are allowed.

## Root junk cleanup

```bash
find . -path ./.venv -prune -o -name '*.pyc' -print
find . -path ./.venv -prune -o -name '__pycache__' -print
find . -maxdepth 2 \( -name 'scratch_*.py' -o -name 'verify.py' -o -name 'proof.py' \) -print
```

Expected: no project-local junk files outside `.venv`.
