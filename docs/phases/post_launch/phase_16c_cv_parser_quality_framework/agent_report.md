# Phase 16C Agent Report

## Completed Tickets
- **TTA-16C-001 — CVNameExtractionService**: Implemented `CVNameExtractionService` which extracts names with confidence and specific rules to reject common incorrect parsing (e.g. "je me suis", job titles, section headers).
- **TTA-16C-002 — Parser confidence and warnings**: Updated `CVDeterministicExtractorService` and `CVParsingService` to track name, email, phone, and url confidence. Low-confidence names (<70) are not propagated to profiles.
- **TTA-16C-003 — Private CV audit corpus structure**: Added `private_test_corpus/` to `.gitignore` and added `README.md` to document usage policies along with a fake data example.
- **TTA-16C-004 — audit_cv_parser command**: Implemented `CVParserAuditService` and `audit_cv_parser` management command which adheres to the shared diagnostics contract.
- **TTA-16C-005 — Parser metrics and regression tests**: Created `apps/cvs/tests/test_name_extractor.py` to cover French and English bad cases.
- **TTA-16C-006 — Correction capture foundation**: Created the `CVFieldCorrection` model and registered it with Django Admin to capture corrections and their sources.

## Files Changed
- `apps/cvs/models.py` (modified)
- `apps/cvs/admin.py` (modified)
- `apps/cvs/services/name_extractor.py` (new)
- `apps/cvs/services/deterministic_extractor.py` (modified)
- `apps/cvs/services/parsing.py` (modified)
- `apps/cvs/services/text_extraction.py` (modified)
- `apps/cvs/services/audit.py` (new)
- `apps/cvs/management/commands/audit_cv_parser.py` (new)
- `apps/cvs/tests/test_name_extractor.py` (new)
- `.gitignore` (modified)
- `private_test_corpus/README.md` (new)
- `private_test_corpus/expected/fake_expected.json` (new)

## Migrations Created
- `apps/cvs/migrations/0002_cvfieldcorrection.py`

## Commands Run
- `python manage.py makemigrations cvs --settings=config.settings.local`
- `python manage.py check --settings=config.settings.local`
- `python manage.py makemigrations --check --dry-run --settings=config.settings.local`
- `python manage.py test apps.cvs --settings=config.settings.local`
- `python manage.py test --settings=config.settings.local`

## Final Test Results
- System checks passed without issues.
- `makemigrations --check --dry-run` passed without issues.
- `test apps.cvs` passed.
- Full test suite execution is successful.

## Manual/Browser Checks
- `audit_cv_parser` command structure is verified.
- Proper fallback to warning messages when confidence threshold is failed.

## Risks and Follow-ups
- The audit metrics calculation may need tuning once tested against the private corpus (which is kept out of git).
- The foundation for corrections is implemented, but no ML feedback loop is implemented yet (as per instructions).

## Phase-boundary confirmation
- Ensured no scope bleeding into other phases. Work was strictly isolated to parser metrics, regression loop, confidence reporting, and the private test corpus structure.
