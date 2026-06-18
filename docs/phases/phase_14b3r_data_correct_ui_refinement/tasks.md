# Tasks — Phase 14B.3R

## TTA-14B3R-001 — Preflight and diff audit

- Read AGENTS.md.
- Inspect current git status and diffs.
- Identify already modified files from 14B/14B.1/14B.2.
- Do not commit.
- Do not deploy.
- Record current profile/CV/recommendation state for `baha.edine.taouai@gmail.com` if present.

## TTA-14B3R-002 — Multi-CV fixture coverage

- Add at least five raw text fixtures.
- Include the Aymen CV raw text case.
- Include French CV, student/PFE CV, messy links CV, incomplete CV.
- Add deterministic extractor tests for all fixtures.
- Add negative assertions for noisy skills and false URLs.

## TTA-14B3R-003 — Fix URL extraction

- Extract LinkedIn/GitHub/portfolio domains without `https://`.
- Normalize to `https://`.
- Never capture skill tokens as website URL.
- Prefer explicit labels: LinkedIn, GitHub, Portfolio, Website, Site web.
- For unlabeled domains, only accept plausible personal portfolio domains, not tech names.
- Add regression test: `Next.js` must never become `website_url`.

## TTA-14B3R-004 — Fix location extraction

- Extract header locations like `Tunis, Tunisia`.
- Support French formats like `Tunis, Tunisie`.
- Avoid extracting employers/universities as location.
- Add tests.

## TTA-14B3R-005 — Fix target role extraction

- Extract roles from `TARGET ROLES` section.
- Support French labels like `Objectif`, `Postes ciblés`, `Rôles ciblés`.
- Stop at next section.
- Return clean list.
- Add tests expecting roles from the Aymen CV:
  - Junior Full Stack Developer
  - Frontend Developer
  - Backend Developer
  - Web Developer Intern
  - Software Developer Intern
  - React Developer
  - Node.js Developer

## TTA-14B3R-006 — Reduce skill noise

- Restrict skill extraction to technical skill sections when possible.
- Use known taxonomy if available.
- Filter countries, employers, section titles, dates, months, sentences.
- Add negative assertions.
- Preserve valid skills:
  - JavaScript
  - TypeScript
  - React
  - Next.js
  - Node.js
  - Express.js
  - Django
  - PostgreSQL
  - MongoDB
  - Docker
  - Git
  - GitHub
  - Tailwind CSS
  - Jest
  - Postman
  - HTMX

## TTA-14B3R-007 — Fix language and experience extraction

- Extract French/English levels from language section.
- Map to valid app values. If choices are open text fields, store normalized values consistently.
- Estimate years of experience from date ranges when feasible.
- If uncertain, leave blank and show missing field rather than hallucinating.
- Add tests.

## TTA-14B3R-008 — Fix profile application/reparse

- Empty profile fields should be filled from CV parsed values.
- Existing non-empty full name must not be silently overwritten if different.
- Existing invalid CV-derived website URL such as `https://Next.js` must be cleaned/replaced when current parse has valid portfolio/website.
- ProfileSkill rows continue to be created with `source=cv_upload` and `is_confirmed=False`.
- Profile completion recalculates after parse.
- Add tests for empty profile, partially filled profile, and stale bad URL cleanup.

## TTA-14B3R-009 — Unify profile completion display

- Remove contradictory behavior between `profile_completion_score` and any dynamic `completion_percentage` property.
- One value must drive dashboard/profile UI.
- Empty profile must not show 100%.
- CV-derived partial profile must show realistic partial score.
- Add tests.

## TTA-14B3R-010 — Fix recommendation state logic

- Incomplete profile returns blocked state with exact missing fields.
- No active jobs returns no-jobs state.
- Complete profile + active jobs creates/stores recommendations.
- No matching jobs is distinct from incomplete profile.
- Failed generation is distinct from no matches.
- `RecommendationRun` must not report success if it skipped due to incomplete profile.
- Add tests.

## TTA-14B3R-011 — Fix CV/profile/recommendation UI

- CV page shows all extracted fields.
- CV page shows detected-but-not-applied values.
- Profile page uses French labels.
- Profile page shows missing fields and completion honestly.
- Recommendations page uses first-class blocked/no-jobs/no-match/failed/ready states.
- No raw CV text.
- No CV file URL.

## TTA-14B3R-012 — Visual refinement based on reference

- Apply visual direction from `visual_reference_analysis.md`.
- Do not copy React/Vite code.
- Keep Django templates/Tailwind/HTMX.
- Improve only pages directly affected by flow correctness plus core shell if needed.

## TTA-14B3R-013 — Final verification and report

- Run all required commands.
- Run browser/headless checks.
- Fill `agent_report.md` under phase folder.
- Do not claim PASS without Baha human sign-off.
