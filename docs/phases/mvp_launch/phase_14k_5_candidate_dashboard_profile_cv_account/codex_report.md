# Codex Report - Phase 14K-5 Candidate Dashboard, Profile, CV, Account

## Final verdict

REPAIRED_PASS

Codex inspected the Phase 14K-5 dashboard/profile/CV/account/email preference work, repaired small in-scope template issues, rebuilt CSS, and verified the final worktree with the required checks.

## Files changed by Codex

- `templates/dashboard/profile.html`
- `templates/dashboard/cv_manage.html`
- `templates/dashboard/email_preferences.html`
- `templates/cvs/partials/cv_status.html`
- `static/css/app.css` via `npm run css:build`
- `docs/phases/phase_14k_5_candidate_dashboard_profile_cv_account/codex_report.md`

Files already changed before Codex verification and left in scope:

- `templates/dashboard/home.html`
- `templates/dashboard/account.html`
- `templates/dashboard/sidebar.html`
- `docs/phases/phase_14k_5_candidate_dashboard_profile_cv_account/agent_report.md`
- phase prompt/task/acceptance docs under `docs/phases/phase_14k_5_candidate_dashboard_profile_cv_account/`

## Scope verification

- Only private dashboard/profile/CV/account/email preference templates, one directly used CV status partial, generated CSS, and phase docs are changed.
- No backend Python, URLs, settings, migrations, dependencies, or tests were modified.
- No public job, matching detail/history, recommendations, saved jobs, auth, legal, or homepage templates were redesigned by Codex.
- Phase 14K-6 was not started.

## Repairs performed

- Repaired CV status copy from English to approved French labels:
  - pending -> `En attente`
  - processing -> `Analyse du CV en cours`
  - parsed -> `Analyse terminee`
  - parsed_with_warnings -> `Analyse terminee avec avertissements`
  - failed -> `Analyse echouee`
- Added a French local-development note in the CV status partial.
- Added profile back link, visible section landmarks, completion status label, and accessible progressbar attributes.
- Replaced non-existent `tta-alert-error` usage in touched forms with explicit Tailwind alert utilities.
- Replaced incorrect `tta-sticky-save` with existing `tta-sticky-save-bar`.
- Removed inline submit JavaScript from profile and email preference submit buttons so native form submission/validation behavior remains intact.
- Added persistent private-CV messaging to the empty CV state.
- Added a proper file input label association and `tta-dropzone` class to the CV upload UI while preserving the existing file field.
- Cleaned trailing whitespace found by `git diff --check`.

## Route verification

Verified current URL names in `apps/dashboard/urls.py`, `apps/jobs/urls.py`, and `apps/matching/urls.py`.

Existing routes used by Phase 14K-5 templates:

- `dashboard:home`
- `dashboard:profile`
- `dashboard:cv`
- `dashboard:cv_status` with `cv.public_id`
- `dashboard:recommendations`
- `dashboard:saved_jobs`
- `dashboard:email_preferences`
- `dashboard:account`
- `dashboard:connections`
- `dashboard:delete_account`
- `jobs:list`
- allauth routes `account_change_password` and `account_set_password`

No invented route was found. No `matching:quick_match` link was added. No public integer URL was added.

## Route smoke

Ran a Django test-client smoke check with `HTTP_HOST='localhost'` for existing private pages:

```text
/dashboard/ 200
/dashboard/profile/ 200
/dashboard/cv/ 200
/dashboard/email-preferences/ 200
/dashboard/account/ 200
```

The first smoke attempt failed due to a malformed one-line shell command (`SyntaxError`) before the app was exercised. It was rerun as a proper stdin script and passed.

## UI/design verification

- Dashboard pages use the approved private app grid/sidebar pattern.
- Profile page now has clearer section markers matching the approved profile form structure.
- CV page keeps the active CV card, upload/replace card, privacy line, status polling partial, and delete modal behavior.
- Account/security page keeps account summary, password action, linked accounts action, and danger zone.
- Email preferences page preserves the existing preference form and adds consistent explanatory copy.
- Final CSS was regenerated with Tailwind.

## CV privacy verification

- No `file.url`, `cv.file.url`, or `upload.file.url` appears in the dashboard/CV templates.
- No `raw_text`, `raw_request_json`, `raw_response_text`, or `raw_response_json` appears in the touched templates.
- CV page displays only safe parsed summary fields from the existing `cv_parsed_summary.html` partial.
- Delete form uses `active_cv.public_id`, not an internal integer ID.
- CV status polling uses `cv.public_id`.
- The required private file line remains visible: file is private and not shared with employers.

## Form behavior verification

- Profile form preserves `method="post"`, CSRF, hidden fields, field rendering, suggestions, field errors, non-field errors, and submit behavior.
- CV upload form preserves `method="post"`, `enctype="multipart/form-data"`, CSRF, `{{ form.file }}`, `{{ form.consent_accepted }}`, file errors, consent errors, and Alpine upload state.
- CV delete form preserves `method="post"`, CSRF, and hidden `delete_cv_id` with `active_cv.public_id`.
- Email preferences form preserves `method="post"`, CSRF, hidden fields, checkbox fields, non-field errors, and submit behavior.
- Account page preserves allauth password links, social connection route, and delete account route.

## Commands and results

Required checks on final state:

```text
python manage.py check --settings=config.settings.local
Result: PASS - System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
Result: PASS - No changes detected.

python manage.py test --settings=config.settings.local --parallel 1
Result: PASS - Ran 440 tests in 73.224s, OK.

npm run css:build
Result: PASS - Done in 679ms.
Note: Browserslist/caniuse-lite maintenance warning only.

python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
Result: PASS - 1 static file would be copied, 135 unmodified.

git diff --check
Result: PASS.

git diff --cached --check || true
Result: PASS / no staged diff issues.
```

## Security grep classification

```text
grep -R "cdn.tailwindcss.com" templates config static -n || true
Result: no matches.

grep -R "FranceTravailClient|search_offers|api.francetravail" apps/*/admin.py apps/*/views.py templates -n
Result: no matches.

grep -R "OpenRouterClient|OPENROUTER|run_llm|client.chat|_make_request" apps/*/admin.py apps/*/views.py templates -n
Result: no matches.

grep -R "<int:" apps templates config -n
Result: no matches.

secret diff grep
Result: OK: no obvious secrets in diff.
```

Non-blocking grep findings:

- `React`, `Next.js`, `Vite`, `vue`, and `angular` matches are existing skill taxonomy, job fixture, placeholder, and test content. They are not frontend stack implementation.
- `raw_text`, `raw_request_json`, `raw_response_text`, and `raw_response_json` matches are existing backend models/services/tests/admin exclusions. They are not exposed by Phase 14K-5 templates.

## Blocking issues

None.

## Commit recommendation

Do not commit automatically. Recommended commit after review:

```bash
git add static/css/app.css templates/dashboard/home.html templates/dashboard/profile.html templates/dashboard/cv_manage.html templates/dashboard/account.html templates/dashboard/email_preferences.html templates/dashboard/sidebar.html templates/cvs/partials/cv_status.html docs/phases/phase_14k_5_candidate_dashboard_profile_cv_account/
git commit -m "Complete Phase 14K-5 candidate dashboard polish"
```
