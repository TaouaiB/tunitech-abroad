# 13 — Future Phase Split Recommendation v3

This is not an implementation prompt.
This is only a recommended split after the design vision is approved.

## Phase 14K-A — Design system and global shell

Scope:

- Tailwind `darkMode: "media"`
- brand palette in `tailwind.config.js`
- `app.css` component classes
- base layout
- navbar
- footer
- buttons
- cards
- badges
- forms
- messages/alerts
- legal `.tta-legal`
- empty state component
- responsive shell

No page logic changes.

Acceptance direction:

- all existing pages still load
- dark mode follows system
- no route/form/HTMX breakage

## Phase 14K-B — Public UX polish

Scope:

- homepage search gateway
- jobs list
- mobile filter drawer
- job card variants
- job detail
- quick match visual polish
- CV checker
- privacy/terms visual cleanup

Preserve:

- public search local DB behavior
- public_id routes
- job detail actions
- save/quick match HTMX

## Phase 14K-C — Auth and onboarding polish

Scope:

- login
- signup
- password reset visual consistency
- OAuth buttons
- French labels
- auth split-screen desktop layout
- mobile auth layout

Preserve:

- django-allauth provider tags
- forms
- CSRF
- redirect behavior

## Phase 14K-D — Dashboard app polish

Scope:

- dashboard home bento/action center
- profile sectioned form
- sticky mobile save
- CV page/dropzone/status
- recommendations page
- saved jobs
- match history/detail
- email preferences
- account/security

Preserve:

- forms
- CSRF
- HTMX
- CV privacy
- recommendation behavior
- match scoring behavior

## Phase 14K-E — Final UI QA and polish

Scope:

- mobile review
- dark mode review
- accessibility/focus review
- empty states review
- French copy pass
- visual consistency pass
- screenshot review
- regression checks

No new design features.

## Why split this way

A single huge UI phase risks breaking backend behavior. These subphases isolate risk:

1. shell/components first
2. public pages next
3. auth pages separately
4. private app pages separately
5. QA cleanup last

The agent may work automatically inside one approved subphase only.
