# Scope — Phase 14H-C

## In scope
- Remove `<script src="https://cdn.tailwindcss.com"></script>` from `templates/base.html`.
- Add a real Tailwind CLI build pipeline.
- Add or update static source/output folders for CSS.
- Add npm scripts for build/watch.
- Configure Tailwind content scanning for:
  - `templates/**/*.html`
  - `apps/**/*.py`
  - `apps/**/*.html` if applicable
- Generate a minified CSS output file under project static assets.
- Ensure Django can discover the compiled CSS through staticfiles.
- Add docs for local development and deployment static build.
- Add tests/checks for no Tailwind CDN and correct local CSS reference.

## Out of scope
- Redesigning pages.
- Rewriting templates.
- Replacing HTMX or Alpine.
- Moving to React/Next/Vite app architecture.
- Celery Beat changes.
- France Travail ingestion changes.
- CV parsing changes.
- LLM changes.
- Matching/recommendation scoring changes.
- Production deploy.
- Domain/email/hosting work.
