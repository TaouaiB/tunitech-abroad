# Phase 16H-R0 Codex Review Report

## Verdict
REPAIR REQUIRED

## Summary
Runtime implementation is correct for the product-owner decision: CV upload no longer requires or renders a separate processing-consent checkbox, and valid PDF upload works through the form/service path without `consent_accepted`.

Privacy, PDF validation, ownership checks, delete flow, private storage, public UUID routes, and CV safe-manager behavior remain intact.

The remaining blocker is documentation-only: two current approved design documents still instruct future agents to preserve or render a CV consent checkbox.

## Consent removal review
- active checkbox removed: Yes. `templates/dashboard/cv_manage.html` no longer renders the consent checkbox or related script, and the app-only consent grep returned no hits.
- backend requirement removed: Yes. `CVUploadForm` only includes `file`, and `CVUploadService.upload_cv(user, uploaded_file)` no longer accepts or validates `consent_accepted`.
- tests updated: Yes. CV service/view tests and recommendation integration tests were updated to call upload without `consent_accepted`; full tests pass.
- remaining references: No active app/template references. Historical/planning references remain in older docs and in the Phase 16H-R0 prompt/report materials. Current approved design docs still include two actionable checkbox references listed under Required repairs.

## Privacy/security review
- private CV storage: Preserved. `CVUpload.file` still uses `PrivateMediaStorage`, and `PrivateMediaStorage.url()` still raises `ValueError`.
- PDF validation: Preserved. Form validation still rejects non-PDF extension/content type, and service validation still checks extension, MIME type, size, and `%PDF-` magic bytes.
- owner checks: Preserved. CV status uses `get_object_or_404(CVUpload.objects, user=request.user, public_id=public_id)`, and delete uses `CVUpload.objects.get(user=user, public_id=cv_public_id)`.
- file URL exposure: No new exposure found. Diff grep for `cv.file.url`, `file.url`, `MEDIA_URL`, `private_media`, and unsafe `CVUpload.all_objects` usage returned no relevant hits.

## Architecture review
- views/services/forms: Acceptable. The dashboard view remains thin and delegates upload/delete behavior to services; validation remains in form/service layers.
- forbidden backend scope: No model, migration, settings, jobs, matching, LLM, France Travail, or search implementation changes found. The only grep hit was `apps/recommendations/tests/test_integration.py`, limited to test call-site updates for the upload service signature.
- LLM/OpenRouter: No implementation changes.
- France Travail/search: No changes.
- matching/recommendations: No implementation changes; only recommendation integration tests were updated for the upload service signature.
- migrations: None. `makemigrations --check --dry-run` reported no changes detected.

## Docs review
`docs/planning/post_launch/decision_cv_upload_no_separate_consent_checkbox.md` exists and explicitly states that upload itself is the user action and overrides older v1 docs requiring a separate checkbox.

Editable approved design docs were partially updated:
- `docs/design/approved_ui_ux/design_vision/08_forms_auth_cv_profile_spec.md` removed the upload-card consent checkbox and consent copy.
- `docs/design/approved_ui_ux/static_ui_prototype/cv.html` removed the prototype checkbox.
- `docs/design/approved_ui_ux/design_vision/06_page_specs_private_dashboard.md` removed one `consent required` bullet.

However, current approved design docs still include actionable checkbox instructions:
- `docs/design/approved_ui_ux/design_vision/06_page_specs_private_dashboard.md:151` still lists `consent checkbox` under the CV upload/replace card.
- `docs/design/approved_ui_ux/design_vision/11_page_by_page_final_blueprint.md:201` still lists `consent checkbox` under `/dashboard/cv/` "Must preserve".

No binary PDFs were edited.

## Tests/checks run
- `git status --short --branch`: branch `dev...origin/dev`; implementation/doc files modified; prompt pack and decision/report docs untracked before this review report was created.
- `git diff --stat`: 10 tracked files changed, 13 insertions, 60 deletions before this review report.
- `git diff --name-status`: tracked changes limited to CV form/service/tests, dashboard view/template, recommendation integration tests, and approved design docs/prototype.
- active consent grep across `apps templates docs`: app/templates clean; remaining hits are older planning/phase docs, Phase 16H-R0 materials, and the two current approved design doc blockers.
- app-only consent grep across `apps templates`: no hits.
- backend forbidden scope grep: only `apps/recommendations/tests/test_integration.py`.
- privacy exposure grep: no hits.
- public integer URL grep: no hits.
- `python manage.py check --settings=config.settings.local`: passed, no issues.
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`: passed, no changes detected.
- `python manage.py test apps.cvs apps.dashboard apps.privacy apps.core --settings=config.settings.local`: passed, 154 tests OK.
- `python manage.py test --settings=config.settings.local`: passed, 643 tests OK.
- `npm run css:build`: passed; Browserslist emitted the standard outdated `caniuse-lite` notice.
- `git diff --check`: passed.

## Required repairs
- Remove or rewrite `consent checkbox` at `docs/design/approved_ui_ux/design_vision/06_page_specs_private_dashboard.md:151`.
- Remove or rewrite `consent checkbox` at `docs/design/approved_ui_ux/design_vision/11_page_by_page_final_blueprint.md:201`.
