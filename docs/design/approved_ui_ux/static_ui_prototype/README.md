# TuniTech Abroad Static UI Prototype

Open `prototype-map.html` first.

This is a static visual prototype, not Django code. It is meant to validate the UI direction before Phase 14K implementation.

Included frames:
- Home
- Jobs list
- Job detail
- CV checker
- Dashboard
- Recommendations
- Profile
- CV management
- Saved jobs
- Match detail
- Match history
- Email preferences
- Account/security
- Login
- Signup
- Privacy
- Terms

Rules reflected:
- Adaptive light/dark mode through `prefers-color-scheme`
- No forced black-only design
- No external font dependency
- No React/Next/Vue/SPA
- No backend behavior implemented
- French UX copy direction
- Cards, badges, buttons, filters, progress, score ring, dropzone, empty states

Use this as visual reference. Do not copy routes blindly into Django without preserving CSRF, HTMX attributes, allauth tags, public_id, and existing service boundaries.


## v2 additions

This v2 prototype integrates the final UI polish recommendations:

- Toast container and toast states with auto-dismiss behavior.
- Skeleton loading cards for job list/filter perceived performance.
- Active/touch feedback for buttons and interactive cards.
- Branded 404 and 500 error pages.
- `component-states.html` for reviewing micro-interactions before Django implementation.

These additions remain visual/static prototype work only. They do not introduce React, Next.js, SPA behavior, backend changes, or new dependencies.
