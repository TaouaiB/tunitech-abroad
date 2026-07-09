# INSTALL — v1.1 Phase Execution Pack v3

This version is path-correct for the repo structure that separates old MVP phases from post-launch phases.

## Target path

Put this pack here:

```text
docs/phases/post_launch/
```

Keep previous phases here:

```text
docs/phases/mvp_launch/
```

Keep v1.1 planning addenda here:

```text
docs/planning/post_launch/
```

## Manual placement

Copy these directly into `docs/phases/post_launch/`:

```text
README_PHASE_EXECUTION_PACK.md
INSTALL.md
GLOBAL_AGENT_RULES_v1_1.md
CHANGELOG_v2_SONNET_REVIEW_FIXES.md
CHANGELOG_v3_PATH_UPDATE.md
MANUAL_PLACEMENT.md
shared/
phase_16a_production_stabilization/
phase_16b_job_ingestion_freshness_search_country_neutral_ui/
phase_16c_cv_parser_quality_framework/
phase_16d_skill_taxonomy_alias_accuracy/
phase_16e_job_skill_extraction_data_quality/
phase_16f_matching_recommendation_accuracy/
phase_16g_admin_monitoring_alerts/
phase_16h_ui_ux_redesign_decision_system/
phase_16i_email_professionalization/
phase_16j_future_ml_llm_platform/
```

## Verification by eye

Check these files exist:

```text
docs/phases/post_launch/shared/gemini_codex_tiebreak_policy.md
docs/phases/post_launch/shared/diagnostics_contract_policy.md
docs/phases/post_launch/phase_16d_skill_taxonomy_alias_accuracy/canonical_skill_seed_table_v1.md
docs/phases/post_launch/phase_16a_production_stabilization/gemini_prompt.md
docs/phases/post_launch/phase_16a_production_stabilization/codex_review_prompt.md
```

## Use rule

Use only one phase at a time. Start with Phase 16A.
