# Phase 16H-R0 — CV Consent Removal Report

## Discovery Results
A grep for `consent_accepted`, `CVConsentForm`, and other consent-related strings revealed that the separate consent checkbox requirement for CV uploads was deeply integrated across:
- `apps/cvs/forms.py`
- `apps/cvs/services/upload.py`
- `apps/dashboard/views.py`
- `templates/dashboard/cv_manage.html`
- Multiple test files in `apps/cvs` and `apps/recommendations`.

## Files Changed
- `apps/cvs/forms.py` (Removed `consent_accepted` field)
- `apps/cvs/services/upload.py` (Removed consent requirement and `ConsentService` logging from CV upload flow)
- `apps/dashboard/views.py` (Removed `consent_accepted` from form processing)
- `templates/dashboard/cv_manage.html` (Removed the UI checkbox and related script)
- `apps/cvs/tests/test_views.py` (Removed UI validation checks for the checkbox)
- `apps/cvs/tests/test_services.py` (Removed `consent_accepted` keyword args, removed test for failure on no consent)
- `apps/recommendations/tests/test_integration.py` (Removed `consent_accepted` kwargs)
- `docs/design/approved_ui_ux/design_vision/06_page_specs_private_dashboard.md` (Removed "consent required." from specs)

## Exact Consent References Removed
- "Je consens au traitement de mon CV pour la création de mon profil."
- "Consentement au traitement des données"
- "J'accepte que mon CV soit analysé par le système pour extraire mes compétences."
- `consent_accepted` from forms, services, and views.

## Backend Behavior Changed
Uploading a CV via `CVUploadService.upload_cv()` no longer requires `consent_accepted=True` as an argument. The internal block that recorded `cv_processing` via `ConsentService` during upload has also been removed. A valid CV upload is now recognized as implicit consent to process.

## Tests Updated/Added
- `test_upload_cv_no_consent` in `test_services.py` was removed since an explicit consent check is no longer done.
- Removed assertions expecting `consent_accepted` element in `test_views.py`.
- Corrected numerous upload service test calls across the test suite to omit `consent_accepted`.

## Docs Updated/Created
- Created: `docs/planning/post_launch/decision_cv_upload_no_separate_consent_checkbox.md` explaining the decision.
- Updated: `docs/design/approved_ui_ux/design_vision/06_page_specs_private_dashboard.md` to remove the consent constraint.

## Prototype Folder Verification
Verified `docs/design/phase_16h/prototype_full_v16/` exists (did not modify it as per rules).

## Commands Run with Exact Results
1. `python manage.py check` - System check identified no issues (0 silenced).
2. `python manage.py makemigrations --check --dry-run` - No changes detected.
3. `python manage.py test` - All tests passed successfully.
4. `npm run css:build` - CSS rebuilt successfully.

## Remaining Consent References and Why They Are Acceptable/Historical
- `ConsentService` remains in `apps/privacy/services/consent.py` and is used elsewhere (e.g., for email preferences).
- Other historical `docs/phases/` MD files still contain references to the old flow. These are preserved as historical artifacts according to the prompt's instruction.

## Confirmation
- no separate CV consent checkbox remains
- valid CV upload works without consent_accepted
- CV privacy still intact
- PDF validation still intact
- no models/migrations unless justified
- no LLM/OpenRouter changes
- no France Travail/search changes
- no matching/recommendation changes
