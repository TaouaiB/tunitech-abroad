# Scope

## In scope

- Verify local environment health: PostgreSQL, Redis, Django, Celery worker, optional Celery Beat.
- Verify Tailwind compiled CSS still styles key pages.
- Verify anonymous flows: landing page, jobs list, job detail, filters.
- Verify authenticated flows: login/signup, dashboard, profile, CV upload, CV parse status, matching, recommendations, saved jobs, email preferences.
- Verify job ingestion + normalization + enrichment queue behavior with a small safe run.
- Verify privacy/account deletion with a disposable user only.
- Fix small blocking bugs discovered during validation.
- Add/adjust tests only when a bug is fixed or a critical regression gap is found.
- Produce an E2E validation report.

## Out of scope

- Deployment.
- Tailwind redesign.
- New product features.
- New countries.
- Employer/recruiter portal.
- Payment/premium features.
- React/Next.js/Vue/Angular.
- FastAPI/MongoDB/SQLAlchemy.
- LLM final scoring.
- Live France Travail calls during public job search.
- Large UI redesign.
- Changing architecture.
