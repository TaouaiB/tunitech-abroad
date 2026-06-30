# Gemini/Codex Disagreement and Tiebreak Policy

## Purpose

This policy prevents Codex from silently changing the intent of a phase ticket while “fixing” Gemini’s implementation.

## Roles

```text
Gemini = implementation agent.
Codex = verification and repair agent.
ChatGPT/Baha = final architecture/product decision gate.
```

## Rule

Codex may automatically fix defects when the fix preserves the ticket intent.

Allowed automatic fixes:

```text
move business logic from view to service
add missing tests
fix migration weakness
fix unsafe query/filter handling
fix public_id lookup mistake
fix secret/logging exposure
fix syntax/runtime/test failure
```

Codex must not silently change ticket intent.

Escalate in Codex report when:

```text
Codex believes the ticket as written violates architecture.
Codex believes the ticket would create security/privacy risk.
Codex believes the ticket conflicts with v1/v1.1 docs.
Codex replaces the requested implementation pattern with materially different behavior.
Codex defers or removes a ticket instead of implementing it.
Codex changes scoring/product logic beyond exact acceptance criteria.
Codex adds a schema/model not requested to satisfy its own design preference.
```

## Required Codex report section

```text
Intent-preserving fixes:
- ...

Intent-changing fixes or disagreements:
- none
```

If not none, stop after report. Do not proceed to production deployment until ChatGPT/Baha reviews.

## Final tiebreak

```text
Architecture/security/privacy rules beat implementation convenience.
v1 architecture boundaries beat v1.1 execution shortcuts.
v1.1 post-launch priorities beat old public copy/product wording.
Explicit phase acceptance beats agent preference.
When still ambiguous, stop and escalate.
```
