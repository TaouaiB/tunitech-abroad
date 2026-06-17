# Visual Reference Analysis

## Reference summary

The attached design reference appears to follow a modern indie SaaS/job-matcher aesthetic:

- warm ivory/off-white background
- dark primary text and dark hero surfaces
- lime/green accent for success/active/match states
- blue accent for interactive elements
- pill navigation and rounded CTAs
- large bold headlines
- spacious white cards
- soft shadows and rounded corners

## How to adapt safely to TuniTech Abroad

TuniTech Abroad should feel:

- France-first
- credible for recruiters/portfolio viewers
- youthful for students/juniors
- technical but not cold
- helpful and honest
- not generic job board

## Color rules

Use this hierarchy:

```text
Background: warm ivory / off-white
Primary text/surfaces: deep navy or near-black
Card background: white or very light ivory
Accent: lime green for match/success/active states
Secondary accent: blue for links/focus only
Warning: amber
Danger: red
Muted text: slate/gray
```

Do not use lime as tiny text on white. Use it as a badge fill, ring, icon background, score accent, or CTA accent with dark text.

## Component direction

### Navigation

- Rounded pill nav group.
- Clear logged-in vs logged-out state.
- Logged-in users must never see signup CTAs.
- Mobile nav must not break.

### Homepage

- Large direct headline.
- One-line product explanation.
- Two CTAs: explore jobs / analyze CV.
- Product preview card showing match score, validated skills, missing skills.
- User audience cards: étudiant, PFE/stage, junior, bootcamp, mid-level.

### Dashboard

- Mission-control layout.
- Status cards for profile, CV, recommendations, saved jobs, matches.
- Missing-field chips.
- Direct next action buttons.

### CV page

- Upload status card.
- Parsed field checklist.
- Detected-but-not-applied card.
- Warning card.
- No raw CV text.
- No private file URL.

### Recommendations

Use first-class state cards:

- Profile incomplete
- No active jobs
- No matching jobs
- Generation failed
- Recommendations ready

Each state needs:

- icon
- title
- plain-language reason
- missing field chips if relevant
- primary CTA

### Match detail

- Score hero.
- Score label.
- Matched skills.
- Missing skills.
- Risk flags.
- Recommended actions.
- Job summary.

## Icon rules

Do not install icon libraries. Use inline SVG only. Heroicons-style inline SVG is acceptable.

## Glassmorphism rule

Use blur/glass only sparingly for the hero/nav. Do not use blur/glass on dense data cards or forms.
