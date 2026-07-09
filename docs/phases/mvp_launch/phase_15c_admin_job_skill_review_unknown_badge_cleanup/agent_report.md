# Agent Report: Phase 15C — Admin Job Skill Review + Unknown Badge Cleanup

## Completed Objectives
- Created an admin workflow to identify and manually review active IT jobs that have zero materialized skills.
- Implemented `NormalizedJobSkillInline` for manual skill assignment directly in the admin panel.
- Added safe admin actions to:
  - Re-run deterministic skill extraction (`re_extract_skills_action`)
  - Rematerialize skills from existing LLM enrichment (`rematerialize_skills_action`) without making new API calls
- Built the `export_jobs_needing_skill_review` management command to generate CSV/JSONL reports of jobs lacking skills.
- Cleaned up the public UI by creating the `is_valid_badge` template filter, which robustly hides placeholder values (like "unknown", "n/a", etc.) from badges across job cards, job details, saved jobs, and recommendations.

## Files Modified / Created
- **Created:**
  - `apps/jobs/templatetags/job_presentation.py` (custom `is_valid_badge` template filter)
  - `apps/jobs/management/commands/export_jobs_needing_skill_review.py` (management command)
  - `apps/jobs/tests/test_15c_admin_skill_review.py` (tests for UI badges, admin actions, filters, and command)
  - `docs/phases/phase_15c_admin_job_skill_review_unknown_badge_cleanup/agent_report.md`
- **Modified:**
  - `apps/jobs/services/presentation.py` (added `is_valid_badge_value` static method)
  - `apps/jobs/admin.py` (added `NormalizedJobSkillInline`, `NoSkillsFilter`, and new actions)
  - `apps/jobs/services/admin_operations.py` (added `re_extract_skills` and `rematerialize_from_enrichment`)
  - `templates/jobs/job_detail.html` (UI badge cleanup)
  - `templates/jobs/partials/job_card.html` (UI badge cleanup)
  - `templates/dashboard/saved_jobs.html` (UI badge cleanup)
  - `templates/recommendations/partials/recommendation_card.html` (UI badge cleanup)

## Admin Workflow Added
- **Filter**: `Has Materialized Skills` (Yes / No) allows finding jobs with zero `job_skills`.
- **Inline**: `NormalizedJobSkillInline` allows manual entry with autocomplete for the `Skill` model.
- **Actions**: Admins can select multiple jobs and choose to either run deterministic extraction or rematerialize from the latest valid enrichment.

## Export Command Example Output
Running `python manage.py export_jobs_needing_skill_review --active-only` produces a CSV containing:
```
job_id,public_id,title,company,location,status,source,source_job_id,skill_signal_quality,skill_extraction_status,job_skill_count,description_excerpt
123,550e8400-e29b-41d4-a716-446655440000,Apprenti(e) Technicien Informatique,Company A,Paris,active,fixture,456,unknown,not_enough_text,0,Au sein de notre site...
```

## Tests and Checks
- Wrote tests for `is_valid_badge` verifying behavior with edge-case strings.
- Wrote tests for `NoSkillsFilter` verifying correct job matching.
- Wrote tests for `export_jobs_needing_skill_review` covering both CSV and JSONL outputs.
- All 5 tests passed locally.
- Checked `makemigrations --check` and `check --settings` (no issues).
- Checked `npm run css:build` and `collectstatic` (successful).

## Safety Greps Results
- No instances of `OpenRouterClient` or `client.chat` in views/templates.
- No instances of `FranceTravailClient` in views/templates.
- No direct file or raw text exposure in the UI (`cv.file.url`, `raw_response_json`).
- No hardcoded IDs or exposed secrets in git diff.

## Remaining Risks
- The `re_extract_skills` action runs synchronously in the admin panel. If an admin selects too many jobs simultaneously (> 100), the request could time out. In the future, this could be refactored into a Celery task.
- Currently, `rematerialize_skills_action` also runs synchronously.
- `is_valid_badge` relies on an explicitly defined set of strings. New placeholder variants might still pass through until added to `UNKNOWN_LANGUAGE_VALUES`.

## Commit Recommendation
Code looks good to review and commit. No direct OpenRouter or FranceTravail calls exist in views, and UI rendering logic is centralized in a proper template tag layer.

```bash
git add .
git commit -m "Complete Phase 15C admin job skill review and badge cleanup"
```
