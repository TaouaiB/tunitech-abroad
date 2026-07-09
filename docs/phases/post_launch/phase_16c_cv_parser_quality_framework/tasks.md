# Phase 16C — CV Parser Quality Framework — tasks.md

## Goal

Make CV parser quality measurable and prevent embarrassing wrong confident extraction.

## In-scope apps/areas

```text
cvs parsing/name extraction/audit commands
profiles prefill protection
private test corpus docs
```

## Tickets

### TTA-16C-001 — CVNameExtractionService

Priority: P0  
Type: service/test

Acceptance:

```text
Service returns value, confidence, candidates, warnings.
Rejects "je me suis".
Rejects first-person phrases, sentences, section headers, job titles, emails, URLs, phones, dates, all-lowercase prose.
Uses explicit labels, top first-page lines, email local-part hint, and authenticated user name as candidate sources.
Low-confidence returns None.
Tests cover French and English bad cases.
```

### TTA-16C-002 — Parser confidence and warnings

Priority: P0  
Type: service/model/test

Acceptance:

```text
CVParsedData confidence_json and warnings_json are populated.
Low-confidence fields do not overwrite confirmed profile data.
Name/email/phone/links/skills get confidence or warnings where relevant.
No full CV text logged.
```

### TTA-16C-003 — Private CV audit corpus structure

Priority: P0  
Type: docs/command/test-policy

Acceptance:

```text
private_test_corpus/cvs/ documented.
private_test_corpus/expected/ documented.
private_test_corpus/reports/ documented.
private_test_corpus/ added to .gitignore.
Example expected JSON included with fake data only.
Policy states real CVs require consent and must not be committed/uploaded.
```

### TTA-16C-004 — audit_cv_parser command

Priority: P0  
Type: command/service/test

Acceptance:

```text
Command accepts --cv-dir, --expected-dir, --output.
Parses all corpus PDFs in isolated/audit mode.
Compares actual vs expected JSON.
Outputs CSV and JSON reports.
Returns non-zero if thresholds fail.
Uses shared diagnostics dict contract.
Does not log full CV text.
```

### TTA-16C-005 — Parser metrics and regression tests

Priority: P0  
Type: test/quality

Acceptance:

```text
Tracks name_exact_accuracy, name_acceptable_accuracy, email_accuracy, phone_accuracy, skill_precision, skill_recall, false_skill_rate, low_confidence_count, parse_failed_count.
Every fixed parser bug gets a regression test.
False positives are treated as more severe than missed optional fields.
```

### TTA-16C-006 — Correction capture foundation

Priority: P1  
Type: model/service/admin/test

Acceptance:

```text
CVFieldCorrection or equivalent captures extracted_value, corrected_value, confidence, field_name, source user/admin.
Correction data is admin-only personal data.
No export without anonymization.
Future ML label use is documented but no ML is built.
```

## Out of scope

```text
No OCR.
No ML/DL.
No full LLM parser dependency.
No production use of private test corpus.
No UI redesign.
```
