# Phase 15B — Unmatched Skill Candidate Policy

## Main answer

Do not add all unmatched skill candidates as skills.

`UnmatchedSkillCandidate` is a review queue, not an automatic skill creation queue. The correct handling is:

1. Promote to canonical `Skill`
   - Use when the term is a real reusable IT skill/technology/domain capability.
   - Examples: Active Directory, ISO 27001, SIEM, PowerShell, Azure Data Factory, COBOL.

2. Add as `SkillAlias`
   - Use when the term is a synonym, translation, spelling variant, or common phrasing for an existing canonical skill.
   - Examples:
     - `Cybersécurité` -> `Cybersecurity`
     - `API REST` -> `REST API`
     - `Réseaux` -> `Network Security` or a more precise network canonical skill if present
     - `VmWare` -> `VMware`
     - `Développement logiciel` -> `Software Development`

3. Keep pending
   - Use when the term may be useful but needs human review.
   - Examples: niche domain terms, ambiguous phrases, sector-specific acronyms.

4. Ignore
   - Use when the term is not a candidate skill for matching.
   - Examples:
     - job duties that are not skills
     - generic behavior/process phrases
     - business-only terms
     - education requirements
     - vague terms with no useful matching value

## Never do this

Never bulk-create every unmatched candidate as a `Skill`.

That would pollute matching and make recommendations less trustworthy.

## Quality criteria for promotion or aliasing

A candidate is safe to add if it satisfies most of these:
- It can appear on both a CV/profile and a job.
- It helps compare candidate capability to job requirement.
- It is not just a responsibility sentence.
- It is reusable across multiple jobs or a high-value single niche job.
- It maps clearly to one canonical concept.
- It does not overgeneralize a business task into a technical skill.

## Examples from current local findings

High-value aliases/canonical skills:
- Cybersécurité
- Windows
- Active Directory
- DevOps
- API REST
- Cloud
- OpenShift
- PowerShell
- Réseaux
- SIEM
- TCP/IP
- ISO 27001
- Azure Data Factory
- Prompt Engineering
- Data Modeling
- Microsoft 365
- VLAN
- Firewall

Review carefully / not always safe:
- Gestion de projets
- Pédagogie
- Business Developer
- Médiateur scientifique
- Transport / Manufacturing / Energy transformation consulting
- Safety Procedures
- Generic documentation phrases

Known acceptable unresolved remainder:
- Some active jobs should remain without skills because they have no usable candidates or are not strongly technical.
- Target is 90%+ coverage, not 100%.
