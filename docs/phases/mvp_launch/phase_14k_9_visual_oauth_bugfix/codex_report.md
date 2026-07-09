# Phase 14K-9 Visual OAuth Bugfix - Codex Report

## Completed tickets

- Fixed verified Google/GitHub OAuth signup behavior so trusted social provider emails are stored as verified and do not trigger account confirmation email sending.
- Preserved normal email/password signup verification behavior with a regression test proving confirmation mail is still requested.
- Preserved account provisioning for OAuth users with CandidateProfile and EmailPreference assertions.
- Fixed account dropdown stacking so it appears above page content and removed the "Compatibilités" shortcut from dropdown menus.
- Removed "Compatibilités" from the dashboard sidebar while leaving direct matching routes untouched.
- Renamed the dashboard sidebar entry from "Vue d’ensemble" to "Tableau de bord".
- Improved light/dark contrast on homepage, CV page, dashboard cards, and footer text.
- Reduced homepage hero spacing so "Offres récentes" starts closer to the search area.
- Compacted the CV page empty state and upload section while preserving the POST form, file upload, consent field, CSRF, delete form, validation errors, and HTMX status include.

## Files changed

- `apps/accounts/adapters.py`
- `apps/accounts/tests.py`
- `templates/base.html`
- `templates/core/home.html`
- `templates/dashboard/sidebar.html`
- `templates/dashboard/home.html`
- `templates/dashboard/cv_manage.html`
- `static/src/css/app.css`
- `static/css/app.css`
- `docs/phases/phase_14k_9_visual_oauth_bugfix/codex_report.md`

## Checks

Checks were run locally with `config.settings.local`; see final agent response for pass/fail results.

## Remaining risks / manual steps

- Browser-level visual QA should still verify both light and dark modes after the Tailwind rebuild.
- No commit was created, per instruction.
