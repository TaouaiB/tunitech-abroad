# Phase 14D Boundaries

## Stack boundaries

Use only the project stack:

- Django
- Django ORM
- PostgreSQL
- Redis
- Celery
- Celery Beat if needed
- Django templates
- HTMX/Tailwind only where already used
- OpenRouter via existing/controlled LLM service layer

Forbidden:

- React
- Next.js
- Vue
- Angular frontend
- FastAPI
- SQLAlchemy
- MongoDB
- live LLM calls in views
- live France Travail calls in views

## Layering boundaries

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models do not call external APIs.
- Management commands call services/tasks.
- Templates render data only.

## Privacy/security boundaries

- Never expose raw CV text or CV file URLs.
- Never log secrets.
- Never print real OpenRouter keys.
- `.env.example` may document variable names only.
- `.env` must not be touched or committed.

## User-facing wording boundary

Do not show these on public/user pages:

```text
IT signal
non-IT
parser
skill_signal_quality
match_confidence
raw LLM
no_required_skills_extracted
low_confidence_job_skills
excluded_non_it
generic_only
validation_error
```

Allowed user-facing wording:

```text
Bon potentiel
Potentiel moyen
À vérifier
Faible alignement
Analyse limitée
Analyse CV non disponible
Compétences détectées
Compétences à renforcer
Points à vérifier
```

Admin/logs may show internal values.
