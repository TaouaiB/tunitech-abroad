# Phase 16E — Job Skill Extraction and Data Quality — tasks.md

## Goal

Improve job skill extraction and public job data quality before matching/recommendation scoring is hardened.

## Contract with Phase 16F

This phase must produce per-job-skill confidence data that Phase 16F can consume. Phase 16F should not invent confidence fields.

## In-scope apps/areas

```text
jobs skill extraction
NormalizedJobSkill
search vector rebuild
public eligibility diagnostics
management commands
```

## Tickets

### TTA-16E-001 — Required/optional/detected classifier

Priority: P0  
Type: service/test

Acceptance:

```text
JobSkillExtractionService separates required, optional, detected where possible.
When classification is weak, use detected/unknown with lower confidence instead of pretending required.
Per-skill confidence is written to NormalizedJobSkill.confidence or existing equivalent field.
Source of detection is recorded: rule/llm/admin/source_api where available.
Tests cover clear required, clear optional, ambiguous detected.
```

### TTA-16E-002 — Zero-skill and weak-skill job detection

Priority: P0  
Type: service/command/admin/test

Acceptance:

```text
Jobs with zero skills detectable.
Jobs with only generic skills detectable.
Jobs with low-confidence-only skills detectable.
Diagnostics expose reason buckets.
No jobs are deleted; status/eligibility/review flags are used.
```

### TTA-16E-003 — rematerialize_job_skills command

Priority: P0  
Type: command/service/task/test

Acceptance:

```text
Command can rebuild NormalizedJobSkill rows safely.
Supports dry-run.
Supports limit/batch options.
Idempotent reruns do not duplicate rows.
Does not call external API.
```

### TTA-16E-004 — rebuild_job_search_vectors command

Priority: P0  
Type: command/service/test

Acceptance:

```text
Search vectors rebuild from title, required skills, optional skills, company, location, description.
Command supports dry-run/limit/batch.
Rerun is safe.
Search by canonical skill/alias improves after rebuild.
```

### TTA-16E-005 — inspect_public_job_eligibility command

Priority: P0  
Type: command/service/admin/test

Acceptance:

```text
Command reports normalized_total, active_total, public_visible_total, public_matchable_total, excluded_total.
Reports exclusion reasons.
Reports zero_skill_jobs, weak_skill_jobs, non_it_candidates if available.
Uses shared diagnostics dict contract.
```

### TTA-16E-006 — Job quality feedback foundation

Priority: P1  
Type: model/service/admin/test

Acceptance:

```text
Owner/admin can mark job quality issue: not_it, wrong_skills, wrong_level, expired, duplicate, source_noise.
Feedback is stored for future diagnostics and future ML labels.
No recruiter/team workflow is added.
```

## Out of scope

```text
No final match score changes.
No recommendation ranking changes.
No live external API during search.
No ML/DL.
```
