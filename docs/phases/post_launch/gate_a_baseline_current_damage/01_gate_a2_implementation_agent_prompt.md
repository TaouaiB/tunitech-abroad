# TuniAtlas Gate A.2 Implementation Agent Prompt

## Role

You are implementing **Gate A.2 — Production trust stabilization patch** for TuniAtlas.

TuniAtlas is the public product name. Do not rebrand it to TuniTech Abroad in public/user-facing text.

You are working in an existing Django monolith. Follow the current architecture strictly.

## Current state

Production deployment is complete and successful.

- Production deployed commit: `85bfda5 Merge dev for good version deployment`
- Source dev commit: `1562177 Harden pre-deployment skill and CV extraction`
- Branch workflow:
  - `main` = stable/production
  - `dev` = active work
- Local working branch expected: `dev`
- Current known baseline report:
  - `docs/phases/post_launch/gate_a_baseline_current_damage/gate_a_baseline_report_2026_07_10.md`
- Gate A baseline confirmed:
  - skill extraction noise exists
  - CV parser pollution exists
  - recommendation/match mismatch exists
  - product-flow defects exist after deployment smoke

## Active gate plan

Do not rename this work to Phase 17.

The active plan is:

```text
Gate A — Baseline current damage + production trust defects
Gate B — Skill extraction v2
Gate C — CV parser v2
Gate D — Admin anomaly review
Gate E — Rematerialize and compare
Deferred — EN/FR cleanup
```

You are working only inside **Gate A.2**.

## Hard stack rules

Allowed stack:

```text
Django
Django ORM
PostgreSQL
Redis
Celery / Celery Beat
django-allauth
Django templates
HTMX
Tailwind CSS only as already integrated
Alpine.js only where already needed
OpenRouter only where already existing and feature-flagged
PyMuPDF/pdfplumber for CV extraction
```

Forbidden:

```text
React
Next.js
Angular
FastAPI
MongoDB
SQLAlchemy
SPA architecture
new external services
live France Travail calls during normal user search
LLM calls from Django views
```

## Architecture rules

```text
- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data and do not call services/external APIs.
- No OpenRouter/LLM calls from Django views.
- User job search reads local PostgreSQL only.
- Public URLs use UUID public_id, never internal integer IDs.
- CV files are private and must not be publicly exposed.
- CVUpload.objects must exclude soft-deleted CVs.
- CVUpload.all_objects is only for admin/privacy/deletion/internal tasks.
- LLM can extract/explain/suggest but cannot decide final fit score.
```

## Before changing anything

Run these checks and inspect the output:

```bash
git status --short --branch
git log --oneline --decorate -8
git diff --stat
```

If the working tree contains unexpected changes, stop and report.

The baseline report may already be untracked or newly added under:

```text
docs/phases/post_launch/gate_a_baseline_current_damage/
```

Do not delete it.

## Hard exclusions for Gate A.2

Do **not** implement Gate B/C/D/E work.

```text
- Do not overhaul skill taxonomy.
- Do not rebuild skill extraction v2.
- Do not rebuild CV parser v2.
- Do not rematerialize all job skills.
- Do not recompute all matches globally.
- Do not add new ML/LLM logic.
- Do not call external APIs.
- Do not run France Travail ingestion.
- Do not start EN/FR cleanup.
- Do not refactor the whole UI.
- Do not create broad CSS redesign.
- Do not create migrations unless a blocker is proven and reported first.
- Do not print or read real secrets.
- Do not commit.
- Do not push.
```

## Goal

Fix the **production trust defects** discovered during Gate A baseline and manual deploy smoke, without touching Gate B/C intelligence work.

## Required fixes

### 1. Match detail stale after profile skills change

Problem:

- User calculates match for a job.
- User adds skills in profile.
- Recommendations update and show a better score.
- Opening match detail still shows old score/details.

Expected behavior:

```text
For the same user + job + current profile/CV state:
recommendation score and match detail score must agree.
```

Acceptable implementation directions:

```text
- Invalidate existing MatchResult rows when profile skills/CV/profile-relevant data changes; or
- Make match detail detect stale MatchResult and recompute via matching service; or
- Ensure recommendation refresh creates/updates the MatchResult used by the card/detail link.
```

Rules:

```text
- Keep logic in services.
- Do not put matching logic in templates.
- Do not decide fit score with LLM.
- Do not globally recompute every historical match in request/response.
```

Add regression tests.

### 2. Recommendation refresh/list inconsistency

Problem:

