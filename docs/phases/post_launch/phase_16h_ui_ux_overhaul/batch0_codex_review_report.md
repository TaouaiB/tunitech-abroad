# Codex Review — Phase 16H Batch 0 Discovery

## Status
NOT READY

## Summary
Gemini correctly identified the overall Phase 16H constraint: this is prototype porting into existing Django templates, not a redesign. The report also correctly called out the About/contact backend gap, the need for global email verification state, the `has_usable_password()` password-step rule, and the CSS source-file rule.

However, the report is not safe enough to approve Batch 1. It states that anonymous Save actions are already restricted, but the current job-list card includes `jobs/partials/save_button.html` unconditionally. That means anonymous users can see a Save form on job cards today, even though the endpoint itself is login-required. Phase 16H explicitly requires hiding Save UI from anonymous users, so this should have been caught as a backend/template state gap.

## Gemini report accuracy
Accurate points:

- Correctly treated Phase 16H as a controlled prototype port, not a creative redesign.
- Correctly mapped the major prototype files to Django templates.
- Correctly identified `/about/` plus real contact backend as missing.
- Correctly identified that email verification banner state should use allauth email verification data.
- Correctly identified `request.user.has_usable_password()` as the basis for Set Password logic.
- Correctly identified `static/src/css/app.css` as the CSS source to edit, not compiled CSS directly.
- Correctly treated `notifications.html` as a toast/state reference only, not a notification feed.

Inaccurate or incomplete points:

- Gemini says anonymous saving is appropriately restricted after checking `saved_jobs.html` and `job_detail.html`. That is incomplete. `templates/jobs/partials/job_card.html` includes `jobs/partials/save_button.html` unconditionally, and the save partial itself has no `user.is_authenticated` guard.
- Gemini says the job detail CTA will "naturally extend" from the current "Test complet" / "Test rapide" logic. That understates the backend/template work. Current `apps/jobs/views.py` only passes `job`, `is_saved`, and `valid_languages`; it does not pass existing user/job match state, profile/CV readiness, or failed/stale match state for the required CTA matrix.
- Gemini's route/template map omits several routes that matter to Batch 3 and settings/account preservation: `dashboard:connections`, `dashboard:delete_account`, `dashboard:delete_account_done`, `dashboard:cv_status`, `matching:detail`, and `matching:feedback`.
- Gemini's likely touched files for Batch 3 omit `templates/dashboard/connections.html`, `templates/dashboard/delete_account.html`, `templates/dashboard/delete_account_done.html`, and `apps/dashboard/test_social_connections.py`.
- Gemini's risky-test list is too narrow. Existing tests contain brittle copy/DOM assertions around base layout, home CTAs, job cards, CV UI, dashboard account/password copy, and auth/allauth behavior.

## Missed routes/templates/backend pieces
Important current routes/templates that Gemini underreported:

- `/dashboard/cv/status/<uuid:public_id>/` -> `templates/cvs/partials/cv_status.html`
- `/dashboard/account/connections/` -> `templates/dashboard/connections.html`
- `/dashboard/settings/delete-account/` -> `templates/dashboard/delete_account.html`
- `/dashboard/settings/delete-account/done/` -> `templates/dashboard/delete_account_done.html`
- `/dashboard/matches/<uuid:public_id>/` -> `templates/matching/match_detail.html`
- `/dashboard/matches/<uuid:public_id>/feedback/`
- `/dashboard/recommendations/<uuid:public_id>/feedback/`

Backend pieces that must be treated as real work in later batches:

- Job detail CTA state needs explicit context/service support for: anonymous, no profile/CV, no match, existing match, and failed/stale/refresh states. Current `MatchResult` has `llm_explanation_status="failed"` but no general match result status field, so "failed/stale" needs careful interpretation against existing data rather than invented state.
- Job-list Save visibility needs a template guard or equivalent context discipline. The endpoint being login-required is not enough.
- Global email verification banner should be backed by a context processor or middleware-style context, because `base.html` needs it globally. It should use allauth `EmailAddress` primary/verified state and respect trusted OAuth behavior already encoded in `apps/accounts/adapters.py`.
- About/contact remains correctly scoped as a real backend feature for Batch 5: model, form, service, Celery task, route/view/template, migration, anti-spam, and tests. A fake static form is not acceptable.

## Rule compliance check
- Prototype porting, not redesign: Gemini mostly complied.
- No UI invention/feature creep: no direct feature creep found in Gemini's report.
- Anonymous/logged-in nav: Gemini understood the locked direction, but the current code does not yet match it. Existing anonymous nav still shows `Analyse CV` and `Comment ça marche`, and logged-in nav includes `CV` plus a broad account dropdown. Batch 1 must correct this without deleting backend dashboard routes.
- Save/Saved visibility: NOT correctly verified. Anonymous Save buttons are present on job cards via unconditional partial inclusion.
- Dynamic job detail CTA: NOT fully verified. Current backend context is insufficient for the required matrix.
- Password step: correctly identified as `not request.user.has_usable_password()`.
- Verified primary email: mostly correctly identified, but implementation must avoid repeated template queries and must account for trusted OAuth-created verified allauth email rows.
- Global banner backend: correctly identified.
- About/contact backend: correctly identified.
- Notifications reference: correctly identified as state/toast only.
- CSS strategy: correctly identified.
- Risky tests: incomplete.

