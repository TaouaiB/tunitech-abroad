Read this entire prompt and execute it exactly.

# Phase 14E — Production Auth / Profile / Privacy Hotfix

## Mission

Fix production-blocking user account issues before any more ingestion/recommendation work.

Current production problems:

1. Google OAuth works at redirect level, but existing users with the same Gmail are treated like a duplicate signup and sent to email confirmation.
2. OAuth login with trusted verified providers should not require email confirmation.
3. Account deletion shows “Suppression en cours” and stays pending; for MVP it must delete immediately after confirmation.
4. Profile completeness gating is wrong: UI says “Profil incomplet minimum 50% requis” even when profile score is above 50%.
5. These fixes must work without relying on Celery/background workers.

Do not implement automated France Travail ingestion in this phase. That is Phase 14F.

## Hard rules

* Do not commit.
* Do not deploy.
* Do not start Phase 14F.
* Do not modify real `.env`.
* Do not print secrets.
* Do not add React, Next.js, Angular, FastAPI, SQLAlchemy, MongoDB, or SPA architecture.
* Keep Django templates + HTMX + Tailwind only.
* Views stay thin.
* Business logic goes in services/adapters.
* No OpenRouter/LLM calls from Django views.
* No France Travail live API calls from user-facing pages.
* CV files must remain private.
* Public URLs must use UUID `public_id`, never internal integer IDs.

Final verdict must be only:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Never write PASS before Baha manual Chrome approval.

## Important working-tree rule

The repository is already dirty from previous phases. Do not revert unrelated changes. Do not clean unrelated phase files. Only edit files needed for Phase 14E.

If you discover unrelated broken code, report it but do not refactor it unless it blocks Phase 14E tests.

## Ticket 14E-001 — Fix Google OAuth existing-account login

### Required behavior

When a user clicks “Continue with Google”:

#### Case A — Existing local account with same email

If a local user already exists with that email and Google returns a verified email:

* Log into the existing user.
* Auto-connect the Google social account to that user if not already connected.
* Do not create a duplicate user.
* Do not send duplicate signup warning email.
* Do not send email confirmation email.
* Do not redirect to `/accounts/confirm-email/`.

#### Case B — New user through Google

If no local user exists and Google returns a verified email:

* Create the user.
* Mark email as verified.
* Log user in.
* Provision candidate profile if required by current app logic.
* Do not require email confirmation.

#### Case C — Future OAuth providers

Do not blindly trust every provider.

* Google verified email may be trusted.
* For GitHub/future OAuth, only auto-link if the provider explicitly returns a verified email.
* If provider email is missing or unverified, do not auto-link to an existing local account automatically.

### Implementation guidance

Inspect current django-allauth version and current settings/adapters.

Possible implementation paths:

* settings-based allauth configuration if safe for the installed version;
* custom `SocialAccountAdapter`;
* account provisioning service;
* signal logic cleanup.

The final behavior must be tested, not only configured.

### Tests required

Add or update tests proving:

* Existing local user + Google verified email logs in / connects, no duplicate signup email.
* New Google verified email creates usable account without email confirmation.
* Unverified provider email does not auto-link silently.
* Existing normal email/password login still works.
* Email confirmation still applies to normal email signup if the app requires it.

## Ticket 14E-002 — Remove wrong OAuth confirmation UX

The user should not see:

```text
Vérifiez votre boîte mail
Nous vous avons envoyé un email de confirmation...
```

after successful verified Google OAuth login.

Fix redirects/templates/settings/adapters so verified OAuth login goes to the normal logged-in destination, likely dashboard.

Do not hide the problem only in the template. Fix the flow.

## Ticket 14E-003 — Immediate account deletion for MVP

Current production UX says deletion is processing:

```text
Suppression en cours
Votre demande de suppression a été enregistrée...
```

For this MVP, that is wrong.

### Required behavior

After authenticated user confirms deletion:

* Delete account immediately in the request/response cycle through a service.
* Do not rely on Celery.
* Delete or soft-delete user-owned data according to existing privacy architecture.
* CV uploads/files must be cleaned or marked deleted according to existing CV privacy rules.
* Saved jobs, recommendations, match results, profile data, notification preferences, sessions/tokens/social accounts must not remain usable.
* User is logged out.
* Redirect to a simple success/goodbye page.
* No permanent “processing” state for the user.

### Architecture

* View must stay thin.
* Create/update service such as `AccountDeletionService` or existing privacy deletion service.
* If an existing deletion-request model exists, it may be kept for audit/admin, but the user-facing deletion must complete immediately.
* No background worker required.

### Tests required

