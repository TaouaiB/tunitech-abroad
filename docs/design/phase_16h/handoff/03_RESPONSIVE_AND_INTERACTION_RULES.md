# Responsive and Interaction Rules

## Main mobile principle

**Primary content visible. Secondary content collapsible.**

Do not force users to scroll through large setup/search/settings blocks before reaching the useful content.

## Global responsive behavior

- Desktop layout should stay close to v16.
- Mobile uses drawers, accordions, and sticky action bars.
- Avoid duplicate actions on mobile.
- Avoid large repeated helper text.
- Keep cards compact.
- Keep spacing consistent.
- Do not let cards touch each other when collapsed.

## Header mobile behavior

- Header has brand, theme toggle, language toggle, avatar, hamburger/menu button.
- Mobile navigation opens as slide drawer.
- Drawer contains compact links only:
  - Jobs
  - Recommendations
  - Saved
  - Profile
  - Settings
  - About
- No explanations inside menu.

## Index mobile behavior

Mobile should prioritize job results.

Recommended structure:

1. Compact search row / Search jobs collapsible block.
2. Filters button opens slide drawer.
3. Active filter chips visible if filters are applied.
4. Job cards visible without excessive scrolling.
5. Stats/overview block collapsible.

Search block:

- Collapsed by default or compact by default.
- Opens when user taps Search jobs.

Stats block:

- Collapsible.
- Should not always occupy first screen.

Filters:

- Mobile drawer.
- Close button.
- Reset button.
- Apply/search action if needed.

Desktop:

- Keep normal layout with sidebar filters.

## Profile mobile behavior

Problem to avoid:

- Three big stepper cards taking too much vertical space.
- Duplicate inline and sticky bottom buttons.

Correct behavior:

- Show compact step indicator:
  - `Step 1 of 3 · Set password`
  - `Step 2 of 3 · CV`
  - `Step 3 of 3 · Profile`
- Step list can expand if needed.
- Sticky bottom actions handle navigation.
- On mobile, hide inline action buttons if sticky bottom bar is present.
- Do not duplicate buttons.
- Remove extra helper text.

Desktop:

- Stepper can remain visible as in v16.
- Inline buttons can remain if that is the desktop design.

## Settings mobile behavior

Problem to avoid:

- A settings section nav list above content wasting space.
- Collapsed cards touching each other.

Correct behavior:

- Hide section nav on mobile.
- Each settings section is an accordion card:
  - Account
  - Email
  - Security
  - Connections
  - Delete account
- Add small vertical gap between collapsed cards.
- One open at a time is preferred.
- Account can be open by default.

Desktop:

- Preserve v16 layout.

## Job detail mobile behavior

- Keep title and key job meta visible.
- Sticky bottom action bar: Postulate + Save.
- Avoid duplicate action buttons if sticky bottom bar is visible.
- Match/details can collapse if they take too much space.

## Match score mobile behavior

- Score remains visible.
- Details can collapse:
  - Fit summary
  - Strengths
  - Missing
  - Next actions
- Sticky bottom action bar: Postulate + Save.
- Avoid duplicate actions if sticky bottom bar is visible.

## Recommendations / saved mobile behavior

- Job cards remain compact.
- Match badge should not create overlap.
- Save/remove action in bottom row or aligned cleanly.
- No already-applied/expired/urgent state.

## Toast behavior

- Toasts appear top-right.
- Compact message.
- Do not use bottom toasts if they conflict with sticky mobile action bar.

## Loading behavior

Use AI progress cards for long actions:

CV parsing:

- Uploading CV
- Reading file
- Extracting profile
- Detecting skills
- Preparing review

Match score:

- Reading job
- Checking profile
- Comparing skills
- Finding gaps
- Building score

Recommendations:

- Reading profile
- Filtering jobs
- Ranking matches
- Preparing list

Use real progress only if available; otherwise use indeterminate/staged UI.