## Batch 1 readiness
NOT READY

Batch 1 should not start from Gemini's report as-is. The discovery report needs correction first, mainly because it gives a false PASS on anonymous Save visibility and understates job detail CTA state work. Starting Batch 1 with that report risks carrying incorrect assumptions into global navigation and later jobs work.

## Required corrections before Batch 1
- Amend the discovery report to state that anonymous Save UI is currently exposed on job-list cards through `templates/jobs/partials/job_card.html` and `templates/jobs/partials/save_button.html`.
- Amend the Batch 2 gap list to include explicit Save UI hiding for anonymous job cards, not only job detail.
- Amend the job detail CTA section to say current view/template lacks the required CTA state context and needs a focused service/context addition.
- Add the omitted account/settings/delete/CV status/match feedback routes and templates to the mapping.
- Expand risky tests to include at least:
  - `apps/jobs/tests/test_views.py`
  - `apps/core/test_home_cta.py`
  - `apps/core/tests/test_ui.py`
  - `apps/dashboard/tests.py`
  - `apps/dashboard/test_social_connections.py`
  - `apps/cvs/tests/test_views.py`
  - `apps/accounts/tests.py`
  - relevant `apps/matching/tests.py` view assertions
- Keep Batch 1 scoped to global shell, nav, banner, toasts, and CSS source changes only. Do not start jobs/template CTA work in Batch 1.

## Commands run
```bash
sed -n '1,240p' docs/phases/post_launch/phase_16h_ui_ux_overhaul/rules_lock.md
sed -n '1,260p' docs/phases/post_launch/phase_16h_ui_ux_overhaul/page_mapping.md
sed -n '1,260p' docs/phases/post_launch/phase_16h_ui_ux_overhaul/batch_plan.md
sed -n '1,260p' docs/phases/post_launch/phase_16h_ui_ux_overhaul/review_checklist.md
sed -n '1,320p' docs/phases/post_launch/phase_16h_ui_ux_overhaul/batch0_discovery_report.md
rg -n "path\(|include\(|urlpatterns|about|dashboard|recommendations|saved|email-preferences|quick-match|match" config apps -g 'urls.py'
rg -n "has_usable_password|EmailAddress|emailaddress_set|verified|primary|ACCOUNT_EMAIL_VERIFICATION|SOCIALACCOUNT|ACCOUNT_" config apps templates
rg -n "Save|Saved|save|saved|unsave|quick|Test complet|Test rapide|View score|match|recommend" templates/jobs templates/dashboard templates/matching templates/recommendations apps/jobs apps/matching apps/dashboard apps/recommendations
rg --files templates apps static/src/css docs/design/phase_16h/prototype
nl -ba templates/base.html | sed -n '1,230p'
nl -ba templates/jobs/job_detail.html | sed -n '1,150p'
nl -ba templates/jobs/partials/job_card.html | sed -n '1,150p'
nl -ba templates/jobs/partials/save_button.html | sed -n '1,80p'
nl -ba apps/jobs/views.py | sed -n '1,240p'
nl -ba apps/dashboard/views.py | sed -n '1,240p'
nl -ba apps/jobs/services/search.py | sed -n '1,260p'
nl -ba apps/jobs/services/query.py | sed -n '1,220p'
nl -ba apps/matching/views.py | sed -n '1,240p'
nl -ba apps/accounts/adapters.py | sed -n '1,220p'
nl -ba apps/accounts/services/account_provisioning.py | sed -n '1,220p'
nl -ba apps/core/views.py apps/core/urls.py | sed -n '1,180p'
nl -ba config/settings/base.py | sed -n '80,140p'
nl -ba apps/jobs/tests/test_views.py | sed -n '1,260p'
nl -ba apps/core/tests.py apps/core/test_home_cta.py apps/core/tests/test_ui.py | sed -n '1,260p'
nl -ba apps/dashboard/tests.py apps/dashboard/test_social_connections.py | sed -n '1,260p'
rg -n "assertContains|assertNotContains|Offres|Favoris|Connexion|Créer|Dashboard|Tableau|Sauvegarder|Test rapide|Test complet|profile|password|has_usable|email" apps/*/tests.py apps/*/tests -g '*.py'
rg -n "class MatchResult|status|failed|stale|is_stale|match_confidence|created_at|updated_at" apps/matching/models.py apps/matching/services -g '*.py'
nl -ba apps/matching/models.py | sed -n '60,155p'
nl -ba apps/matching/services/match_result.py | sed -n '1,140p'
nl -ba templates/dashboard/account.html templates/dashboard/connections.html | sed -n '1,180p'
nl -ba apps/core/models.py apps/core/tasks.py | sed -n '1,240p'
git status --short --branch
python manage.py check --settings=config.settings.local
```

Final check results:

```text
git status --short --branch
## dev...origin/dev
?? docs/phases/post_launch/phase_16h_ui_ux_overhaul/batch0_codex_review_report.md
?? docs/phases/post_launch/phase_16h_ui_ux_overhaul/batch0_discovery_report.md

python manage.py check --settings=config.settings.local
System check identified no issues (0 silenced).
```

## Phase boundary confirmation
Review-only pass completed. No UI, CSS, template, backend, migration, or test code was changed. No commit was made. Batch 1 was not started.
