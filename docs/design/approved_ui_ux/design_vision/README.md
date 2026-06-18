# TuniTech Abroad — Professional UI/UX Design Vision v3

Status: **design-spec ready for approval after Sonnet audit reconciliation**.

This package is the technical UI/UX vision for the professional redesign of TuniTech Abroad. It is intentionally boring, explicit, and implementation-oriented. It is **not** a coding prompt and **not** a phase package yet.

## Product stance

TuniTech Abroad is a France-first job intelligence platform for Tunisian IT candidates. The interface must make this obvious in less than five seconds:

1. Find France IT jobs and internships.
2. Upload or complete a CV/profile.
3. Get deterministic match scores.
4. Understand missing skills and risks.
5. Save/apply to realistic opportunities.

The product is not a generic job board, not an employer marketplace, not a black-only AI landing page, and not a university admin portal.

## Readiness decision

This v3 package resolves the audit blockers:

- Adaptive light/dark mode is locked to system preference using Tailwind `darkMode: "media"`.
- No manual theme toggle in this redesign.
- No new dependency requirement: no `django-widget-tweaks`, no `django-crispy-forms`, no `@tailwindcss/typography`, no frontend framework.
- Font decision is locked: system stack first; optional self-hosted Inter later, not Google Fonts by default.
- Brand colors, semantic colors, surfaces, radii, shadows, spacing, typography, and component states are specified.
- Mobile jobs filters use an overlay drawer, not `<details>`.
- Legal pages have explicit `.tta-legal` component styling.
- CV upload has drag-over feedback.
- Profile forms have sticky mobile save.
- Match score rings have responsive sizing.
- Empty states have icons and action copy.
- Job/recommendation/saved-card variants are defined.
- Backend safety guardrails are explicit.

## Hard implementation constraints

- Django templates only.
- Tailwind CSS.
- HTMX only where it improves server-rendered UX.
- Alpine.js only for tiny UI behavior already accepted: dropdowns, mobile drawer, drag/drop visual state.
- No React, Next.js, Vue, Angular, SPA architecture, FastAPI, MongoDB, SQLAlchemy.
- No new backend product features during UI polish.
- Preserve existing routes, forms, CSRF tokens, `public_id`, allauth provider URLs, and HTMX attributes.
- CV files stay private.
- Public job search reads local PostgreSQL only.
- Views stay thin and call services.

## Approval scope

Approve this package before creating Phase 14K implementation files.

Approving this package means approving the visual system, page hierarchy, theme behavior, component behavior, copy conventions, mobile behavior, and safety boundaries.

It does not mean approving generated code yet.


## v3 reconciliation after external audit

This version resolves the remaining implementation-readiness issues found by the Sonnet audit:

- Canonical French labels are reconciled across recommendation cards, match detail, and copy dictionary.
- Account/security route is locked to `/dashboard/account/`; `/dashboard/settings/` is removed from the implementation vision.
- `Comment ça marche` is locked to `/#comment-ca-marche`.
- Match history is renamed from ambiguous `Analyses` to `Compatibilités`.
- Pagination component is specified.
- Progress bar component is specified.
- Select styling and skill-filter behavior are specified.
- Avatar dropdown Alpine pattern is specified.
- Cookie/privacy banner is explicitly conditional, not blindly implemented.
- GDPR-adjacent account UI avoids fake controls without backend support.

Verdict: v3 is ready as the design vision source of truth before Phase 14K package creation.
