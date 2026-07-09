# Boundaries — Phase 14G

## Hard architecture rules

- Do not call OpenRouter/LLM from Django views.
- Do not call CV parsing services directly from upload views if parsing should be asynchronous.
- Views may create records, validate permissions, enqueue tasks, and render templates only.
- Celery tasks must call services.
- CV files must not be publicly exposed.
- Never use `cv.file.url` or direct file URLs in templates.
- Do not expose raw CV text to templates unless explicitly intended and protected.
- Do not use internal integer IDs in public/user-facing URLs.
- Use `public_id` UUIDs for CV status/detail routes.
- Do not use `CVUpload.all_objects` in user-facing views.
- Do not hard-delete CVs in normal user flows.

## Allowed implementation style

- Django templates.
- HTMX polling.
- Tailwind CSS classes.
- Minimal Alpine.js only if truly needed.
- Django messages for user feedback.
- Django admin actions for retry/fix visibility.

## Forbidden implementation style

- React, Vue, Angular, Next.js, SPA.
- FastAPI.
- SQLAlchemy.
- MongoDB.
- Public media URL for private CVs.
