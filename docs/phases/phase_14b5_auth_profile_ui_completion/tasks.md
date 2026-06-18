# Tasks

## T1 — Preflight and route/template audit

- [ ] Read phase docs.
- [ ] Run git status/diff.
- [ ] Enumerate all user-facing project URLs.
- [ ] Enumerate installed allauth account/socialaccount templates.
- [ ] Create a checklist of every `/accounts/` page to style.
- [ ] Do not implement before route/template audit is complete.

## T2 — Fix profile truth source

- [ ] Create/confirm one service method for missing fields.
- [ ] Use same missing fields in profile, dashboard, recommendations.
- [ ] Ensure phone/location are never listed missing if DB has them.
- [ ] Rename `Current level` to `Niveau de carrière`.
- [ ] Rename `Years experience` to `Années d’expérience`.
- [ ] Remove `target_country` from all user-visible UI.
- [ ] Add tests for missing-field truth.

## T3 — CV parse/profile sync repair

- [ ] Ensure CV parse fills empty phone/location/links.
- [ ] Ensure current level inference only when obvious.
- [ ] Do not hallucinate years experience.
- [ ] Do not hallucinate target country.
- [ ] Recalculate profile completion after parse.
- [ ] Show applied/detected data clearly on CV page.
- [ ] Add regression tests.

## T4 — Recommendation blocker repair

- [ ] Recommendation blocker uses same missing-field service.
- [ ] Recommendation page shows exact missing fields only.
- [ ] Recommendations show stored offers when profile usable.
- [ ] No fake `Aucune offre ne correspond` for incomplete profile.
- [ ] Add tests for incomplete, usable, no jobs, no match, failed/stale states.

## T5 — Allauth page styling

- [ ] Style `/accounts/3rdparty/`.
- [ ] Style `/accounts/password/set/`.
- [ ] Style confirm email pages.
- [ ] Style password reset/change pages.
- [ ] Style email management pages.
- [ ] Style social signup/error/cancel/connection pages where present.
- [ ] Ensure all auth forms use same design system.

## T6 — Email template cleanup

- [ ] Configure Site/domain locally to TuniTech Abroad appropriate domain.
- [ ] Override account email templates.
- [ ] Remove `example.test` from all email content.
- [ ] Ensure duplicate-account email has clear copy and no fake confirmation wording.
- [ ] Ensure verification email contains real verification link.
- [ ] Add tests or render checks for email subjects/body.

## T7 — Social account connections

- [ ] Add/fix `/dashboard/account/connections/`.
- [ ] Show Google/GitHub connected state.
- [ ] Show connect buttons for missing providers.
- [ ] Show safe disconnect controls where appropriate.
- [ ] Show set-password CTA for OAuth-created user with unusable password.
- [ ] Add user-facing explanation about provider browser session/account switching.
- [ ] Add tests for page rendering and connection state.

## T8 — Provider data provisioning

- [ ] Fill empty full name from Google/GitHub provider data.
- [ ] Fill GitHub profile URL from GitHub provider data.
- [ ] Add avatar URL support if no existing safe field exists.
- [ ] Add migration only if avatar_url field is needed.
- [ ] Do not store OAuth tokens.
- [ ] Add tests using fake provider payloads.

## T9 — Full UI coverage QA

- [ ] Run all checks/tests.
- [ ] Run all security greps.
- [ ] Render all public/dashboard/auth pages.
- [ ] Record every page in agent report.
- [ ] Mark final verdict `BLOCKED_HUMAN_VISUAL_SIGNOFF`.
