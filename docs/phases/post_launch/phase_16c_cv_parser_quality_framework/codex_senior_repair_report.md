# Codex Senior Repair Report — Phase 16C CV Parser Quality Framework

## Status

```text
PASS
Ready for senior review: yes
```

## Files Changed

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
docs/phases/post_launch/phase_16c_cv_parser_quality_framework/agent_report.md
docs/phases/post_launch/phase_16c_cv_parser_quality_framework/codex_review_report.md
docs/phases/post_launch/phase_16c_cv_parser_quality_framework/codex_senior_repair_report.md
docs/phases/post_launch/phase_16c_cv_parser_quality_framework/examples/fake_expected.json
docs/phases/post_launch/phase_16c_cv_parser_quality_framework/phase16c_senior_repair_prompt.md
```

Existing untracked artifact left untouched because it is outside the repair scope:

```text
phase16c_review_pack_20260630_153516.zip
```

## Migrations Changed/Created

```text
apps/cvs/migrations/0002_cvfieldcorrection.py
```

## Commands Run And Exact Results

```bash
python manage.py check --settings=config.settings.local
```

```text
System check identified no issues (0 silenced).
```

```bash
python manage.py makemigrations --check --dry-run --settings=config.settings.local
```

```text
No changes detected
```

```bash
python manage.py test apps.cvs --settings=config.settings.local
```

```text
Ran 49 tests in 4.228s
OK
Found 49 test(s).
System check identified no issues (0 silenced).
```

```bash
python manage.py test --settings=config.settings.local
```

```text
Ran 584 tests in 122.534s
OK
Found 584 test(s).
System check identified no issues (0 silenced).
```

```bash
python manage.py audit_cv_parser --cv-dir /tmp/tunitech_phase16c_senior_repair/private_test_corpus/cvs --expected-dir /tmp/tunitech_phase16c_senior_repair/private_test_corpus/expected --output /tmp/tunitech_phase16c_senior_repair/private_test_corpus/reports/latest.csv --threshold-name-acceptable 1.0 --threshold-skill-precision 1.0 --threshold-skill-recall 1.0 --settings=config.settings.local
```

```text
CV parser audit passed: {'cv_count': 1, 'passed_count': 1, 'failed_count': 0, 'low_confidence_count': 0, 'parse_failed_count': 0, 'name_exact_accuracy': 1.0, 'name_acceptable_accuracy': 1.0, 'email_accuracy': 1.0, 'phone_accuracy': 1.0, 'skill_precision': 1.0, 'skill_recall': 1.0, 'false_skill_rate': 0.0, 'low_confidence_rate': 0.0}
```

```bash
git diff --check
```

```text
PASS: no output.
```

## Final Check Results

```text
python manage.py check: PASS
python manage.py makemigrations --check --dry-run: PASS
python manage.py test apps.cvs: PASS, 49 tests
python manage.py test: PASS, 584 tests
git diff --check: PASS
```

## Audit Command Smoke Result

```text
PASS
```

The smoke test used a synthetic local PDF and fake expected JSON under `/tmp`. It did not use real CV files.

## Threshold-Failure Regression Result

```text
PASS
```

Added `CVParserAuditServiceTests.test_run_fails_when_thresholds_are_not_met`, which runs the audit service against a synthetic fake PDF/expected JSON pair with an intentionally impossible threshold and asserts:

```text
result["ok"] is False
result["reasons"]["threshold_failed:skill_recall"] == 1
```

## Private Corpus Hygiene Confirmation

```text
private_test_corpus/ is in .gitignore: yes
No private_test_corpus files are tracked by git: yes
Committed fake expected JSON stays under docs/phases/post_launch/phase_16c_cv_parser_quality_framework/examples/: yes
No real CVs committed: yes
No raw CV text printed in reports/logs from this repair pass: yes
```

## Intent-Preserving Fixes

```text
- Removed trailing whitespace in apps/cvs/services/parsing.py and apps/cvs/services/text_extraction.py.
- Added a focused threshold-failure regression for CVParserAuditService.
- Captured full project suite verification with final test count.
- Captured synthetic audit command smoke verification.
```

## Intent-Changing Fixes Or Disagreements

```text
none
```

## Remaining Risks

```text
- Real audit thresholds may need tuning once Baha creates a consented private corpus.
- The audit framework remains text-PDF only; OCR, ML/DL, correction UI, and LLM parser dependency are still out of scope.
```
