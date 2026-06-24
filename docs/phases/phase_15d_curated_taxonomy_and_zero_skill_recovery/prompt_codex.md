You are Codex acting as strict senior verifier for TuniTech Abroad.

Current phase: Phase 15D — Curated Taxonomy + Zero-Skill Job Recovery.

Verify Gemini implementation. Repair only in scope. Do not commit.

Strictly reject:
- bulk promotion of unmatched candidates
- fake skills
- matching formula changes
- direct OpenRouter calls from views/admin/templates
- France Travail calls from views/templates/admin
- duplicate canonical skills
- duplicate normalized aliases
- broad dangerous ignore regex
- non-idempotent seed/recovery
- provider calls in recovery command/admin action

Inspect:
- `apps/skills/services/seed.py`
- `apps/skills/services/normalizer.py`
- any ignore/reconcile services
- any new management command
- `apps/jobs/services/zero_skill_recovery.py`
- `apps/jobs/admin.py`
- tests
- phase reports

Verify:
1. Only approved curated decisions are applied.
2. `keep_pending` rows are untouched.
3. ignore rules are narrow and tested.
4. already-resolved candidates are reconciled without duplicate aliases.
5. zero-skill recovery adds only evidence-supported canonical skills.
6. false-positive jobs do not receive technical skills.
7. dry-run commands do not write.
8. apply commands are idempotent.
9. admin action calls service only.
10. no migrations unless justified.
11. full tests pass.

Run all commands/checks from tasks.md.

Create:
`docs/phases/phase_15d_curated_taxonomy_and_zero_skill_recovery/codex_report.md`

Verdict:
PASS / REPAIRED_PASS / FAIL
