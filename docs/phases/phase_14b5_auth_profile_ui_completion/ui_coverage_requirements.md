# Full UI Coverage Requirements

## Rule

No more styling only the page Baha discovers manually. The agent must audit all reachable user-facing pages and style them proactively.

## Required page groups

### Public

- `/`
- `/jobs/`
- `/jobs/<uuid>/`
- quick match form/result on job detail
- `/privacy/`
- `/terms/`
- custom 404
- custom 500 template if present

### Dashboard

- `/dashboard/`
- `/dashboard/profile/`
- `/dashboard/cv/`
- `/dashboard/recommendations/`
- `/dashboard/matches/`
- `/dashboard/matches/<uuid>/`
- `/dashboard/saved-jobs/`
- `/dashboard/email-preferences/`
- `/dashboard/account/`
- `/dashboard/account/connections/` if added
- `/dashboard/settings/delete-account/`

### Account/auth

- all `/accounts/` GET pages that are user-facing
- all account templates that can be rendered by allauth
- all socialaccount templates that can be rendered by allauth

## Design system rules

- Warm ivory page background
- Deep navy/near-black primary surfaces
- Lime accent for success/active/score only
- Blue only for links/focus states
- Red only for destructive actions
- Amber only for warnings
- No lime tiny text on white
- No overused glassmorphism on dense data pages
- Use crisp cards for forms, profile, CV, recommendations, jobs
- Inline SVG icons only
- French-first copy

## Component requirements

Create or reuse consistent components for:

- auth shell/card
- form fields
- primary/secondary/danger buttons
- provider connection card
- profile missing-field banner
- blocked/empty/error state card
- CV extracted-field row
- recommendation card
- match score card
- dashboard metric card

## Browser verification

Use Chrome manually or headless screenshots. The agent report must list every checked URL and status.

Baha manual signoff remains mandatory even if automated browser checks pass.
