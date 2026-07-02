# Phase 16H Batch 2: Jobs List + Job Detail Implementation

## Goal
Port the approved v16 prototype into the existing Django jobs templates (`job_list.html`, `job_detail.html`, `job_card.html`, and `save_button.html`) while preserving backend behavior, matching logic, and CTA dynamic matrices.

## Changes Made
1. **`job_card.html` & `save_button.html`**
   - Implemented the new prototype card layout with the `job-card` article, new classes, and badge styling.
   - Preserved dynamic data (job title, badges, skills logic, URL reverse mappings).
   - Ensured anonymous users do not see the Save button natively by evaluating `user.is_authenticated`.
   - Updated `save_button.html` to output exactly what the new v16 prototype expects.

2. **`cta_context.py` Service**
   - Created `apps/jobs/services/cta_context.py` containing `CTAContextService`.
   - Added logic matching the specified dynamic CTA matrix:
     - Anonymous users -> Sign in to test
     - Logged-in without complete profile/CV -> Complete Profile CTA
     - Logged-in ready, no match -> Calculate Match CTA
     - Logged-in match exists -> View Score CTA
     - Logged-in match failed -> Retry CTA

3. **`views.py` & `job_detail.html`**
   - Updated `job_detail` view to inject `cta_context` via the new service.
   - Refactored `job_detail.html` strictly matching the prototype. Added logic blocks using the injected `cta_context` dict state instead of relying on complex conditionals in the template.

4. **Tests Fixes**
   - Refactored the UI assertion tests (`test_views.py`, `test_14j_job_card_skills.py`, `test_15e_eligibility.py`) to align with the new v16 DOM structure (`job-card`, `pill-row`) and the updated text copy.
   - Removed the obsolete test asserting that the anonymous quick-match form contained a JavaScript reset, as anonymous users no longer see the quick match form in the detail view.

## Verification
- Ran backend unit tests -> PASSED.
- Built CSS `npm run css:build` -> PASSED.

## Manual Steps Remaining
- Review UI locally on Desktop and Mobile to verify padding, margins, and dynamic element rendering.
