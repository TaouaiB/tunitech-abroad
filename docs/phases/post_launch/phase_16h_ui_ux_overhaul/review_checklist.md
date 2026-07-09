# Phase 16H Review Checklist

## Use this checklist for every batch

A batch is not approved until all applicable checks pass.

## Global architecture checks

- [ ] No React/Next/Vue/Angular/SPA added.
- [ ] Views remain thin.
- [ ] Business logic is in services.
- [ ] Celery tasks call services only.
- [ ] Models do not call external APIs.
- [ ] No OpenRouter/LLM calls from views.
- [ ] No final score logic moved to LLM.
- [ ] Public routes use UUID `public_id`, not internal IDs.
- [ ] CV privacy preserved.
- [ ] No secrets added to repo, logs, docs, or `.env.example` values.
- [ ] No production deployment performed.

## Visual fidelity checks

- [ ] Prototype visual hierarchy preserved.
- [ ] Colors match approved prototype/design tokens.
- [ ] Button hierarchy matches prototype.
- [ ] Card style matches prototype.
- [ ] Spacing is consistent with prototype.
- [ ] Mobile layout matches prototype intent.
- [ ] Dark mode still works.
- [ ] No invented icons/emoji/sections.
- [ ] No new visual theme invented by agent.
- [ ] Large inline CSS was not added to templates.
- [ ] `static/src/css/app.css` is the source CSS file if CSS changes are needed.

## Auth/nav checks

Logged-out state:

- [ ] Shows Jobs.
- [ ] Shows Recommendations leading to auth with next.
- [ ] Shows About.
- [ ] Shows Sign in / Get started.
- [ ] Does not show Saved.
- [ ] Does not show Profile.
- [ ] Does not show Settings.
- [ ] Does not show Sign out.
- [ ] Does not show Save buttons.

Logged-in state:

- [ ] Shows Jobs.
- [ ] Shows Recommendations.
- [ ] Shows Saved.
- [ ] Shows Profile.
- [ ] Shows Settings.
- [ ] Shows About.
- [ ] Shows Sign out.
- [ ] Save buttons visible where appropriate.

## Email verification banner checks

- [ ] Hidden for anonymous user.
- [ ] Hidden for verified email user.
- [ ] Hidden for trusted OAuth verified user.
- [ ] Visible for authenticated unverified primary email user.
- [ ] Resend confirmation behavior uses allauth-compatible flow.
- [ ] No raw email/provider exception shown to user.
- [ ] Banner disappears once verified.

## Job/list/detail checks

- [ ] Public users can browse jobs.
- [ ] Public users can view job detail.
- [ ] Public users do not see Save.
- [ ] Logged-in users can save/unsave.
- [ ] HTMX save/unsave still works.
- [ ] France-only locked/default state is clear.
- [ ] No fake countries added.
- [ ] No Postulate English copy; use Apply.
- [ ] French Postuler is acceptable.

## Job detail CTA checks

- [ ] Logged out sees sign-in/check recommendations CTA.
- [ ] Logged in no CV/profile sees complete profile/upload CV CTA.
- [ ] Logged in profile/CV and no match sees check/calculate match CTA.
- [ ] Logged in existing match sees view score CTA.
- [ ] Failed/stale match gets retry/refresh CTA.
- [ ] No score shown if no score exists.
- [ ] Backend quick-match logic not removed.

## Profile/password checks

- [ ] Password step uses `not user.has_usable_password()`.
- [ ] OAuth user without password sees Set Password step.
- [ ] Email/password user skips Set Password step.
- [ ] OAuth user after setting password no longer sees Set Password step.
- [ ] Backend password policy not weakened.
- [ ] UI password copy matches backend validators.

## States/toasts checks

- [ ] Empty states used where real data is empty.
- [ ] Loading skeletons used where appropriate.
- [ ] Failure states are compact and safe.
- [ ] Toasts follow prototype/state reference.
- [ ] `notifications.html` was not implemented as a real page.
- [ ] No notification bell/feed/model added.

## About/contact backend checks

- [ ] `/about/` route exists if About batch is implemented.
- [ ] Form has CSRF.
- [ ] Validation exists.
- [ ] ContactMessage or equivalent DB record exists.
- [ ] DB record is created before Celery email task.
- [ ] Service layer owns business logic.
- [ ] Celery task calls service.
- [ ] No raw exception in UI/logs.
- [ ] Anti-spam control exists.
- [ ] Tests cover success/failure/safety.

## Test/command checks

Every batch should run at minimum:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
git diff --check
```

Run focused tests for touched areas.

Run full suite at final phase gate and when backend changes are made.

If CSS changes are made, run the project Tailwind build/check command used by this repo.

## Agent report required fields

Every agent report must include:

```text
Status: PASS/FAIL
Files changed
Prototype files used
Rules followed
Intentional deviations from prototype
Backend behavior preserved
Tests/commands run with exact results
Known risks
Phase boundary confirmation
No commit/deploy confirmation
```
