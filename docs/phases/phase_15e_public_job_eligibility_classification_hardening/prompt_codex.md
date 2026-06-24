You are Codex acting as strict senior verifier for TuniTech Abroad.

Current phase: Phase 15E — Public Job Eligibility + Classification Hardening.

Verify Gemini implementation and repair only in scope. Do not commit.

Reject:
- hiding all `excluded_non_it` blindly without reclassification protection
- public visibility logic scattered across templates/views without central service
- real IT jobs still excluded: Data Engineer GCP, Tech Lead/DevOps, Fullstack Java/Angular, .NET/C# Fullstack
- non-IT/commercial/outreach jobs still public/matchable
- OpenRouter/France Travail calls from views/admin/templates
- matching formula changes
- UI redesign
- DB migrations unless justified
- deleted jobs

Inspect:
- classification/signals services
- new eligibility service
- public job list/detail views
- recommendation and match views
- presentation/badge helpers
- management command `reclassify_jobs`
- tests
- phase report

Verify:
1. Classification positive IT overrides work.
2. Non-IT false positives are excluded.
3. Central eligibility service is used by public views/recommendations/match actions.
4. Public detail for excluded/admin-review-only returns 404 for normal users.
5. Match actions are blocked for non-matchable jobs.
6. Badge deduplication works.
7. `Compétences en cours d'analyse` only appears for truly pending analysis.
8. Reclassification command dry-run/apply/idempotency works.
9. Full tests pass.
10. Safety greps pass.

Run all commands from tasks.md.

Create:
`docs/phases/phase_15e_public_job_eligibility_classification_hardening/codex_report.md`

Verdict:
PASS / REPAIRED_PASS / FAIL
