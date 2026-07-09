# Scope — Phase 14B.3R

## In scope

### Product-flow repair

- Fix deterministic CV extraction for multiple CV fixture shapes.
- Fix stale bad profile data caused by previous broken extraction, especially `website_url=https://Next.js`.
- Fix profile application after CV parsing.
- Fix profile completion consistency.
- Fix recommendation states and generation behavior.
- Fix CV page display of extracted fields and detected-but-not-applied values.
- Fix profile page display of extracted/profile values and missing fields.
- Fix recommendations page so it never lies with vague empty state.
- Improve match/quick-match/profile/CV/recommendation UI where it directly supports the product-flow correctness.

### Visual refinement

Use the attached design reference only for visual direction:

- warm ivory background
- deep navy / near-black brand surfaces
- lime accent used sparingly for success/match states
- blue only for links/focus states
- rounded SaaS cards
- pill navigation/buttons
- large bold typography
- crisp white cards for dense data
- reusable empty/blocked/error state cards

### Testing

- Add at least 5 extractor text fixtures.
- Keep or add at least 1 PDF fixture if present.
- Add regression tests for CV extraction, profile application, completion, recommendations, and bad URL prevention.
- Run full Django test suite.
- Run browser/headless checks.
- Require Baha manual Chrome sign-off before PASS.

## Out of scope

- Deployment.
- Commit.
- React/Next/Vue/Vite/SPA.
- New employer/recruiter module.
- Payment/subscription.
- CV generator.
- Portfolio builder.
- Chatbot.
- Legal/visa advice.
- Full LLM product redesign.
- Replacing deterministic score with LLM.
- Live France Travail calls from public `/jobs/` search.

## Allowed backend changes

Allowed only where directly required by this phase:

- `apps/cvs/services/deterministic_extractor.py`
- `apps/cvs/services/parsing.py`
- `apps/profiles/services/completeness.py`
- `apps/profiles/models.py` only if required to remove duplicated completion logic or bad property logic
- `apps/recommendations/services/query.py`
- `apps/recommendations/services/recommendation.py`
- recommendation/profile/CV tests
- templates for CV/profile/recommendations/match/jobs/auth states

## Not allowed backend changes

- New scoring formula.
- New live API calls from views.
- LLM calls from views.
- Public ID changes.
- CV file serving changes.
- New product modules outside this phase.
