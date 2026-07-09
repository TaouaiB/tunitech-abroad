# TuniAtlas v16 Implementation QA Checklist

Use this before accepting the implemented UI.

## Global visual QA

- [ ] Theme matches v16.
- [ ] Colors match v16.
- [ ] Typography matches v16.
- [ ] Card radius/shadows match v16.
- [ ] Header matches v16.
- [ ] Footer matches v16.
- [ ] No unnecessary helper wording added.
- [ ] No old “More” menu.
- [ ] Account menu only has Profile, Settings, Sign out.
- [ ] Account menu has no arrows.

## Theme QA

- [ ] Default follows system preference.
- [ ] Toggle works.
- [ ] Preference persists.
- [ ] No wrong-theme flash or minimal flash only.
- [ ] All pages support dark/light.

## Language QA

- [ ] EN/FR switch visible in header.
- [ ] Language preference persists.
- [ ] Jobs page translates key labels.
- [ ] Job detail translates key labels.
- [ ] Match score translates key labels.
- [ ] Auth translates key labels/errors.
- [ ] Profile translates key labels/errors.
- [ ] Settings translates key labels/errors.
- [ ] About/contact translates key labels/errors.
- [ ] No mixed half-translated major UI sections.

## Jobs page QA

- [ ] Index is landing page.
- [ ] Jobs visible logged out.
- [ ] Search visible and usable.
- [ ] Filters work.
- [ ] France-only filter checked/disabled.
- [ ] Stage/alternance are filters/tabs, not separate pages.
- [ ] Job cards have Save only.
- [ ] No Postulate button on cards.
- [ ] Job card/title links to detail.
- [ ] Freshness labels follow rule.
- [ ] Empty state works.
- [ ] Mobile filters open in drawer.
- [ ] Mobile search/stats do not block job browsing.

## Job detail QA

- [ ] Shows title, company, city, source.
- [ ] Shows description and required skills.
- [ ] Shows Postulate external link.
- [ ] Shows Save.
- [ ] Shows View score.
- [ ] Shows Back to jobs.
- [ ] Mobile sticky action bar works.
- [ ] No removed Missions/Profile blocks reintroduced.

## Match score QA

- [ ] Score ring visible.
- [ ] Fit summary visible.
- [ ] Strengths visible.
- [ ] Missing skills visible.
- [ ] Next actions visible.
- [ ] Postulate and Save work.
- [ ] Mobile sticky action bar works.
- [ ] Mobile details are not too heavy.

## Auth QA

- [ ] Google OAuth button visible.
- [ ] GitHub OAuth button visible.
- [ ] No unnecessary “or email” text.
- [ ] Email validates live.
- [ ] Password validates live.
- [ ] Password minimum 6 characters shown as error while typing.
- [ ] Verify password validates live.
- [ ] Matching password shows green/success state.
- [ ] Signup starts email verification flow.

## Account activation QA

- [ ] Banner means email confirmation only.
- [ ] Banner visible when email unverified.
- [ ] Banner not shown when email verified.
- [ ] Resend email action works or is wired.

## Profile setup QA

- [ ] OAuth signup starts at Set password.
- [ ] Account without password returns to Set password first.
- [ ] Step order: Set password → CV → Profile.
- [ ] CV upload accepts PDF/DOCX.
- [ ] Profile fields match v16.
- [ ] Live validation works.
- [ ] Mobile stepper compact.
- [ ] Mobile uses bottom action buttons only.
- [ ] No duplicate buttons on mobile.
- [ ] No extra helper wording like OAuth account / Optional / Check extracted data.

## Recommendations QA

- [ ] Requires authenticated user/profile/CV as appropriate.
- [ ] Cards match v16.
- [ ] Match badge displays correctly.
- [ ] Save action works.
- [ ] Empty state works.
- [ ] Loading state works.
- [ ] Failure state works.

## Saved jobs QA

- [ ] Requires login.
- [ ] Saved jobs display.
- [ ] Remove/unsave works.
- [ ] Empty state works.
- [ ] No applied/expired/urgent state.

## Settings QA

- [ ] Account section works.
- [ ] Email preferences work.
- [ ] Security/password update works.
- [ ] Google/GitHub connection states show.
- [ ] Delete account flow exists.
- [ ] Mobile sections collapse.
- [ ] Collapsed cards have spacing and do not touch.

## About/contact QA

- [ ] About page remains compact.
- [ ] Email validation live while typing.
- [ ] Contact form handles success/failure.
- [ ] No extra marketing wall added.

## Loading/failure/empty states QA

- [ ] Empty jobs state.
- [ ] Empty saved jobs state.
- [ ] Empty recommendations state.
- [ ] CV missing state.
- [ ] Profile incomplete state.
- [ ] CV too large state.
- [ ] Unsupported file state.
- [ ] Parser failed state.
- [ ] Match failed state.
- [ ] Verification expired state.
- [ ] Contact failed state.
- [ ] Session expired state.
- [ ] Network error state.
- [ ] AI progress loaders display for CV/match/recommendations.

## Regression blockers

Block implementation if:

- [ ] UI is visibly redesigned away from v16.
- [ ] Job cards add Postulate.
- [ ] Already-applied state appears.
- [ ] Expired/urgent job states appear.
- [ ] Admin UI is added.
- [ ] Extra explanatory wording is added.
- [ ] Mobile profile has duplicate buttons.
- [ ] Settings mobile cards touch when collapsed.
- [ ] EN/FR switch breaks major labels.
