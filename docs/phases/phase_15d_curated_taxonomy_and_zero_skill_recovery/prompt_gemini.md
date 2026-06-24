You are Gemini acting as implementation agent for TuniTech Abroad.

Current phase: Phase 15D — Curated Taxonomy + Zero-Skill Job Recovery.

Read first:
- `docs/phases/phase_15d_curated_taxonomy_and_zero_skill_recovery/README_PHASE_15D.md`
- `zero_skill_diagnostic.md`
- `deterministic_recovery_rules.md`
- `decision_policy.md`
- `tasks.md`
- curated CSV decision files in this phase folder
- Phase 15A/15B/15C reports if present

Goal:
1. Apply curated taxonomy decisions.
2. Add ignore rules and reconciliation for old pending unmatched candidates.
3. Add deterministic recovery for active IT jobs with zero materialized skills.
4. Prevent false positives/business/outreach jobs from receiving fake skills.

Strict rules:
- Do not bulk-promote all unmatched candidates.
- Do not fake skills from title alone.
- Do not change matching formula.
- Do not redesign UI.
- Do not call OpenRouter or France Travail from views/admin/templates.
- Do not add React/Next/FastAPI/MongoDB/SQLAlchemy.
- No migrations unless absolutely necessary and justified.
- Do not commit.

Implement:
- seed updates from approved decisions only
- ignore rule service/helper
- reconciliation command
- zero-skill recovery service
- zero-skill recovery command
- admin action calling service only
- tests listed in tasks.md

Diagnostic examples to cover:
- `Apprenti(e) Technicien Informatique` should recover support/network/security/cloud/documentation-related canonical skills when evidence exists.
- `Apprenti / Apprentie infrastructure et sécurité informatique` should recover network/security/infrastructure skills.
- `ALTERNANT EN INFORMATIQUE` should recover support/workstation/troubleshooting/access/network-related skills.
- `SDR/BDR - Business Developer - Cybersécurité`, `Médiateur scientifique`, and excluded transformation consulting must not receive fake technical skills.

Run all checks from tasks.md.

Create:
`docs/phases/phase_15d_curated_taxonomy_and_zero_skill_recovery/agent_report.md`

Report:
- files changed
- taxonomy decisions applied
- ignore rules
- reconciliation counts
- recovery before/after counts
- tests/checks
- safety greps
- remaining risks

Do not commit.
