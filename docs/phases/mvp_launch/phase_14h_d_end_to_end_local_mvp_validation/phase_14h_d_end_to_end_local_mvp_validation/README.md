# Phase 14H-D — End-to-End Local MVP Validation

This phase validates the full local MVP after the audit-hardening, Celery Beat, and Tailwind production build phases.

It is a **validation and small bug-fix phase**, not a feature phase.

Goal:

Tunisian IT profile → France IT jobs/internships → CV upload/parsing → job matching → missing skills → recommendations → saved jobs/privacy flows.

## Main rule

Do not add new features. Validate the existing product and fix only blocking bugs found during the validation.

## Required output

Create/update:

```text
docs/validation/local_mvp_e2e_report.md
```

The report must clearly say what passed, what failed, what was fixed, and what remains blocked for human visual signoff.

## Final verdict

Use only:

```text
FINAL_VERDICT: FAIL
```

or

```text
FINAL_VERDICT: BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Do not use PASS because manual browser confirmation is required.
