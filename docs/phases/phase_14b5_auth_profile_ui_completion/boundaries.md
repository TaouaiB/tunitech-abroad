# Hard Boundaries

## Stack boundaries

Allowed:
- Django
- Django ORM
- django-allauth
- Django templates
- HTMX
- Tailwind CSS
- tiny Alpine.js only if already used and necessary

Forbidden:
- React
- Next.js
- Vue
- Angular
- Vite frontend app
- SPA architecture
- FastAPI
- MongoDB
- SQLAlchemy
- Bootstrap/Material UI rewrites
- lucide-react or any React icon package

Use inline SVG icons only. Heroicons-style inline SVG is acceptable.

## Architecture boundaries

- Views stay thin.
- Business logic goes into services.
- Models must not call external APIs.
- Celery tasks call services only.
- No OpenRouter/LLM calls from views.
- No France Travail live calls from public search.
- Public job search reads local PostgreSQL only.
- Public routes use UUID public IDs.
- CV files remain private.
- Do not expose raw CV text in templates.
- Do not expose CV file URLs.

## Auth boundaries

- Use django-allauth for OAuth/login/email mechanics.
- Do not implement custom OAuth token exchange manually.
- Do not store OAuth access tokens in `CandidateProfile`.
- Do not log provider tokens or raw provider payloads.
- Do not bypass email security by unsafe account merging.
- Duplicate accounts must be handled carefully through allauth and verified email matching only where safe.

## Product boundaries

- France-only MVP remains.
- Remove `target_country` from UI, but do not remove the DB field unless explicitly approved in a future cleanup.
- Do not add Belgium/Canada/Luxembourg user choices now.
- Do not promise jobs, visas, relocation, or acceptance.

## PASS blockers

Fail the phase if any of these are true:

- `/accounts/3rdparty/` is unstyled.
- `/accounts/password/set/` is unstyled.
- Any auth email says `example.test`.
- Any visible auth/account page has default allauth styling.
- Google/GitHub connection status is not visible in account settings.
- OAuth-created user has no way to set a password.
- Profile/recommendations disagree about missing fields.
- Recommendation page lists phone/location missing while DB has phone/location.
- Target country is visible to the user.
- CV raw text or CV file URL appears in rendered HTML.
- Agent claims final PASS before Baha manual Chrome signoff.
