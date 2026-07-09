# Boundaries

Strict rules:

- Do not commit.
- Do not deploy.
- Do not start Phase 14H-C or Phase 14I.
- Do not start Tailwind build.
- Do not Dockerize Django/Celery.
- Do not add React/Next/FastAPI/MongoDB/SQLAlchemy.
- Do not call France Travail from public views/search.
- Do not call OpenRouter/LLM from Django views.
- Do not let LLM decide final match scores.
- Do not expose CV files or raw CV text.
- Do not use internal integer IDs in public URLs.
- Do not use `CVUpload.all_objects` outside admin/privacy/deletion/internal tasks.

Operational limits:

- Periodic ingestion must respect existing admin/config limits.
- Periodic enrichment must respect run and daily LLM budget controls.
- Email scheduling must be opt-in and idempotent if included.
- Celery Beat must be optional locally; normal Django server must still start without Beat running.
