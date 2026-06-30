# Phase 15C Problem Examples

## Problem 1 — Clearly IT job has no skills

Example:
`Apprenti(e) Technicien Informatique (H/F)`

Description contains:
- administration systèmes et réseaux
- gestion et maintenance des systèmes informatiques
- réseaux
- disponibilité matérielle informatique
- installer et configurer les équipements informatiques
- sécurité informatique
- cybersécurité
- cloud
- support technique utilisateurs
- diagnostiquer et résoudre les incidents
- documentation technique

Expected materialized skills should include some of:
- System Administration
- Network Administration / Network Security
- IT Support
- Hardware Maintenance
- Troubleshooting
- Cybersecurity
- Cloud
- Technical Documentation
- Operating System Installation / Software Installation, if evidence exists

The exact skills must come from canonical `Skill` records and `SkillAlias` mappings, not raw text.

## Problem 2 — Public UI shows `Unknown`

Public job cards/details must not display placeholder-like badges:
- Unknown
- unknown
- UNKNOWN
- None
- null
- N/A
- Non précisé, if used as placeholder badge
- empty strings

For example, a job header should show:
`CDD · Internship · Publiée le 18 Jun 2026`

not:
`CDD · Unknown · Internship · Publiée le 18 Jun 2026`

If experience level / remote status / contract detail is unknown, hide it.

## Problem 3 — Admin lacks review workflow

Admin needs a fast way to review jobs where:
- active job has zero `NormalizedJobSkill`
- signal is `strong` or `partial`
- extraction status is `not_enough_text`, `success`, `pending`, or suspicious
- enrichment succeeded but produced no materialized skills
- active jobs are visible to users but poor for matching

Admin must not edit raw provider payloads.
Admin must edit canonical job skills only.
