# Boundaries — Phase 14B.3R

## Stack boundaries

Use only:

- Django
- Django ORM
- PostgreSQL
- Redis/Celery if existing task behavior requires it
- Django templates
- Tailwind CSS
- HTMX
- minimal Alpine.js only if already present and justified

Forbidden:

- React
- Next.js
- Vue
- Angular
- Vite
- SPA routing
- Bootstrap
- Material UI
- paid UI kits
- npm icon packages
- lucide-react
- external icon JS packages

Use inline SVG icons only. Prefer Heroicons-style inline SVG copied into templates or local partials. Do not add a frontend build pipeline.

## Architecture boundaries

- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data. Do not move external/API calls into models.
- No OpenRouter/LLM call from Django views.
- No France Travail live API call during normal `/jobs/` user search.
- Public job search reads local PostgreSQL only.
- Public URLs use UUID `public_id`, not integer IDs.
- CV files stay private.
- `CVUpload.objects` must exclude soft-deleted CVs.
- `CVUpload.all_objects` is only for admin/privacy/internal tasks.
- LLM may extract/explain/suggest but may not decide final fit score.

## Privacy/security boundaries

Never expose:

- raw CV text
- private media URLs
- CV file URL
- uploaded file path
- OpenRouter key
- France Travail secret
- email app password
- OAuth client secret
- internal integer IDs in public UI

## Design boundaries

Do not copy the attached reference app code or stack. Use only visual inspiration.

Color usage rules:

- deep navy / near-black = main brand surface and major headings
- warm ivory = page background
- white = dense data cards
- lime = success/match/active accent only
- blue = links/focus only
- amber = warning only
- red = destructive only

No lime small text on white. No excessive glassmorphism on forms, CV data, jobs, or recommendations.

## PASS blockers

No PASS if:

- only one synthetic CV fixture passes
- extractor hardcodes the Aymen CV
- skill names like `Next.js` become `website_url`
- countries/employers/section titles become skills
- recommendations page says no jobs match when profile is incomplete
- `RecommendationRun` says success with zero recommendations for an incomplete profile
- profile shows 100% while empty/incomplete
- logged-in user sees “Créer un compte” CTA
- CV page shows only email/phone while parsed data has more fields
- agent report says browser QA but does not list pages and observations
- Baha has not manually approved Chrome pages
