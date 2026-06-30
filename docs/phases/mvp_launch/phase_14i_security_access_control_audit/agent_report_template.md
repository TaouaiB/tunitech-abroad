# Phase 14I Agent Report Template

## 1. Summary

```text
Phase: 14I Security and Access Control Audit
Agent:
Date:
Branch:
Final verdict: FAIL / BLOCKED_HUMAN_SECURITY_SIGNOFF
```

Do not write PASS unless Baha has completed manual Chrome/admin security signoff and all automated checks passed.

## 2. Files changed

```text
List every changed file.
```

## 3. Audit documents produced

```text
docs/audits/security_access_matrix.md — created/updated: yes/no
docs/audits/security_findings_14i.md — created/updated: yes/no
```

## 4. Tests added or changed

```text
Test file:
Test class/function:
Security behavior covered:
```

## 5. Findings fixed

For each fixed finding:

```text
ID:
Severity: P0/P1/P2
Area:
Problem:
Fix:
Tests:
Files:
```

## 6. Findings accepted as safe

For each grep or audit finding not changed:

```text
Finding:
Why safe:
Evidence:
```

## 7. Remaining risks / follow-up

```text
Risk:
Why not fixed in 14I:
Recommended phase:
```

## 8. Commands run

Paste exact command and result summary:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
git diff --check
```

Include frontend/static/Celery commands if relevant.

## 9. Security grep results

Paste grep command summaries and explain every non-empty result.

## 10. Manual browser/admin checks still required

```text
Two-user browser IDOR smoke: pending/done
CV direct file URL check: pending/done
Admin non-staff/staff/superuser check: pending/done
OAuth/account pages sanity check: pending/done
HTMX mutation check: pending/done
```

## 11. Final verdict

Allowed values before Baha manual signoff:

```text
FINAL_VERDICT: FAIL
FINAL_VERDICT: BLOCKED_HUMAN_SECURITY_SIGNOFF
```

Use `FAIL` if any automated check fails or any P0/P1 security issue remains.
Use `BLOCKED_HUMAN_SECURITY_SIGNOFF` if automated work passes but manual Chrome/admin signoff is still required.
