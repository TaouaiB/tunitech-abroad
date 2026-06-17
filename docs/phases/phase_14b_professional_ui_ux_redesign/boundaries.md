# Phase 14B Boundaries

## Stack boundaries

Allowed:

- Django templates
- Tailwind CSS
- HTMX
- minimal Alpine.js only where already present or clearly justified

Forbidden:

- React
- Next.js
- Vue
- Angular
- SPA architecture
- FastAPI
- MongoDB
- SQLAlchemy
- Bootstrap
- Material UI
- paid UI kits
- heavy JS dependencies
- CDN dependence for core app behavior

## Architecture boundaries

- Views stay thin.
- Services own business logic.
- Celery tasks call services only.
- Models store data only.
- No OpenRouter calls from Django views.
- No France Travail calls from `/jobs/` or normal user search.
- Public job search must read local PostgreSQL only.
- Public routes must use UUID `public_id`, never internal integer IDs.
- CV files remain private.
- `CVUpload.objects` must exclude soft-deleted CVs.
- `CVUpload.all_objects` is reserved for admin/privacy/deletion/internal tasks.

## Privacy/security boundaries

Do not expose:

- `.env`
- API keys
- OAuth secrets
- OpenRouter keys
- France Travail client secret
- access tokens
- bearer tokens
- private CV file URLs
- full raw CV text
- stack traces
- URLconf dump in production-like 404
- admin-only data in public templates

## Product boundaries

Do not claim:

- guaranteed employment
- guaranteed visa/relocation
- legal immigration advice
- AI decides the final score
- AI ranks all jobs by itself
- production scale that does not exist
- paid partnerships that do not exist

## Git/deployment boundaries

- Do not commit.
- Do not push.
- Do not deploy.
- Do not modify Render configuration.
- Do not use `git add .`.
- Do not stage accidental screenshots, PDFs, or temporary files.

## External API boundaries

This UI phase should not run real external API calls unless existing tests already do so.

- Do not run real OpenRouter calls for visual redesign.
- Do not run France Travail sync unless explicitly required by acceptance and already controlled.
- Use local seeded data through `seed_demo_data`.
