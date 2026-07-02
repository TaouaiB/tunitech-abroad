# Phase 16H Rules Lock — TuniAtlas UI/UX Overhaul

## Status

This document is binding for Phase 16H. It overrides older prototype handoff notes when there is a conflict.

Phase 16H is a prototype port and product-state integration phase, not a creative redesign phase.

## Core instruction to agents

You are not a UI/UX designer in this phase. You are a Django template integrator.

Your job is to port the approved v16 prototype into existing Django templates while preserving backend behavior and architecture.

Do not invent new colors, layouts, sections, animations, routes, icons, dashboards, data models, matching algorithms, recommendation logic, or product flows.

If the prototype conflicts with this rules lock, follow this rules lock.

If backend behavior conflicts with static prototype assumptions, preserve backend behavior and adapt the template state.

## Locked stack and architecture

Use only the existing project stack:

- Django templates
- Django ORM
- PostgreSQL
- Redis
- Celery
- django-allauth
- HTMX
- Tailwind CSS
- Alpine.js only where needed

Do not introduce:

- React
- Next.js
- Vue
- Angular
- FastAPI
- SPA architecture
- MongoDB
- SQLAlchemy
- new frontend build system

Architecture rules:

- Views stay thin.
- Business logic belongs in services.
- Celery tasks call services only.
- Models do not call external APIs.
- No OpenRouter/LLM calls from Django views.
- No France Travail live API calls during normal user job search.
- User job search reads local PostgreSQL only.
- Public URLs use UUID `public_id`, never internal integer IDs.
- CV files are private and must not be publicly exposed.
- Matching final score remains deterministic. LLM must not decide fit score.

## Prototype source

Prototype files are expected at:

```text
docs/design/phase_16h/prototype/
```

Reference files are expected at:

```text
docs/design/phase_16h/handoff/
docs/design/phase_16h/agent_plan/
```

These files are implementation references, not active website routes.

## Visual fidelity rules

Preserve the approved v16 visual system.

Do not:

- create a new color palette
- replace the visual identity
- change prototype card style
- change button hierarchy
- change spacing scale unless required to fit existing Tailwind utilities
- add gradients unless already present in prototype
- invent icons
- add emoji
- add extra explanatory text
- rename navigation labels unless locked copy requires it
- create a new dashboard/home page
- expose saved-job UI to anonymous users
- add fake data in production templates

Implementation guidance:

- Port prototype structure into Django templates.
- Reuse existing `.tta-*` classes when they match the prototype.
- Add small reusable `.tta-*` classes in `static/src/css/app.css` only when needed.
- Do not edit compiled `static/css/app.css` directly except through the approved Tailwind build process.
- Do not put large style blocks inside templates.

## Page visibility and routing rules

### Landing/page entry

The jobs/search experience is the primary public entry point.

No separate visible dashboard/home page should be added as a new product landing experience.

Existing backend dashboard routes may remain if they are used for recommendations, saved jobs, settings, profile, account, or email preferences.

### Logged-out header

Logged-out users see:

- Jobs
- Recommendations -> redirects to login/signup/auth with `next=/dashboard/recommendations/` or the correct recommendations route
- About
- Sign in / Get started

Logged-out users must not see:

- Saved
- Saved Jobs box/link
- Save buttons on job cards or job detail
- Profile
- Settings
- Sign out

### Logged-in header

Logged-in users see:

- Jobs
- Recommendations
- Saved
- Profile
- Settings
- About
- Sign out

Account dropdown, if used, contains:

- Profile
- Settings
- Sign out

No "More" menu. No unnecessary arrows.

## Jobs and saved jobs rules

Anonymous users:

- can browse jobs
- can open job detail pages
- do not see Save buttons
- do not see Saved links or boxes
- can click Recommendations in nav and be sent to auth with next URL

Logged-in users:

- can see Save buttons
- can save/unsave jobs using existing backend/HTMX endpoints
- can see Saved Jobs
- can open Recommendations normally

Do not create new saved-job behavior if existing endpoints already satisfy the requirement.

## Job detail match CTA matrix

Job detail CTA is dynamic.

