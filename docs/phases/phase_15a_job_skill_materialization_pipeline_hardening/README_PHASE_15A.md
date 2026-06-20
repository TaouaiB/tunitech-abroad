# Phase 15A — Job Skill Materialization Pipeline Hardening

Purpose: fix the backend/data pipeline gap where jobs can be normalized and LLM-enriched but still do not get canonical `NormalizedJobSkill` rows.

This phase is not UI polish and not deployment. It is a data pipeline hardening phase before deployment.

Current verified symptoms from local diagnostics:
- Many `NormalizedJob` rows exist.
- Many `JobEnrichment` rows are `success`.
- Most active jobs still have `skill_extraction_status=pending`.
- Most active jobs do not have `NormalizedJobSkill` rows.
- Several active jobs have successful enrichment JSON with common skills like Python, SQL, Docker, Kubernetes, Java, Git, PostgreSQL, but no materialized `job_skills`.

Architectural target:
`RawJobRecord -> NormalizedJob -> JobSkillExtractionService / JobEnrichment -> Skill/SkillAlias normalization -> NormalizedJobSkill -> matching/recommendations/UI`.

Agent rule:
Gemini implements. Codex verifies and repairs only in scope. Neither commits.
