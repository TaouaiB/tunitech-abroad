# Acceptance — Phase 14H-C

Phase 14H-C is accepted only if all are true:

## Static build
- `npm run css:build` succeeds.
- `static/css/app.css` exists and is non-empty.
- `templates/base.html` no longer references `https://cdn.tailwindcss.com`.
- `templates/base.html` loads compiled local CSS through Django staticfiles.
- `node_modules/` is not tracked.

## Architecture
- No React, Next.js, Angular, Vue, SPA, or frontend rewrite.
- No change to Django URL architecture.
- No change to matching, scoring, ingestion, CV parsing, LLM, or recommendation logic.
- No migrations are created.

## UI safety
- Main pages still render.
- Existing Tailwind classes continue to have CSS output.
- HTMX and Alpine behavior remains intact.
- The phase does not intentionally redesign the app.

## Security/privacy
- No CV file URLs exposed.
- No raw CV text exposed.
- No OpenRouter/LLM calls in views.
- No France Travail calls in views/templates.
- No secrets committed.

## Tests/checks
Required checks pass:
- `python manage.py check --settings=config.settings.local`
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`
- `npm run css:build`
- `python manage.py test apps.core apps.dashboard apps.cvs apps.jobs --settings=config.settings.local`
- `python manage.py test --settings=config.settings.local --parallel 1`
- `python manage.py collectstatic --dry-run --noinput --settings=config.settings.local`
- `git diff --check`
