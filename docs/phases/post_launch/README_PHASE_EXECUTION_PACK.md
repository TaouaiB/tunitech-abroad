# TuniAtlas v1.1 Phase Execution Pack

This pack contains execution-ready phase plans for Gemini implementation and Codex verification/review.

## How to use

1. Keep original v1 planning PDFs in `docs/planning/`.
2. Keep v1.1 planning addenda in `docs/planning/post_launch/`.
3. Put this pack under `docs/phases/post_launch/`. Previous phases 0-15 stay under `docs/phases/mvp_launch/`.
4. For each phase, give Gemini the `gemini_prompt.md` for that phase.
5. After Gemini finishes and reports, give Codex the `codex_review_prompt.md` for the same phase.
6. Codex verifies/fixes only inside the same phase. It must not start the next phase.
7. Send ChatGPT the Gemini report, Codex report, changed-file list, diffs, and test output for senior review.

## Phase order

```text
16A — Production Stabilization
16B — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening
16C — CV Parser Quality Framework
16D — Skill Taxonomy and Alias Accuracy
16E — Job Skill Extraction and Data Quality
16F — Matching and Recommendation Accuracy
16G — Admin Monitoring and Alerts
16H — Full UI/UX Redesign and Decision System
16I — Email Professionalization
16J — Future ML/LLM Platform
```

Phase 16H is intentionally not detailed. It is a full UI/UX demolition/rebuild phase that must be planned separately after backend intelligence is stable.

## v2 senior-review fixes included

This execution pack has been tightened after external senior review.

Added:

```text
shared/gemini_codex_tiebreak_policy.md
shared/diagnostics_contract_policy.md
phase_16d_skill_taxonomy_alias_accuracy/canonical_skill_seed_table_v1.md
```

Updated:

```text
Per-ticket tasks.md acceptance criteria are now explicit instead of boilerplate.
16A security/correctness tickets are ordered before product-quality fixes.
16B rollback plan includes active/public job count regression guard.
16C CV corpus policy includes consent/sourcing rules.
16D taxonomy must use seed artifact instead of agent-invented aliases.
16E explicitly produces per-skill confidence for 16F.
16F explicitly consumes 16D/16E contracts.
Codex must flag intent-changing fixes instead of silently changing ticket behavior.
Diagnostics services must return consistent structured dicts for 16G dashboards.
```


## Path layout

```text
docs/phases/
  mvp_launch/        # completed old phases 0-15
  post_launch/       # this v1.1 phase execution pack, phases 16A-16J
```

All prompt references in this v3 pack use `docs/phases/post_launch/...`.