Use the correct state instead of blindly showing "View score".

```text
Logged out:
- CTA to sign in / check recommendations / get match guidance.

Logged in, no profile/CV:
- Complete profile / Upload CV.

Logged in, profile/CV exists, no match result:
- Check match / Calculate match.

Logged in, match exists:
- View score.

Logged in, match failed/stale:
- Retry match / Refresh match.
```

Do not remove anonymous quick-match backend logic during this phase. UI may hide it, but backend logic remains unless a later phase explicitly removes it.

## Profile setup and password step rules

The password step is based on usable password state, not a permanent OAuth flag.

Use:

```python
not request.user.has_usable_password()
```

Rules:

- OAuth user with no password: show Set password -> CV -> Profile.
- Email/password signup user: skip Set password, show CV -> Profile.
- Returning user with no usable password: Set password remains first required step.
- OAuth user who later sets password: do not show Set password again.

Do not hardcode "OAuth users always see Set Password".

## Email verification banner rules

Show email confirmation banner only when:

- user is authenticated
- primary email is not verified

Hide banner when:

- anonymous user
- user email is verified
- user logged in through trusted OAuth and provider email is treated as verified

Use django-allauth email verification state. Do not invent custom verification tokens.

Resend confirmation UI may be added, but it must use allauth-compatible behavior or a thin wrapper around allauth behavior.

Resend rules:

- compact success state
- compact failure state
- no raw backend/provider exception text in UI or logs
- spam/rate-limit/cooldown protection if a custom endpoint is added

## Password policy rule

Backend password policy wins.

Do not weaken password validators to match prototype copy.

If prototype says "minimum 6" but backend requires a stronger password, update UI copy and validation hints to match backend.

## About/contact rules

The About page contact form must be real, not fake.

Minimum backend behavior:

- `/about/` route
- Django form with CSRF
- `ContactMessage` model or equivalent
- contact service layer
- DB record created first
- Celery task sends email after DB record exists
- safe success/failure messages
- no raw exception details in UI or logs
- anti-spam protection such as honeypot and/or rate limiting
- tests

Do not place contact business logic directly in the view.

## Notifications/states rule

`notifications.html`, `empty-states.html`, `loading-states.html`, and `failure-states.html` are component/state references only.

Phase 16H includes:

- empty states
- loading skeletons
- failure/error states
- success/error/warning/info toasts
- email confirmation banner
- contact form success/failure states
- CV upload pending/processing/failure states
- recommendations empty/loading/failure states
- saved jobs empty state
- job search no-results state
- match unavailable/failed/stale state

Phase 16H does not include:

- notification bell
- notifications dropdown
- notification feed page
- Notification model
- mark read/unread
- real-time notifications
- per-user in-app alerts

Existing email notification/preferences/unsubscribe backend stays.

## Country scope rule

France is locked/default for now.

Do not add fake countries.

Do not overpromise other countries.

Keep backend flexible for future countries.

## Language rule

Phase 16H keeps French as the primary UI language.

Do not implement prototype-style JS/localStorage translation.

Do not start a full Django i18n rollout in the same UI-port batch unless explicitly approved later.

Templates should be written in a way that can be internationalized later, but Phase 16H does not need full EN/FR switching.

## Copy rules

Use prototype copy where it matches this rules lock.

Fix incorrect copy:

- English: use "Apply", not "Postulate".
- French: "Postuler" is acceptable.

Avoid misleading AI wording:

- Do not say AI decides the final match score.
- Do not imply AI makes the final recommendation score.
- Deterministic matching/recommendation logic remains the source of scoring truth.

## Forbidden phase creep

Do not implement:

- new notification center
- public profile pages
- new analytics dashboards beyond existing Phase 16G admin dashboards
- new matching algorithm
- new recommendation algorithm
- new LLM features
- new countries
- new paid plans/pricing
- new job application tracking system
- production deployment

## Agent reporting requirement

Every implementation batch must report:

- files changed
- backend behavior preserved
- prototype deviations, if any
- tests run with exact results
- screenshots/manual pages checked, if any
- blocked questions
- confirmation that no forbidden features were added
