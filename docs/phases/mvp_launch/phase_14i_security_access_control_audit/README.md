# Phase 14I — Security and Access Control Audit

## Goal

Prove that TuniTech Abroad protects user data before deployment.

This phase audits and fixes access control around:

- authentication gates
- object ownership
- CV privacy
- HTMX endpoint safety
- POST/CSRF mutation safety
- admin/staff boundaries
- public UUID routing
- secret leakage
- external-call isolation

## Why this phase exists

The MVP now contains accounts, OAuth, CV uploads, parsed CV data, profile data, recommendations, saved jobs, matches, LLM support, email preferences, privacy deletion, and admin operations. That creates IDOR, privacy, and route-permission risk. These risks must be tested before admin analytics, UI polish, or deployment.

## Non-negotiable rules

```text
Views stay thin.
Business logic stays in services.
Celery tasks call services only.
Models store data only.
No OpenRouter/LLM calls from views.
No France Travail live calls from public job search.
Public URLs use UUID public_id, never internal integer IDs.
CV files are private.
CVUpload.objects excludes soft-deleted CVs.
CVUpload.all_objects is reserved for admin/privacy/deletion/internal tasks.
No raw CV text in templates/admin list displays.
No secrets in logs/docs/prompts/reports/tests.
```

## Required repo outputs from this phase

```text
docs/audits/security_access_matrix.md
docs/audits/security_findings_14i.md
security/access-control tests covering private routes, IDOR attempts, CV privacy, admin boundaries, HTMX endpoints, POST mutation safety, public_id usage, and external-call isolation
```

## Stop condition

The phase is not accepted until automated checks pass and Baha performs manual Chrome/admin security signoff using `manual_browser_security_signoff.md`.
