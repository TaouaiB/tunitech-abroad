# Phase 14D: LLM Job Enrichment - Agent Report

## 1. Final Verdict
**Final verdict: BLOCKED_HUMAN_VISUAL_SIGNOFF**
The backend enrichment logic is implemented and passes all 293 tests. However, manual UI validation in Chrome is required by Baha.

## 2. Tickets Completed
- `[x]` TTA-14D-001 — Add `JobEnrichment` model to `apps.llm`
- `[x]` TTA-14D-002 — Add `JOB_ENRICHMENT_ENABLED` to settings
- `[x]` TTA-14D-003 — Add `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA` to settings
- `[x]` TTA-14D-004 — Implement prompt execution logic in `services/job_enrichment.py`
- `[x]` TTA-14D-005 — Implement JSON schema validation (soft skill filtering, evidence check)
- `[x]` TTA-14D-006 — Create Celery task `apps/llm/tasks.py`
- `[x]` TTA-14D-007 — Create management command `enrich_jobs`
- `[x]` TTA-14D-008 — Update match scoring to use enriched data conditionally
- `[x]` TTA-14D-009 — Polish UI copy (removed internal/technical labels)
- `[x]` TTA-14D-010 — Add comprehensive test coverage

## 3. Files Modified/Created
**Created:**
- `apps/llm/models.py` (added `JobEnrichment` model)
- `apps/llm/services/job_enrichment.py` (core service logic)
- `apps/llm/tasks.py` (background task)
- `apps/llm/management/commands/enrich_jobs.py` (management command)
- `apps/llm/tests/test_14d_enrichment.py` (test suite)

**Modified:**
- `config/settings/base.py` (added feature flags)
- `.env.example` (added feature flags)
- `apps/llm/admin.py` (registered `JobEnrichment` if needed)
- `apps/matching/services/scoring.py` (updated scoring logic to read from enrichment JSON)
- `templates/jobs/job_detail.html` (UI copy updates for Stack Technique section)
- `templates/matching/match_detail.html` (UI copy updates to remove internal technical phrases)
- `apps/matching/tests.py` (updated string assertions)

## 4. Risks & Technical Debt
- **Evidence Verification:** The evidence verification step currently performs a naive lowercase text search and a split-word fallback. If the LLM hallucinates evidence heavily modified or translated, it will fail validation.
- **Cost control:** A daily limit is implemented via `JOB_ENRICHMENT_DAILY_LIMIT` settings and enforced in `job_qualifies_for_enrichment`, but we don't currently track exact OpenRouter costs dynamically per token basis in our database—we only track `prompt_tokens` and `completion_tokens`.
- **Soft Skills List:** The list of soft skills to filter out is hardcoded (`"rigueur", "autonomie", "bon relationnel", "esprit d'équipe", "communication", "curiosité"`). If new soft skills are hallucinated, they might pass validation unless the list is expanded.

## 5. Next Steps for Baha
1. Open the project in Chrome.
2. Ensure the feature flag `JOB_ENRICHMENT_ENABLED=True` and `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA=True` in `.env`.
3. Run `python manage.py enrich_jobs --limit 5` (if using local fake data) to see it working against the actual OpenRouter API.
4. Verify the UI copy on `match_detail.html` and `job_detail.html` visually.
5. If everything looks good, provide manual sign-off!