* Deletion requires authenticated user.
* POST confirmation deletes/deactivates account immediately.
* User cannot log in afterward.
* User session is ended.
* CVUpload privacy/soft-delete behavior is respected.
* No pending deletion message remains for completed immediate deletion.

## Ticket 14E-004 — Fix profile completeness gating

Current bug:

```text
Profil Incomplet (minimum 50% requis)
```

appears even when profile percentage is above 50%.

### Required behavior

* One service is the source of truth for profile completeness.
* If completeness score is `>= 50`, recommendation/matching unlock gates must not show “Profil incomplet”.
* If score is `< 50`, gate may show the warning.
* CV parsing/profile update must recalculate or read fresh completeness.
* Dashboard/profile/recommendations must agree on the same score.
* Do not hardcode different thresholds in different templates/services.

### Tests required

* Profile score 49 blocks recommendation gate.
* Profile score 50 unlocks.
* Profile score above 50 unlocks.
* CV parsing/profile update recalculates or exposes updated score.
* Template/context uses same service/field as recommendation service.

## Ticket 14E-005 — Production compatibility checks

This phase must work on Render Free-style deployment where there might be:

* no pre-deploy command;
* no Celery worker;
* only web service + database.

So:

* OAuth login must work without Celery.
* Account deletion must work without Celery.
* Completeness gating must work without Celery.
* No code should assume production has local media permanence for CV files beyond current app storage behavior.

## Ticket 14E-006 — UI copy cleanup

Remove confusing user-facing text related to these bugs.

### OAuth

Do not show email confirmation after verified OAuth login.

### Delete account

Do not show “Suppression en cours” after immediate deletion.

Use simple copy like:

```text
Votre compte a été supprimé.
```

or French equivalent consistent with existing UI.

### Profile completeness

Show accurate score and accurate action.

If complete enough:

```text
Profil prêt pour les recommandations
```

If incomplete:

```text
Complétez votre profil pour améliorer vos recommandations
```

Do not show contradictory warnings.

## Regression/security checks

Run and report:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.accounts apps.profiles apps.privacy apps.dashboard apps.recommendations apps.cvs --settings=config.settings.local
python manage.py test --settings=config.settings.local
git diff --check
git status --short
git diff -- . ':!.env' | grep -iE "OPENROUTER_API_KEY|FRANCE_TRAVAIL_CLIENT_SECRET|client_secret|access_token|password|secret" || echo "OK: no obvious secrets in diff"
```

Also run grep checks:

```bash
grep -R "OpenRouter\|OPENROUTER\|llm\|LLM" apps/*/views.py apps/*/views -n 2>/dev/null || true
grep -R "FranceTravailClient\|search_offers\|api.francetravail" apps/accounts apps/dashboard apps/profiles apps/privacy apps/recommendations templates -n 2>/dev/null || true
grep -R "file.url\|cv.file.url\|raw_text" templates -n 2>/dev/null || true
grep -R "Suppression en cours\|minimum 50% requis" templates apps -n 2>/dev/null || true
```

The last grep may show tests or old docs only if intentionally kept; user-facing templates should be fixed.

## Manual proof commands to include in report

Include shell snippets or test proof for:

1. Existing user + Google verified email can authenticate without duplicate signup.
2. OAuth verified login does not create EmailConfirmation requirement.
3. Immediate deletion changes account state immediately.
4. Profile score `>= 50` unlocks recommendations.

Do not expose real personal secrets.

## Deliverables

Create or update:

```text
docs/phases/phase_14e_auth_profile_privacy_hotfix/
```

Include:

```text
implementation_plan.md
task.md
agent_report.md
```

But do not stop after creating the plan. Implement the phase automatically.

Final `agent_report.md` must include:

```text
# Phase 14E Agent Report

## Verdict
FAIL or BLOCKED_HUMAN_VISUAL_SIGNOFF

## Summary

## Files changed

## OAuth proof

## Immediate deletion proof

## Profile completeness proof

## Commands run

## Security/regression checks

## Remaining risks

## Browser/manual status
Baha manual Chrome signoff: pending
```

## Acceptance criteria

Phase 14E is acceptable only when:

* Google OAuth verified email logs into existing account with same email.
* No duplicate-signup warning email for trusted verified Google OAuth login.
* New verified Google OAuth account does not require email confirmation.
* Unverified future OAuth provider emails are not auto-linked blindly.
* Account deletion completes immediately for MVP and does not stay pending.
* Profile completeness gate uses one threshold and unlocks correctly at `>= 50`.
* No Celery worker is required for these three features.
* All required tests/checks pass.
* No secrets are printed.
* No deployment or commit is performed.

Remember: final verdict cannot be PASS. Use `BLOCKED_HUMAN_VISUAL_SIGNOFF` if code/tests pass and only Baha Chrome signoff remains.
