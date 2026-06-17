# Phase 14B Scope — Professional UI/UX Redesign

## Goal

Make TuniTech Abroad look and feel like a real modern product, not a raw Django prototype.

The interface must feel:

- modern
- clean
- youth-oriented
- France-first
- serious enough for portfolio/recruiter demo
- understandable for Tunisian IT candidates, students, bootcamp graduates, internship seekers, and junior/mid developers

## Included

This phase may modify:

- Django templates
- Tailwind utility classes
- HTMX partials
- small frontend behavior needed for UI state
- form rendering and help text
- template-level copy
- empty states
- error pages
- page layout
- cards, buttons, badges, alerts, skill chips
- tests that assert rendered content, routes, and security boundaries
- docs/phases/phase_14b_professional_ui_ux_redesign/agent_report.md

## Excluded

This phase must not implement:

- new backend product features
- new scoring formula
- recruiter/employer/training-center dashboards
- payment/subscription features
- chatbot
- CV generator
- portfolio builder
- SPA frontend
- React/Next/Vue/Angular
- deployment
- database redesign
- real API ingestion redesign

## Success target

The site should become a polished local MVP. A viewer can open the app and understand in 10 seconds:

1. This is a France IT job intelligence product.
2. It is made for Tunisian IT profiles.
3. It compares CV/profile to jobs.
4. It shows match, missing skills, and recommendations.

## Main surfaces

The agent must inspect and improve:

- `/`
- `/jobs/`
- `/jobs/<uuid>/`
- `/accounts/login/`
- `/accounts/signup/`
- `/accounts/password/reset/`
- `/accounts/password/change/`
- `/accounts/email/`
- `/dashboard/`
- `/dashboard/profile/`
- `/dashboard/cv/`
- `/dashboard/recommendations/`
- `/dashboard/matches/`
- `/dashboard/matches/<uuid>/`
- `/dashboard/saved-jobs/`
- `/dashboard/email-preferences/`
- `/dashboard/account/`
- `/dashboard/settings/delete-account/`
- `/privacy/`
- `/terms/`
- custom 404
- custom 500
