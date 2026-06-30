# Phase 15D — Curated Taxonomy + Zero-Skill Job Recovery

## Purpose

Phase 15A fixed job skill materialization.
Phase 15B made high-value aliases permanent.
Phase 15C added admin review and hid public `Unknown` badges.

Phase 15D now fixes the remaining data-quality problem:

1. Curated unmatched skill candidates should become aliases, canonical skills, ignore rules, or stay pending.
2. Active IT jobs with zero materialized skills should be automatically recovered when the job text contains clear technical evidence.
3. Non-IT false positives must not receive fake technical skills.
4. Admin should still see unresolved zero-skill jobs for review.

## Diagnostic basis

Current local diagnostic showed:

- 15 active jobs with zero `NormalizedJobSkill`.
- Several have long descriptions and clear IT text but still have `skill_extraction_status=not_enough_text`.
- Several have `enrichment_status=success` but zero `required_skills` and zero useful `optional_skills`.
- At least one job has `skill_extraction_status=success`, `enrichment_status=success`, but only `IT experience`, which is not materializable.
- Some rows are not real technical jobs and should stay zero-skill or be excluded.

## Strict scope

Allowed:
- skill seed aliases and canonical skills from curated decisions only
- ignore rules for obvious junk/unhelpful skill candidates
- reconciliation of already-resolved unmatched candidates
- deterministic fallback extraction for obvious job-text patterns
- zero-skill active job recovery command/service
- tests and reports

Forbidden:
- bulk-promoting all unmatched candidates
- fake skills just because a title says IT
- matching formula changes
- UI redesign
- OpenRouter calls from views/admin/templates
- France Travail calls from views/templates/admin
- live external API calls during user search
- React/Next/FastAPI/MongoDB/SQLAlchemy
