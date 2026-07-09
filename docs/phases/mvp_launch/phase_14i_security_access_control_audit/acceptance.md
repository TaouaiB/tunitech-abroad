# Phase 14I Acceptance Criteria

## Required project outputs

```text
docs/audits/security_access_matrix.md
docs/audits/security_findings_14i.md
```

Both files must be specific and current. Placeholder audit text is a failure.

## Required automated checks

Run from repo root:

```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

If frontend/static files changed:

```bash
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
```

If Celery/tasks/settings changed:

```bash
python manage.py shell --settings=config.settings.local -c "from celery import current_app; print(len(current_app.tasks))"
```

## Required security greps

Run and document results:

```bash
grep -R "cdn.tailwindcss.com" templates config static -n || true
grep -R "React\|Next.js\|next/\|createRoot\|vue\|angular\|Vite" package.json templates static apps -n 2>/dev/null || true
grep -R "FranceTravailClient\|france_travail" apps/*/views.py templates -n 2>/dev/null || true
grep -R "OpenRouterClient\|OPENROUTER\|run_llm\|llm" apps/*/views.py templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|upload.file.url\|raw_text\|extracted_text" templates apps -n 2>/dev/null || true
grep -R "<int:" apps templates config -n 2>/dev/null || true
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

Every non-empty grep result must be documented as:

```text
SAFE — with reason
FIXED — with file/commit context
FOLLOW_UP — with risk and owner
```

## Required test coverage

Automated tests must cover at least:

```text
anonymous blocked from private dashboard routes
authenticated user allowed on own private routes
user A blocked from user B CV status/delete
user A blocked from user B match detail/explain
user A blocked from user B saved-job mutation
user A blocked from user B email-preference mutation if route/object accepts identifiers
user A blocked from user B recommendation refresh if route/object accepts identifiers
normal user blocked from admin
public jobs and job detail use UUID public_id
integer-ID routes for public jobs/matches/CVs do not exist or 404
CV pages/templates do not expose direct file URL
raw CV text is not rendered in user-facing templates
GET requests do not mutate delete/save/refresh/explain/preference/account-deletion state
no OpenRouter/France Travail calls from views/templates
```

## Manual browser/admin signoff required

Baha must manually verify with Chrome/admin using:

```text
manual_browser_security_signoff.md
```

Until that is complete, final verdict cannot be PASS.

Allowed pre-signoff verdict:

```text
FINAL_VERDICT: BLOCKED_HUMAN_SECURITY_SIGNOFF
```

Fail conditions:

```text
Any automated check fails.
Any private user object can be accessed by another user.
Any direct CV file URL is exposed to normal users.
Any raw CV text is rendered to users.
Any public route uses internal integer IDs for jobs/matches/CVs.
Any normal public job search calls France Travail live.
Any view calls OpenRouter/LLM directly.
Any real secret appears in diff/docs/tests/reports/logs.
Agent starts Phase 14J or adds unrelated features.
```
