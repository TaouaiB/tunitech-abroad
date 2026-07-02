# V16 Exact Implementation Plan

## Goal

Implement the TuniAtlas v16 final prototype into the real Django + HTMX application with maximum visual parity and minimum agent creativity.

The prototype already contains the HTML, CSS, responsive behavior, wording, and page states. Agents should not invent new UI.

## Golden rule

> The prototype is not a design reference. It is the UI contract.

Every implementation task must preserve:

- layout
- spacing
- colors
- typography
- responsive behavior
- wording
- dark/light behavior
- EN/FR behavior
- mobile drawers/accordions
- empty/loading/failure states
- sticky mobile actions

## Best implementation strategy

### Phase 0 — Place source files in repo

Create this folder:

```text
/docs/ui/v16-final/
```

Extract the v16 prototype there:

```text
/docs/ui/v16-final/index.html
/docs/ui/v16-final/job-detail.html
/docs/ui/v16-final/match-score.html
/docs/ui/v16-final/auth.html
/docs/ui/v16-final/profile-setup.html
/docs/ui/v16-final/recommendations.html
/docs/ui/v16-final/saved-jobs.html
/docs/ui/v16-final/settings.html
/docs/ui/v16-final/about.html
/docs/ui/v16-final/notifications.html
/docs/ui/v16-final/empty-states.html
/docs/ui/v16-final/loading-states.html
/docs/ui/v16-final/failure-states.html
/docs/ui/v16-final/404.html
/docs/ui/v16-final/500.html
```

Also place the lock/planning docs:

```text
/docs/ui/V16_UI_LOCK.md
/docs/ui/V16_COPY_LOCK.md
/docs/ui/V16_PAGE_MAPPING.md
/docs/ui/V16_ACCEPTANCE_CHECKLIST.md
```

Agents should read local files directly instead of receiving pasted HTML. This saves tokens.

---

## Phase 1 — Copy first, wire later

Do not convert, wire, refactor, and improve at the same time.

Use this order:

1. reproduce v16 visually as Django templates
2. replace static values with Django variables
3. wire HTMX actions
4. connect forms/backend endpoints
5. run QA and screenshot comparison
6. only then do small cleanup if it does not change visuals

Wrong instruction:

```text
Improve the current frontend based on v16.
```

Correct instruction:

```text
Port v16 exactly into the Django template. Do not redesign. Do not add text. Do not change behavior.
```

---

## Phase 2 — Build shared components first

Before implementing all pages, create or update shared components:

```text
templates/components/
  header.html
  footer.html
  theme_toggle.html
  language_toggle.html
  mobile_nav.html
  job_card.html
  skill_chip.html
  toast.html
  mobile_filter_drawer.html
  ai_progress.html
  empty_state.html
  loading_state.html
  failure_state.html
```

Do not over-abstract too early. Component extraction is useful only when it preserves visual parity.

---

## Phase 3 — Implement page by page

Do not ask an agent to implement all pages at once.

Recommended order:

1. base layout/header/footer/theme/language
2. jobs index
3. job card component
4. job detail
5. match score
6. auth
7. profile stepper
8. recommendations
9. saved jobs
10. settings
11. about
12. notifications
13. empty/loading/failure states
14. 404/500
15. final responsive pass

One task = one page or one component.

---

## Phase 4 — CSS plan

Preferred approach:

```text
static/css/tuniatlas_v16.css
```

Use this file for v16-specific CSS and responsive behavior.

Rules:

- preserve existing `tta-*` design tokens where possible
- do not scatter random CSS across templates
- do not redesign Tailwind classes from scratch
- do not rename classes unless necessary
- do not refactor before visual parity is achieved

Fastest safe path:

1. preserve v16 classes/styles
2. add controlled CSS in one file
3. after parity, optionally refactor carefully

---

## Phase 5 — JS/HTMX plan

Use one small JS file:

```text
static/js/tuniatlas-ui.js
```

Allowed JS responsibilities:

- theme toggle
- language toggle
- mobile menu drawer
- mobile filters drawer
- settings accordions
- profile stepper
- toast helper
- AI progress visual loaders
- sticky mobile bar behavior if needed

Use HTMX for server interactions only:

- save/unsave job
- filter jobs
- load more jobs
- CV upload status
- profile save
- match/recommendation refresh
- settings save

Do not use HTMX for simple visual toggles that can be local JS/Alpine.

Do not add React/Vue.

---

## Phase 6 — Screenshot comparison

For each implemented page:

1. screenshot v16 prototype
2. screenshot Django page
3. compare desktop light
4. compare desktop dark
5. compare mobile light
6. compare mobile dark
7. fix only differences

Acceptance rule:

> If the screenshot differs from v16, fix it. If code is cleaner but screenshot differs, reject it.

---

## Phase 7 — Commit small

Use small commits:

```text
ui: add v16 base layout
ui: implement v16 header and mobile nav
ui: implement v16 job card
ui: implement v16 jobs index
ui: implement v16 job detail
ui: implement v16 match page
ui: implement v16 auth pages
ui: implement v16 profile stepper
ui: implement v16 settings accordions
ui: implement v16 saved jobs
ui: implement v16 recommendations
ui: implement v16 states and error pages
ui: complete v16 responsive parity pass
```

Rollback should be easy.

---

## Final recommendation

Do not ask one agent to “implement the full prototype.”

Ask for one page/component at a time, with strict guardrails and screenshot-based review.
