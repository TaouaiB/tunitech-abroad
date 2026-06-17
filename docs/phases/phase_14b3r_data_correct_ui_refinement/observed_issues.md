# Observed Issues from Manual QA

These are confirmed by Baha's manual Chrome testing and shell diagnostics.

## CV/profile issues

1. CV page initially showed only email and phone, even when the CV contained more data.
2. Parser once wrote bad value `https://Next.js` into website/profile field. `Next.js` is a skill, not a URL.
3. Fresh extractor now gets location/linkedin/github/portfolio for the Aymen CV, but target roles still return `[]`.
4. Raw skill extraction is noisy and includes countries, employers, section titles, and sentences.
5. Profile application/reparse does not reliably clean stale bad data or apply corrected values.
6. Profile completion had conflicting values: `profile_completion_score` and `completion_percentage` did not align.
7. Profile labels still have English terms.
8. CV-detected values not applied to profile are not shown clearly.

## Recommendations issues

1. Active jobs exist, but recommendations page can show `Aucune offre ne correspond` instead of exact blocked reason.
2. Incomplete profile should show missing fields, not a fake no-match state.
3. `RecommendationRun` previously showed `success` while `JobRecommendation` count was 0 for an incomplete profile.
4. Need proof that a complete profile with active jobs creates stored recommendations.

## UI issues

1. Logged-in pages previously showed signup CTAs.
2. Auth/password reset pages had uneven styling.
3. Match analysis visual design was poor.
4. Quick match form/result still looked amateur in screenshots.
5. Profile/CV/recommendation states need first-class cards, not generic empty boxes.

## Reference design observations

The attached `ai-job-matcher` reference has useful visual inspiration but forbidden stack. It is React/Vite-style and must not be copied.

Safe inspiration:

- warm ivory page background
- deep black/navy brand cards
- rounded-pill nav/buttons
- strong bold hero type
- lime accent for success/match states
- crisp cards
- strong empty-state blocks

Do not copy:

- React components
- Vite structure
- lucide-react imports
- app claims or copy that do not match TuniTech Abroad
