You are Gemini acting as implementation agent for TuniTech Abroad.

Current phase: Phase 15E — Public Job Eligibility + Classification Hardening.

Read first:
- `docs/phases/phase_15e_public_job_eligibility_classification_hardening/README_PHASE_15E.md`
- `diagnostic_summary.md`
- `eligibility_policy.md`
- `classification_rules.md`
- `tasks.md`
- Phase 15D reports if present

Context:
We found 10 active `excluded_non_it` jobs. Some are truly non-IT, but several are real IT jobs incorrectly excluded: Data Engineer GCP, Tech Lead / DevOps, Fullstack Java/Angular, .NET/C# Fullstack, Data Engineer / Expert Data Integration. The classifier is over-triggering generic negative terms. Public views also show non-IT jobs and weak wording like `Compétences en cours d'analyse`.

Goal:
1. Harden classification so real IT jobs are not excluded.
2. Add central public eligibility/matchability service.
3. Hide non-IT/admin-review-only jobs from public surfaces.
4. Block match actions for non-matchable jobs.
5. Deduplicate public badges.
6. Use `Compétences en cours d'analyse` only for true pending analysis.

Strict rules:
- No matching formula change.
- No UI redesign.
- No OpenRouter/LLM calls from views/admin/templates.
- No France Travail calls from views/templates/admin.
- User search reads PostgreSQL only.
- No forbidden stack.
- No migrations unless absolutely necessary and justified.
- Do not delete jobs.
- Do not commit.

Implement tasks.md exactly.

Create:
`docs/phases/phase_15e_public_job_eligibility_classification_hardening/agent_report.md`

Run all tests/checks/safety greps from tasks.md.

Report:
- files changed
- classification fixes
- eligibility service
- public surface changes
- reclassification before/after
- badge/wording fixes
- tests/checks
- risks

Do not commit.
