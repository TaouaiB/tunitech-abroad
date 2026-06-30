# Phase 15C Admin Job Skill Review Policy

## Do not fake skills

Manual admin review must add only canonical skills supported by job text.

Bad:
- adding `Python` just because the role is IT
- adding broad `IT` as a skill
- adding skills from imagination
- adding all skills from unmatched candidates blindly

Good:
- job says support users, incidents, equipment installation -> `IT Support`, `Troubleshooting`, `Hardware Maintenance`, `Operating System Installation`
- job says sécurité informatique / cybersécurité -> `Cybersecurity`
- job says systèmes et réseaux -> `System Administration`, `Network Administration` or chosen canonical network/system skills
- job says cloud -> `Cloud`
- job says documentation technique -> `Technical Documentation`

## Admin workflow

For each job with no skills:

1. Check title, description, and source text.
2. Check `skill_signal_quality`.
3. Check `skill_extraction_status`.
4. Check enrichment status and validated output if available.
5. Re-run deterministic extraction/materialization if appropriate.
6. Add missing canonical `NormalizedJobSkill` rows manually if evidence is present.
7. Remove incorrect rows if needed.
8. If the job is not a real IT skill match, leave it without skills or mark reviewed using existing safe fields/admin notes if available.

## Requirement type guidance

Use:
- `required` for explicitly required or core mission skills.
- `optional` for plus/nice-to-have skills.
- `inferred` only if the existing model supports it and the evidence is clear.

## Source guidance

Use:
- `admin` for manually added job skills.
- `rule` for deterministic extraction.
- `llm` for materialized LLM enrichment.

Never mark manual additions as `llm`.

## Unknown badge policy

Presentation layer must filter placeholder values before display.
Do not mutate source data just to hide `Unknown`.