- After adding profile skills, recommendation page changes.
- Clicking “Actualiser recommendations” can show a confusing different list.

Expected behavior:

```text
- Refresh with unchanged profile/CV state should be deterministic enough.
- Ordering should be stable with clear tie-breakers.
- Stale and active recommendation handling should not mix old and new states confusingly.
```

Fix in recommendation services/query layer, not templates only.

Add regression tests for stable ordering and active/stale behavior if existing test structure supports it.

### 3. Manual signup CSRF 403 after submit

Problem:

- Manual signup POST caused 403 CSRF after submit.
- Account was still created/logged in after going back.

Expected behavior:

```text
- Manual signup should complete without CSRF 403.
- Account creation and redirect must be atomic from the user perspective.
- No partial success page failure.
```

Investigate allauth signup template/action, CSRF token rendering, redirect handling, middleware, and custom adapter.

Do not disable CSRF protection.

Add regression or targeted view test if feasible.

### 4. Onboarding redirects

Expected flow:

```text
Manual signup:
  signup -> CV step -> profile step

OAuth signup:
  signup/login -> password step if no usable password -> CV step -> profile step

Existing OAuth user without password:
  login -> password step

Existing manual user:
  login -> jobs page or requested next URL, not forced to password step

Existing OAuth user with password:
  login -> jobs page or requested next URL, not forced to password step

If CV missing:
  route to CV step when onboarding is required

If profile incomplete:
  route to profile step when onboarding is required
```

Implementation direction:

```text
- Prefer a small account/onboarding redirect service.
- Adapter/middleware should call this service.
- Avoid scattered redirect if/else in templates.
```

Add tests covering manual signup, OAuth/no-password login redirect logic, and manual login.

### 5. Password stepper status

Problem:

- Password set page progress card shows CV/Profile orange/pending even when already complete.

Expected behavior:

```text
- Password page receives real state:
  has_active_cv
  profile_complete
  has_usable_password
- Stepper dots reflect actual state.
```

Keep template change minimal.

### 6. Password mismatch stale message

Problem:

- On password set and password change, mismatch error appears.
- After correcting both fields, message does not disappear.

Expected behavior:

```text
- Client-side mismatch message clears when both fields match.
- Same behavior on password_set and password_change.
- Server-side errors remain visible when they are real returned form errors.
```

Fix the smallest JS/template issue needed.

Do not rewrite all i18n.

### 7. Password changed security email

Expected behavior:

```text
- When password is changed, user receives a security email.
- Email explains that password was changed.
- Email includes a safe recovery/reset path if the user did not make the change.
```

Existing templates were found:

```text
templates/account/email/password_changed_message.html
templates/account/email/password_changed_message.txt
templates/account/email/password_changed_subject.txt
```

Verify allauth sends the email. If not, add the minimal adapter/signal/service hook.

Do not expose secrets or tokens.

Add test if feasible using Django mail outbox.

### 8. Contact/About false required errors

Problem:

- Contact form shows “required” errors even when fields are filled.

Expected behavior:

```text
- Empty invalid submit shows field errors.
- Valid filled submit does not show required errors.
- Success path works.
```

Likely template-level: hardcoded visible error divs.

Fix minimally.

### 9. CV upload max size 8 MB

Expected behavior:

```text
- PDF CV up to 8 MB accepted.
- >8 MB rejected.
- Config, form validation, UI text, and tests all agree.
```

Do not change CV privacy behavior.

Do not expose CV files publicly.

### 10. /jobs total and filtered count

Expected behavior:

```text
- /jobs page shows total available jobs.
- When filters/search are applied, UI shows filtered result count.
- HTMX/partial updates preserve correct count if applicable.
```

The search service already appears to expose `total_count`; use existing service context instead of duplicating query logic in templates.

### 11. /jobs scroll-to-top button

Expected behavior:

```text
- When user scrolls near bottom, a small scroll-to-top button appears.
- Clicking it scrolls quickly to page top.
```

Keep this minimal. No redesign.

## Tests to run

At minimum:

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

If full suite is too slow, run targeted tests first, then report what was run.

Known current issue context:

```text
apps.recommendations passes.
Full apps.matching apps.recommendations previously had 2 known matching assertion failures caused by temporary UI/i18n markup, not server failure.
Do not reopen broad i18n cleanup here.
```

## Required final agent report

When done, report:

```text
1. Files changed
2. What was fixed
3. Tests added/updated
4. Commands run and results
5. Any defects deferred to Gate B/C/D/E
6. Any risks
7. Git status
```

Do not commit. Do not push.
