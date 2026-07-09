# TuniAtlas v1.1 Global Agent Rules

These rules apply to Gemini and Codex for every post-launch phase.

## Stack boundary

Use only:

```text
Django
Django ORM
PostgreSQL
Redis
Celery
Celery Beat
django-allauth
Django templates
HTMX
Tailwind CSS
Alpine.js only where needed
OpenRouter only for controlled optional LLM
PyMuPDF/pdfplumber for CV text extraction
```

Do not use:

```text
React
Next.js
Angular
FastAPI
MongoDB
SQLAlchemy
SPA architecture
```

## Architecture boundary

```text
Views stay thin.
Business logic goes in services.
Celery tasks call services only.
Models store data and do not call external APIs.
No OpenRouter/LLM calls from Django views.
No France Travail live API calls during normal user job search.
User job search reads local PostgreSQL only.
Public URLs use UUID public_id, never internal integer IDs.
CV files are private and must not be publicly exposed.
CVUpload.objects excludes soft-deleted CVs.
CVUpload.all_objects is only for admin/privacy/deletion/internal tasks.
LLM can extract, explain, and suggest, but cannot decide the final fit score.
```

## Solo-admin boundary

Baha is currently the only admin/operator/developer/designer. Build owner/superuser dashboards and logs. Do not build enterprise RBAC, multi-staff workflows, reviewer roles, organization accounts, or fake team features.

## Secrets boundary

```text
Never print secrets.
Never commit .env.
Never log OAuth tokens, API keys, SMTP passwords, France Travail credentials, OpenRouter keys, or raw CV text.
Agents may update .env.example with variable names only.
```

## ML boundary

Do not build ML/DL now unless explicitly requested in a future approved phase. Build ML-ready taxonomy, labels, audit corpus, correction tables, and export commands. Future ML predicts canonical Skill IDs + confidence and still feeds deterministic scoring.

## Git boundary

Work on dev or a feature branch. Do not code directly on main. One phase at a time. Do not start the next phase.

## v1.1 additional execution rules from senior review

```text
Security/correctness tickets inside a phase must be completed before product-quality tickets when both exist.
Codex must not silently change Gemini ticket intent; intent-changing fixes require explicit report and senior review.
Diagnostics services must follow a shared structured output convention.
Phase 16D must use the canonical skill seed/alias artifact instead of inventing taxonomy content from scratch.
Phase 16E must produce per-skill confidence data that Phase 16F consumes.
Phase 16B freshness changes must include a fast active-job-count regression check before and after deployment.
```
