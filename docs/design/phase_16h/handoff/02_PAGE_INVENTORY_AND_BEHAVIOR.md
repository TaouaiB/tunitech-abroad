# Page Inventory and Expected Behavior

Prototype v16 contains standalone HTML pages. During implementation, these should become Django templates/components while preserving visual behavior.

## 1. `index.html` — Jobs / Landing Page

Purpose:

- Main landing page.
- Job browsing page.
- Search, filters, job cards.

Key behavior:

- Jobs visible without login.
- Search inputs: role/company/skill and city.
- Filters: country, city, company, contract, work type, experience, stage/alternance tabs, reset.
- Country is France-only and disabled/checked.
- Job cards link to job detail when title/card is clicked.
- Job cards have Save only.
- No Postulate button on cards.
- Mobile: search/stats/filter areas are collapsible or drawer-based so jobs appear quickly.
- Filters open as mobile drawer.

Data to connect:

- Job list from `NormalizedJob` or equivalent active job model.
- Saved state per authenticated user.
- Search/filter query parameters.
- Job source and freshness.

## 2. `job-detail.html` — Job Detail

Purpose:

- Full job detail page.
- External application action.
- Match summary aside/card.

Key behavior:

- Shows title, company, location, source, tags, description, required skills.
- Has Postulate action to external source.
- Has Save action.
- Has View score link to match page.
- Has Back to jobs.
- Mobile: main actions are sticky bottom action bar; secondary blocks can collapse.

Data to connect:

- Job detail fields.
- Job source URL.
- Saved state.
- User-specific match score if authenticated and profile/CV exists.

## 3. `match-score.html` — Match Score

Purpose:

- Show compatibility score and actionable gaps.

Key behavior:

- Shows score ring.
- Shows Fit summary.
- Shows Strengths.
- Shows Missing.
- Shows Next actions.
- Has Postulate and Save actions.
- Mobile: score remains visible; details can collapse; primary actions sticky at bottom.

Data to connect:

- Recommendation/match score result.
- Matched skills.
- Missing skills.
- Recommended next actions.
- Job apply URL.
- Saved state.

Important implementation note:

- Final scoring should remain rule-based if that is current product policy.
- LLM can assist enrichment/CV/skills only if budget and product policy allow.

## 4. `recommendations.html` — Recommended Jobs

Purpose:

- Personalized job recommendations.

Key behavior:

- Requires login/profile/CV state.
- Shows recommended job cards with match badge.
- Save action only.
- Links to job detail/match flow.
- Handles empty/no recommendations state.

Data to connect:

- User recommendation runs.
- Active recommendations.
- Match percentages.
- Saved state.

## 5. `saved-jobs.html` — Saved Jobs

Purpose:

- User’s saved jobs.

Key behavior:

- Requires login.
- Shows saved job cards.
- Save button acts as remove/unsave state.
- Empty state when no saved jobs.
- No applied/expired/urgent state.

Data to connect:

- User saved jobs.
- Active job details.

## 6. `auth.html` — Sign In / Create Account

Purpose:

- Sign in / sign up with OAuth or email/password.

Key behavior:

- Google button.
- GitHub button.
- Email/password fields.
- Signup has verify password.
- Password validation live while typing.
- Minimum password length: 6 characters.
- Verify password shows red/green state live.
- Email validation live while typing.
- Remove unnecessary wording like “or email”.

Data/endpoints to connect:

- Login.
- Signup.
- Google OAuth.
- GitHub OAuth.
- Email verification.

## 7. `profile-setup.html` — Profile Stepper

Purpose:

- Profile onboarding after signup/OAuth.

Final step order:

1. Set password.
2. CV.
3. Profile.

Key behavior:

- OAuth users still start with Set password.
- If account has no password and user returns later, Set password must remain first required step.
- CV upload supports PDF/DOCX.
- Profile fields include identity, contact, links, language, skills, location, target city, experience.
- Mobile: stepper is compact; sticky bottom navigation; no duplicate buttons.
- Use only bottom action buttons on mobile, not duplicate inline and bottom buttons.
- Remove unnecessary helper text such as OAuth account, Optional, Check extracted data.

Data/endpoints to connect:

- User profile.
- Password creation.
- CV upload.
- CV parsing status.
- Extracted profile fields.
- Profile save.
- Recommendation trigger.

## 8. `settings.html` — Account Settings

Purpose:

- User settings.

Sections:

- Account.
- Email.
- Security.
- Connections.
- Delete account.

Key behavior:

- Desktop can use section navigation if it matches v16.
- Mobile sections are collapsible accordion cards.
- Add small spacing between collapsed cards.
- Only one section open at a time is acceptable.
- Google/GitHub connect/disconnect state is visible.

Data/endpoints to connect:

- Account profile updates.
- Email preferences.
- Password update.
- OAuth connections.
- Delete account confirmation.

## 9. `about.html` — About / Contact / Policy Summary

Purpose:

- Compact company/contact/info page.

Key behavior:

- Keep as-is from v16.
- Contact email validates live while typing.
- Do not add more marketing text now.

## 10. `notifications.html`

Purpose:

- Notification/toast/state library reference.

Key behavior:

- Toast style notifications top-right.
- Includes links to state pages in prototype.

## 11. `empty-states.html`

Purpose:

- Demonstrates empty states.

States include:

- No jobs found.
- No saved jobs yet.
- No recommendations yet.
- CV missing.
- Profile incomplete.

## 12. `loading-states.html`

Purpose:

- Demonstrates loading states and AI-progress loaders.

States include:

- Search loading.
- Saving job.
- Checking match.
- Uploading CV.
- Parsing CV.
- Saving profile.
- AI parsing / matching / recommendations with progress bar and rotating compact task labels.

Implementation note:

- Use real progress only if backend task state supports it.
- Otherwise use indeterminate or staged simulated progress for UX only.

## 13. `failure-states.html`

Purpose:

- Demonstrates compact failure/error states.

States include:

- CV too large.
- Unsupported file.
- Parser failed.
- Match failed.
- Verification expired.
- Contact failed.
- Session expired.
- Network error.

## 14. `404.html` and `500.html`

Purpose:

- Error pages.

Key behavior:

- Preserve v16 style.
- Keep text compact.
