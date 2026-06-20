# Phase 15C — Admin Job Skill Review + Unknown Badge Cleanup

## Purpose

Phase 15A fixed materialization.
Phase 15B made high-value taxonomy aliases permanent.
Phase 15C addresses the remaining product/admin quality problem:

- Some clearly IT jobs still show no extracted skills.
- Admin needs a practical review queue for jobs with no `NormalizedJobSkill`.
- Admin must be able to add/remove job skills manually.
- Public UI must not display ugly placeholder badges like `Unknown`.

This is a backend/admin/data-quality phase with one small UI presentation bugfix.

## Example real problem

A job like `Apprenti(e) Technicien Informatique (H/F)` has a clear IT description:
- administration systèmes et réseaux
- infrastructure
- security/cybersecurity
- cloud / modernisation IT
- technical support
- incident diagnosis
- documentation technique

It should not show:
- `Aucune compétence spécifique extraite`
- `Signal technique insuffisant`
- badge `Unknown`

## Target outcome

Admin can find and fix jobs like this without asking an agent:
- list jobs with no skills
- inspect description and enrichment/extraction status
- re-run extraction/materialization
- add canonical job skills manually
- remove wrong job skills
- mark no-skill/non-IT jobs as reviewed/ignored if supported without overbuilding

Public UI:
- hides `Unknown` / empty placeholder badges
- keeps useful badges only
