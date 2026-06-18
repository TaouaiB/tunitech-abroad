# 11 — Page-by-Page Final Blueprint v3

This is the concrete page blueprint to approve before implementation.

## `/` Homepage

### Layout

```text
Navbar
Hero/Search Gateway
Latest Jobs Preview
How It Works
Candidate Types
Intelligence Preview
Final CTA
Footer
```

### Main elements

- H1: `Trouvez des offres IT en France adaptées à votre profil`
- search form above fold
- chips: `Stage PFE`, `Alternance`, `Junior`, `Django`, `Data`, `Remote`
- CTA: `Explorer les offres`
- CTA: `Analyser mon CV`
- latest job cards

### Design

- adaptive light/dark
- `.tta-hero` with `min-h-[68vh] md:min-h-[72vh]`
- no black-only design
- no long marketing wall above jobs action

## `/jobs/`

### Layout

```text
Header
Active filters
Filter sidebar/drawer
Results count + sort
Job cards
Pagination
```

### Must improve

- richer job cards
- active filter chips
- fallback for missing fields
- mobile filter drawer
- styled selects/inputs
- consistent badges
- hover state

## `/jobs/<public_id>/`

### Layout

```text
Back link
Main job card
Sticky action/match card
Technical stack
Description
Similar/recommended if already available
```

### Must preserve

- public_id URL
- source/apply link
- save job HTMX
- quick match
- full match POST

### Must improve

- clearer key facts
- better skills section
- sticky sidebar desktop
- stacked sidebar mobile
- uncertainty labels

## `/cv-checker/`

### Layout

```text
Hero
How CV analysis works
Privacy block
Example insights
CTA
FAQ-lite
```

### CTA logic

- anonymous → login/signup
- authenticated → dashboard CV page

## `/accounts/login/`

### Layout

```text
Split desktop
Single card mobile
```

### Must include

- French labels
- Google button
- GitHub button
- forgot password
- signup link
- form errors

## `/accounts/signup/`

### Layout

Same as login.

### Must include

- French labels
- Google/GitHub signup
- terms/privacy copy
- login link

No CV upload on signup.

## `/dashboard/`

### Layout

```text
Header
Next action card
Bento grid
Account strip
```

### Cards

- Profile
- CV
- Recommendations
- Saved jobs
- Missing skills
- Recent analyses
- Email preferences
- Security/account

## `/dashboard/profile/`

### Layout

```text
Back link
Header
Completeness card
Readiness alert
Sectioned form
Sticky mobile save
```

### Sections

- Identity
- Links
- Objective France
- Experience
- Languages
- Preferences
- Skills

## `/dashboard/cv/`

### Layout

```text
Back link
Header
Active CV card
Parsed data summary
Privacy line
Replace/upload card
Delete action
```

### Must preserve

- file upload backend
- consent checkbox
- parse status polling
- delete flow
- private CV behavior

## `/dashboard/recommendations/`

### Layout

```text
Back link
Header
Filter/status bar
Recommendation cards
Empty/stale state
```

### Card content

- score + label
- reason
- matched skills
- missing skills
- risk flags
- save/apply/detail

## `/dashboard/saved-jobs/`

### Layout

```text
Back link
Header
Saved job cards
Empty state
```

### Must show

- stale/expired labels
- remove saved state
- view job action

## `/dashboard/matches/`

### Layout

```text
Back link
Header
Match result cards
Empty state
```

Each match card:

- job title
- score label
- date
- main risk/missing skill
- view analysis

## `/dashboard/matches/<public_id>/`

### Layout

```text
Back link
Score hero
Breakdown grid
Analysis sections
Apply card
LLM explanation panel if available/requested
```

### Must show

- global score with label
- category scores
- strong skills
- missing required/optional skills
- risk flags
- recommended actions

## `/dashboard/email-preferences/`

### Layout

```text
Back link
Header
Preference cards
Save action
Privacy/unsubscribe info
```

## `/dashboard/account/`

### Layout

```text
Back link
Header
User summary card
Password card
Linked accounts card
Privacy links
Danger zone
```

Danger zone must be visually separated. Privacy links are visible. Do not display data-export or cookie controls unless backend behavior exists.

## `/privacy/` and `/terms/`

Use `.tta-legal`.

No raw unstyled text.
