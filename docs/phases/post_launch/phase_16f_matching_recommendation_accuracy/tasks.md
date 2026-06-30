# Phase 16F — Matching and Recommendation Accuracy — tasks.md

## Goal

Make deterministic match scoring and recommendation explanations trustworthy after skills/job data are cleaner.

## Dependency contract

This phase consumes:

```text
canonical ProfileSkill.skill_id from 16D
NormalizedJobSkill.skill_id, requirement_type, confidence from 16E
```

Do not invent upstream fields that should have been implemented in 16D/16E.

## In-scope apps/areas

```text
matching services
recommendation services
match result snapshots
recommendation reason storage
```

## Tickets

### TTA-16F-001 — Exact skill scoring by canonical ID

Priority: P0  
Type: service/test

Acceptance:

```text
Scoring compares canonical skill IDs.
Required skills affect technical score more than optional skills.
Missing required skills create risk flags.
No string-only comparison is used for scoring.
Tests cover exact match, missing required, optional-only match.
```

### TTA-16F-002 — Low-confidence job skill behavior

Priority: P0  
Type: service/test

Acceptance:

```text
Low-confidence job skills from 16E do not over-inflate score.
Low-confidence source produces warning/profile signal where appropriate.
Score breakdown explains low-confidence job skill data.
Tests cover high-confidence vs low-confidence required skill.
```

### TTA-16F-003 — Related skill scoring guardrails

Priority: P1  
Type: service/model/test

Acceptance:

```text
Related-skill partial credit is implemented only if SkillRelation or equivalent already exists with clear tests.
Exact match gets full credit.
Related/parent ecosystem match gets partial credit only.
No over-crediting: .NET + C# is not the same as ASP.NET Core full match unless ASP.NET Core exists.
If relation model is not ready, defer related scoring explicitly.
```

### TTA-16F-004 — Match explanation cleanup

Priority: P0  
Type: service/frontend/test

Acceptance:

```text
Match result explains matched required skills, matched optional skills, missing required skills, missing optional skills.
Explains language risk, location/remote risk, profile weaknesses, recommended next action.
LLM is not required for deterministic explanation.
No LLM changes final score.
```

### TTA-16F-005 — Recommendation reason storage

Priority: P0  
Type: service/model/test

Acceptance:

```text
Stored recommendations include reason snapshots: strong skills, missing skills, risk flags, freshness, target fit.
Dashboard reads stored recommendations, not heavy recomputation.
Stale recommendations are marked/refreshed through existing services/tasks.
```

### TTA-16F-006 — Matching/recommendation feedback hooks

Priority: P1  
Type: model/service/admin/test

Acceptance:

```text
Owner/admin or user feedback can be captured for match usefulness where simple.
Feedback is label-ready for future ML but no ML is built.
No complex product survey or enterprise workflow is introduced.
```

## Out of scope

```text
No LLM scoring.
No CV parser work.
No skill alias seeding.
No UI redesign beyond explanation clarity needed for existing pages.
```
