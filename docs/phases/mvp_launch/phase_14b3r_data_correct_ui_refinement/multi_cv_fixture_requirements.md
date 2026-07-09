# Multi-CV Fixture Requirements

The Aymen CV is necessary but not sufficient. This phase must prevent overfitting by testing at least five fixture shapes.

## Fixture strategy

Use raw text fixtures for deterministic extraction tests. PDF fixtures are optional except where a PDF already exists. Raw text tests are faster, more explicit, and prevent brittle PDF dependency.

Place fixtures under one of these paths:

```text
apps/cvs/tests/fixtures/
tests/fixtures/cvs/
```

Use names such as:

```text
cv_001_clean_english_full_stack.txt
cv_002_french_junior_stage.txt
cv_003_student_pfe_mixed_format.txt
cv_004_messy_links_multiline.txt
cv_005_incomplete_cv_missing_links.txt
```

## CV-001 — Clean English Full Stack CV

Must include:

- name
- `Tunis, Tunisia`
- phone
- email
- LinkedIn without https
- GitHub without https
- Portfolio domain without https
- technical skills
- experience dates
- languages
- target roles section

Expected:

- location extracted
- URLs normalized to https
- target roles extracted
- skills clean
- no skill becomes website

## CV-002 — French junior/stage CV

Must include French labels:

```text
Téléphone
Email
LinkedIn
GitHub
Portfolio
Compétences
Expérience
Formation
Langues
Objectif: Stage/PFE ou développeur junior en France
```

Expected:

- French labels recognized
- French/English language levels mapped to valid app values
- stage/internship target detected if supported
- no false URL extraction

## CV-003 — Student/PFE mixed format

Must include:

- bootcamp/university context
- PFE/stage target
- limited experience
- projects
- skills

Expected:

- current level student/junior if supported
- years experience 0 or 1
- target roles extracted
- project names not stored as skills unless clearly skill tokens

## CV-004 — Messy links multiline

Must include links split across lines:

```text
LinkedIn:
linkedin.com/in/example
GitHub:
github.com/example
Portfolio:
example.dev
```

Expected:

- links extracted and normalized
- no adjacent skill token captured as URL

## CV-005 — Incomplete CV

Missing links/languages/target roles.

Expected:

- extractor does not hallucinate missing fields
- warnings or missing field list is useful
- no fake URLs
- recommendations/profile UI shows missing fields clearly

## Hard negative assertions

No fixture may produce these as skills:

```text
PROJECTS
EDUCATION
PROFESSIONAL EXPERIENCE
CERTIFICATIONS
LANGUAGES
Tunis
Tunisia
France
Belgium
Luxembourg
Canada
Local Clients
DigitalBridge Labs
Private University of Tunis
March 2025
August 2025
salary range
and role
and error cases
```

No fixture may produce these as URLs:

```text
https://Next.js
https://React
https://Node.js
https://Django
https://PostgreSQL
```
