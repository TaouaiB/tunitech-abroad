# Codex Verification Report — Phase 16C — CV Parser Quality Framework

## 1. Summary

```text
Status: PASS
Branch: dev
Commit/hash if available: not committed
```

Codex reviewed and repaired Gemini's Phase 16C work. The implementation now rejects confident garbage names such as `je me suis`, emits parser confidence/warning data, supports a private local audit corpus, provides a structured `audit_cv_parser` command, tracks parser metrics, and adds correction capture foundation.

## 2. Tickets completed

```text
- TTA-16C-001: PASS — CVNameExtractionService returns value/confidence/candidates/warnings and rejects first-person prose, section headers, job titles, contact data, dates, sentence-like text, and lowercase prose.
- TTA-16C-002: PASS — CVParsedData confidence_json and warnings_json are populated; low-confidence names do not overwrite profile names.
- TTA-16C-003: PASS — private_test_corpus/ is gitignored; corpus policy documents cvs/ expected/ reports/; fake expected JSON example is committed under docs only.
- TTA-16C-004: PASS — audit_cv_parser accepts --cv-dir, --expected-dir, --output, writes CSV/JSON reports, follows shared diagnostics shape, and exits non-zero on failed thresholds.
- TTA-16C-005: PASS — audit metrics include name_exact_accuracy, name_acceptable_accuracy, email_accuracy, phone_accuracy, skill_precision, skill_recall, false_skill_rate, low_confidence_count, and parse_failed_count.
- TTA-16C-006: PASS — CVFieldCorrection captures extracted/corrected values, confidence, field_name, source, and source_user; admin registration is read-only.
```

## 3. Files changed

```text
.gitignore
apps/cvs/admin.py
apps/cvs/management/commands/audit_cv_parser.py
apps/cvs/migrations/0002_cvfieldcorrection.py
apps/cvs/models.py
apps/cvs/services/audit.py
apps/cvs/services/deterministic_extractor.py
apps/cvs/services/name_extraction.py
apps/cvs/services/name_extractor.py
apps/cvs/services/parser_audit.py
apps/cvs/services/parsing.py
apps/cvs/services/text_extraction.py
apps/cvs/tests/test_models.py
apps/cvs/tests/test_name_extractor.py
apps/cvs/tests/test_parser_audit.py
docs/phases/post_launch/phase_16c_cv_parser_quality_framework/codex_review_report.md
docs/phases/post_launch/phase_16c_cv_parser_quality_framework/examples/fake_expected.json
```

Unrelated existing untracked file left untouched:

```text
docs/phases/post_launch/phase_16b_job_ingestion_freshness_search_country_neutral_ui/codex_phase16b_senior_repair_prompt.md
```

## 4. Migrations

```text
apps/cvs/migrations/0002_cvfieldcorrection.py
```

Migration is minimal and creates only the Phase 16C correction capture model with indexes.

## 5. Commands run

```bash
python manage.py check --settings=config.settings.local
# PASS: System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run --settings=config.settings.local
# PASS: No changes detected.

python manage.py test apps.cvs --settings=config.settings.local
# PASS: Ran 48 tests. OK.

python manage.py test --settings=config.settings.local
# PASS: Ran 583 tests. OK.

python manage.py audit_cv_parser --cv-dir /tmp/tunitech_phase16c_audit/private_test_corpus/cvs --expected-dir /tmp/tunitech_phase16c_audit/private_test_corpus/expected --output /tmp/tunitech_phase16c_audit/private_test_corpus/reports/latest.csv --threshold-name-acceptable 1.0 --threshold-skill-precision 1.0 --threshold-skill-recall 1.0 --settings=config.settings.local
# PASS: Synthetic one-case audit passed with 1.0 name/email/phone/skill metrics.
```

## 6. Tests

```text
passed
```

Coverage added/verified:

```text
- bad French first-person case `je me suis` returns no name and low confidence
- rejected candidates include reject_reason
- deterministic extractor exposes confidence and warning codes
- parser audit service writes structured CSV/JSON reports without raw CV text
- CVFieldCorrection stores source/source_user
- existing CV parser/service/model/view tests still pass
```

## 7. Manual/browser checks

```text
Browser checks: not applicable; Phase 16C is service/command/admin foundation work.
Manual command check: audit_cv_parser smoke-tested against synthetic local PDF and fake expected JSON.
```

## 8. Architecture compliance

```text
views thin: yes
services own logic: yes
Celery tasks thin: yes
public_id preserved: yes
CV privacy preserved: yes
no secrets logged: yes
no raw CV text logged in audit reports: yes
phase boundary respected: yes
no stack drift: yes
no fake enterprise RBAC: yes
```

## 9. Intent-Preserving Fixes

```text
- Replaced fragile top-line name extraction with a service that returns accepted/rejected candidates and warning codes.
- Added compatibility shims for prior module paths while adding contract-aligned files.
- Reworked audit service to compare all local expected JSON cases instead of hardcoding fake_expected.json.
- Added threshold-based audit pass/fail behavior and structured diagnostics output.
- Prevented audit command output from printing absolute private corpus paths.
- Added source choices/indexes to CVFieldCorrection.
- Added regression tests for the repaired behavior.
```

## 10. Intent-changing fixes or disagreements

```text
none
```

## 11. Risks / follow-ups

```text
- Audit thresholds may need tuning once Baha builds the real consented private corpus.
- The audit command currently audits local PDFs only; OCR remains explicitly out of scope.
- Correction capture foundation is admin/model-level only; no correction UI or ML feedback loop was built.
```

## 12. Ready for senior review

```text
yes
```
