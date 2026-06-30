# Phase 14B Page Checklist

## `/`
- [ ] Hero explains product in 10 seconds.
- [ ] Primary CTA: Explorer les offres.
- [ ] Secondary CTA: Analyser mon CV / Créer mon profil.
- [ ] How it works section.
- [ ] Target users section.
- [ ] Feature cards.
- [ ] France-first positioning.
- [ ] Mobile layout works.

## `/jobs/`
- [ ] Filters are organized.
- [ ] Job cards are scannable.
- [ ] Metadata badges.
- [ ] Skill chips.
- [ ] Empty state.
- [ ] Pagination.
- [ ] Mobile layout.
- [ ] Search still reads local DB.

## `/jobs/<uuid>/`
- [ ] Header with title/company/location.
- [ ] Contract/remote/experience/freshness badges.
- [ ] Description readable.
- [ ] Skill sections.
- [ ] Source link.
- [ ] Quick match card.
- [ ] Full match CTA.
- [ ] Saved job CTA.

## Auth pages
- [ ] Login polished.
- [ ] Signup polished.
- [ ] Google/GitHub buttons styled.
- [ ] Password reset/change styled.
- [ ] Email confirmation/management styled.
- [ ] Errors visible.

## `/dashboard/`
- [ ] No placeholder text.
- [ ] Profile completeness card.
- [ ] CV status card.
- [ ] Recommendations preview.
- [ ] Saved jobs preview.
- [ ] Matches preview.
- [ ] Missing skills/next steps.
- [ ] Clear CTAs.

## `/dashboard/profile/`
- [ ] Grouped sections.
- [ ] French labels/help.
- [ ] Completion guidance.
- [ ] Validation errors styled.
- [ ] Mobile form works.

## `/dashboard/cv/`
- [ ] Upload zone.
- [ ] Consent message.
- [ ] Active CV status.
- [ ] Parse status.
- [ ] Parsed fields safe summary.
- [ ] Warnings visible.
- [ ] Replace/delete actions.
- [ ] No file URL.
- [ ] No raw full text.

## `/dashboard/recommendations/`
- [ ] Incomplete profile state.
- [ ] No jobs state.
- [ ] Pending state only if real.
- [ ] Failed state.
- [ ] Recommendation cards.
- [ ] Score/missing skills/reasons.
- [ ] Save/detail CTA.

## `/dashboard/matches/`
- [ ] Clean match history cards.
- [ ] Empty state.
- [ ] Score labels.
- [ ] Detail links use UUID.

## `/dashboard/matches/<uuid>/`
- [ ] Score hero.
- [ ] Breakdown.
- [ ] Matched/missing skills.
- [ ] Risk flags.
- [ ] Recommended actions.
- [ ] Job/profile summary.

## `/dashboard/saved-jobs/`
- [ ] Saved cards.
- [ ] Status badges.
- [ ] Empty state.
- [ ] Unsave action.

## `/dashboard/email-preferences/`
- [ ] Clear preference sections.
- [ ] Digest explanation.
- [ ] Save action styled.

## `/dashboard/account/` and delete page
- [ ] Account settings layout.
- [ ] Danger zone.
- [ ] Confirmation text.
- [ ] Serious deletion warning.

## `/privacy/` and `/terms/`
- [ ] readable legal pages.
- [ ] product-specific wording.
- [ ] no debug/fake placeholder.

## 404/500
- [ ] polished.
- [ ] no URLconf under DEBUG=False.
- [ ] no traceback.
