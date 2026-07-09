# Shared Diagnostics Contract Policy

## Purpose

Phase 16B, 16C, 16D, 16E, and 16G all create diagnostics/audit services. They must use consistent output shapes so Phase 16G can render them in owner-admin dashboards without inventing a new adapter per phase.

## Required pattern

Each diagnostics/audit service should expose one primary method:

```python
Service.run(...) -> dict
# or
Service.audit(...) -> dict
```

The returned dict must follow this shape where relevant:

```python
{
    "ok": True,
    "service": "job_ingestion_diagnostics",
    "generated_at": "ISO-8601 timestamp",
    "scope": {...},
    "counts": {...},
    "statuses": {...},
    "reasons": {...},
    "top_items": [...],
    "warnings": [...],
    "errors": [...],
    "recommended_actions": [...],
    "artifacts": {...},
}
```

## Rules

```text
Use stable keys.
Use counts and reason buckets, not prose-only output.
Never include secrets.
Never include full CV text.
Never include raw private file paths.
Never make diagnostics failure break user-facing flows.
Management commands may exit non-zero only when explicitly designed as audit gates.
```

## Phase-specific examples

```text
16B JobIngestionDiagnosticsService: fetched -> raw -> normalized -> active -> public_visible -> matchable.
16C CVParserAuditService: expected vs actual, metrics, failure buckets, report paths.
16D SkillAliasAuditService: duplicate aliases, ambiguous aliases, unmatched candidates, missing aliases.
16E JobQualityAuditService: zero-skill jobs, weak-skill jobs, non-IT candidates, eligibility failures.
16G Admin dashboards: consume all diagnostics outputs without rewriting their logic.
```
