# Phase 16H Batch Plan — Controlled Prototype Port

## Principle

Do not implement Phase 16H as one giant prompt.

Each batch must be implemented, reviewed, and approved before the next batch starts.

Workflow:

```text
Gemini implements one batch.
Codex reviews that batch.
User sends review pack.
Senior review approves or rejects.
Only after approval, next batch starts.
```

## Batch 0 — Discovery and mapping only

### Goal

Verify repository state against prototype and Phase 16H rules before implementation.

### Allowed work

Read-only inspection only.

### Forbidden work

- no file edits
- no migrations
- no CSS changes
- no template changes
- no commits

### Output

A concise report with:

- prototype files detected
- Django routes/templates mapped
- backend gaps
- risks
- tests to protect
- files likely touched per batch
- questions/blockers

## Batch 1 — Global shell

### Scope

Implement global shell only:

- base layout
- header
- mobile drawer/menu
- footer
- theme toggle preservation
- logged-in/logged-out nav states
- email confirmation banner
- toast/state foundation

### Must enforce

Logged-out nav:

- Jobs
- Recommendations -> auth with next
- About
- Sign in / Get started

Logged-in nav:

- Jobs
- Recommendations
- Saved
- Profile
- Settings
- About
- Sign out

Email confirmation banner:

- visible only for authenticated unverified primary email
- hidden for anonymous users
- hidden for verified email users
- hidden for trusted OAuth-verified users

### Forbidden in Batch 1

- no job-card redesign
- no recommendations page redesign
- no saved jobs page redesign
- no profile setup redesign
- no contact backend
- no notification feed/page

### Review gates

- anonymous header correct
- logged-in header correct
- email banner correct
- theme still works
- toasts still work
- existing auth routes still work
- tests pass

## Batch 2 — Jobs list and job detail

### Scope

Implement jobs/search experience:

- jobs list/index layout from prototype
- job card partial
- filter/search layout
- job results/no-results state
- job detail page
- France locked/default UI
- save visibility rules
- dynamic job-detail match CTA

### Must enforce

Anonymous:

- no Save buttons
- no Saved links
- can browse jobs and job detail

Logged-in:

- Save buttons visible
- Saved Jobs available

Dynamic job detail CTA:

- logged out -> sign in/check recommendations CTA
- logged in no CV/profile -> complete profile/upload CV
- logged in profile/CV exists and no match -> check/calculate match
- logged in match exists -> view score
- logged in failed/stale match -> retry/refresh

### Forbidden in Batch 2

- no matching algorithm changes
- no recommendation algorithm changes
- no backend deletion of quick match
- no fake countries
- no application tracking system

## Batch 3 — Auth, profile setup, CV, settings

### Scope

Implement:

- login/signup visual styling
- email verification sent/confirm pages
- password set/change pages
- profile setup/CV/profile flow
- account/settings/connections/email preferences visuals

### Must enforce

Password step:

```python
not request.user.has_usable_password()
```

Email/password users skip set-password step.

OAuth users without usable password see set-password step.

Backend password policy wins over prototype copy.

### Forbidden in Batch 3

- no custom auth replacement
- no weakened password validators
- no fake OAuth behavior
- no new public profile feature

## Batch 4 — Recommendations, saved jobs, match score, reusable states

### Scope

Implement:

- recommendations page and partials
- saved jobs page
- match score/detail page
- match history if needed
- empty states
- loading states
- failure states
- toast/alert visual consistency

Use `notifications.html`, `empty-states.html`, `loading-states.html`, and `failure-states.html` as component references only.

### Forbidden in Batch 4

- no notification feed/page
- no notification bell
- no Notification model
- no algorithm changes
- no new LLM scoring language

## Batch 5 — About/contact backend

### Scope

Implement the real About/contact page backend:

- `/about/` route
- template port from prototype
- ContactMessage model
- migration
- ContactForm
- ContactService
- Celery task for admin email
- safe success/failure messages
- anti-spam control such as honeypot and/or rate limit
- tests

### Must enforce

- DB record first
- Celery send after DB record exists
- no raw exception details in UI/logs
- no secrets in repo
- `.env.example` only if adding config

### Forbidden in Batch 5

- no newsletter system
- no CRM integration
- no external marketing platform
- no user messaging inbox

## Batch 6 — Final responsive polish and QA

### Scope

Polish only:

- mobile layout
- dark mode
- spacing consistency
- visual consistency
- accessibility basics
- empty/loading/failure consistency
- final copy cleanup

### Forbidden in Batch 6

- no new backend features
- no new pages
- no route churn
- no redesign

## Final Phase 16H QA gate

Before Phase 16H is approved:

- Django check passes
- makemigrations check passes
- focused tests pass
- full test suite passes
- Tailwind build/check passes if CSS changed
- `git diff --check` passes
- custom whitespace scanner passes
- manual browser review covers desktop/mobile and light/dark
- anonymous/logged-in/verified/unverified/OAuth password states checked

Reject if:

- colors drift
- cards drift
- anonymous users see Save
- Saved appears logged out
- wrong match CTA appears
- email banner stays after verification
- fake notifications page is added
- agent invents new sections/pages
- backend behavior breaks
