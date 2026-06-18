# Phase 14B Tasks

## TTA-14B-001 — Preflight and UI inventory

Inspect current branch, git status, templates, base layout, public pages, dashboard pages, HTMX partials, auth templates, error pages, static/Tailwind setup, and Phase 14A report if present.

Acceptance:

- agent knows which templates are used
- agent identifies page gaps
- no code changes before preflight passes

---

## TTA-14B-002 — Shared design system

Create/update reusable template patterns for page containers, section headers, cards, buttons, badges, skill chips, alerts, empty states, loading states, score blocks, form groups, and danger zones.

Acceptance:

- main pages use consistent cards/buttons/badges
- no random page-specific style chaos
- mobile layout remains sane

---

## TTA-14B-003 — Base template and navigation

Improve main layout, responsive navigation, logged-in/logged-out state, footer, active/current page cues if practical, page spacing, and global messages.

Remove phase placeholder text, `example.test`, raw future-phase copy, and unprofessional labels.

---

## TTA-14B-004 — Homepage redesign

Build a credible landing page with hero, value proposition, CTAs, how-it-works, target users, feature cards, France-first explanation, and demo honesty if needed.

---

## TTA-14B-005 — Public jobs list redesign

Improve `/jobs/`: search/filter panel, job cards, metadata badges, skill chips, pagination, empty state, responsive layout.

Must preserve local PostgreSQL-only search.

---

## TTA-14B-006 — Job detail + quick match redesign

Improve `/jobs/<uuid>/`: hero/header, job meta badges, source link, skills, description typography, quick match card, full match CTA, saved job CTA.

Quick match must remain anonymous, LLM-free, CV-free, recommendation-free, and not stuck after HTMX.

---

## TTA-14B-007 — Dashboard redesign

Improve `/dashboard/`: profile completeness card, CV status card, recommendations preview, match history preview, saved jobs preview, missing skills preview if available, next action CTAs.

---

## TTA-14B-008 — Profile page redesign

Improve `/dashboard/profile/` with grouped sections: Informations personnelles, Présence professionnelle, Objectif France, Langues, Expérience, Compétences, Préférences.

---

## TTA-14B-009 — CV page redesign

Improve `/dashboard/cv/`: upload zone, consent block, active CV status, parsed fields summary, parse warnings, detected-but-not-applied values if available, replace/delete actions, and clear parse states.

Must never expose private file URL or raw full CV text.

---

## TTA-14B-010 — Recommendations page redesign

Improve `/dashboard/recommendations/` states: incomplete profile, no active jobs, pending refresh, failed refresh, recommendations available.

Cards must show score, job title/company/location, match label, missing skills, reasons, save/detail CTAs.

---

## TTA-14B-011 — Match pages redesign

Improve `/dashboard/matches/` and `/dashboard/matches/<uuid>/`: score hero, score label, breakdown bars/cards, matched skills, missing skills, risk flags, recommended actions, job summary, profile snapshot.

---

## TTA-14B-012 — Saved jobs, email preferences, account pages

Improve saved jobs, email preferences, account, and delete-account pages with clean states and serious danger-zone UX.

---

## TTA-14B-013 — Auth, legal, error pages

Improve login, signup, password reset/change, email management, privacy, terms, 404, and 500 pages.

---

## TTA-14B-014 — Mobile/responsive pass

Check homepage, jobs list, job detail, dashboard, profile, CV, recommendations, match detail, and auth pages at mobile width.

---

## TTA-14B-015 — Regression/security tests and report

Run all required commands and grep checks. Fill agent report.
