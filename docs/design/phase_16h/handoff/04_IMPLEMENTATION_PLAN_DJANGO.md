# Django Implementation Plan

This plan assumes the current TuniAtlas app uses Django + HTMX + Tailwind + PostgreSQL + Redis + Celery, and that the final prototype v16 is currently standalone HTML/CSS/JS.

## Guiding rule

Implement v16 by componentizing it. Do not redesign.

## Phase 1 — Inspect and map prototype

1. Unzip `tuniatlas_full_prototype_v16.zip`.
2. Open every HTML file.
3. Identify shared blocks:
   - header
   - account menu
   - theme toggle
   - language toggle
   - email activation banner
   - footer
   - job card
   - recommendation card
   - saved job card
   - form fields
   - buttons
   - pills/skills
   - score ring
   - mobile drawers
   - accordions
   - sticky mobile action bars
   - empty/loading/failure cards
4. Map each page to existing Django routes and models.

Deliverable:

- Component inventory.
- Route mapping.
- Data mapping.

## Phase 2 — Create base template and shared partials

Create/adjust templates:

- `base.html`
- `_header.html`
- `_footer.html`
- `_account_alert.html`
- `_theme_toggle.html`
- `_language_toggle.html`
- `_mobile_nav.html`
- `_toast.html`
- `_button.html` if useful
- `_job_card.html`
- `_score_ring.html`
- `_skill_pills.html`
- `_empty_state.html`
- `_loading_state.html`
- `_failure_state.html`

Implementation notes:

- Keep CSS tokens from v16.
- If using Tailwind, either preserve classes through utility mapping or keep a compiled custom stylesheet based on the prototype tokens.
- Do not convert styling in a way that changes the visual result.

## Phase 3 — Implement pages one by one

Recommended order:

1. Base/header/footer/theme/language.
2. Jobs page.
3. Job detail.
4. Auth.
5. Profile stepper.
6. Recommendations.
7. Saved jobs.
8. Match score.
9. Settings.
10. About/contact.
11. Empty/loading/failure pages or partials.
12. 404/500.

## Phase 4 — Jobs page implementation

Backend:

- Query active jobs only.
- Apply filters through GET params.
- Save/unsave requires auth.
- Anonymous save click should redirect to auth or prompt sign-in.

Template:

- Preserve v16 card layout.
- Save button only on job cards.
- No postulate button on cards.
- France-only disabled/checked filter.
- Mobile filter drawer.
- Collapsible search/stats on mobile.

## Phase 5 — Job detail implementation

Backend:

- Load active job by slug/id.
- Load saved state for authenticated user.
- Load match score if available.
- External apply URL from source.

Template:

- Postulate action goes to external source.
- Save action.
- View score link.
- Sticky mobile action bar.
- Do not include Missions/Profile extra blocks that were removed from final prototype.

## Phase 6 — Auth implementation

Backend:

- Login.
- Signup.
- Google OAuth.
- GitHub OAuth.
- Email verification flow.
- Password min length 6 if this is accepted security policy; otherwise align backend/password validators carefully while preserving UI copy.

Frontend:

- Live email validation.
- Live password validation.
- Live verify password validation.
- Remove unnecessary wording like “or email”.

## Phase 7 — Profile stepper implementation

Backend:

- Detect whether user has usable password.
- If no password, first required step is Set password.
- CV upload endpoint.
- CV parser/Celery task.
- Profile save endpoint.
- Recommendation trigger.

Frontend:

- Step 1: Set password.
- Step 2: CV.
- Step 3: Profile.
- Mobile compact stepper.
- Sticky bottom navigation on mobile.
- No duplicate buttons on mobile.
- No extra helper wording.

## Phase 8 — Match/recommendation implementation

Backend:

- Reuse existing recommendation/matching services if present.
- Rule-based final scoring if that is existing policy.
- LLM only for CV/skills/enrichment if already planned and budget-safe.
- Cache/stale recommendation rules should be respected.

Frontend:

- Score ring.
- Strengths.
- Missing skills.
- Next actions.
- AI progress loader during long tasks.

## Phase 9 — Settings implementation

Backend:

- Account update.
- Email preferences.
- Password update.
- OAuth connections.
- Delete account flow.

Frontend:

- Desktop layout as v16.
- Mobile accordion cards with spacing.
- No top section list on mobile.
- One open section at a time preferred.

## Phase 10 — EN/FR language implementation

Prototype uses JS translation. Production can use either:

Option A — Django i18n:

- Mark strings with `{% trans %}`.
- Use `/fr/` or language cookie/session.
- Stronger long-term solution.

Option B — Keep JS toggle for MVP:

- Store language in localStorage.
- Translate visible UI strings client-side.
- Faster, but less SEO-friendly and less robust.

Recommended:

- Use Django i18n if not too expensive.
- If time is short, keep the v16 JS toggle initially and migrate later.

## Phase 11 — Theme implementation

- Preserve dark/light toggle.
- Store preference in localStorage.
- Default follows system preference if no stored preference.
- Avoid flash of wrong theme with early inline script.

## Phase 12 — QA before merge

- Compare implemented pages against v16 side-by-side.
- Test desktop and mobile.
- Test dark/light.
- Test EN/FR.
- Test logged out, logged in, email unverified, OAuth no-password, CV missing, profile incomplete, saved jobs empty, recommendations empty.

## Implementation warning

Do not let backend implementation become a redesign. If a backend constraint requires a UI change, document it first and confirm before changing the prototype direction.
