You are Codex acting as strict senior verifier for TuniTech Abroad.

Current phase: Phase 15C — Admin Job Skill Review + Unknown Badge Cleanup.

Your job:
- Verify Gemini implementation.
- Repair only in-scope issues.
- Do not commit.

Strict scope:
- Admin skill review workflow.
- Job skill review export/report.
- Unknown badge presentation cleanup.
- Tests.

Do not allow:
- matching formula change
- UI redesign
- OpenRouter calls from views/admin/templates
- France Travail calls from views/templates
- bulk promotion of unmatched candidates
- fake skills
- forbidden stack
- migrations unless strongly justified

Inspect:
- `apps/jobs/admin.py`
- `apps/jobs/models.py`
- `apps/jobs/services/presentation.py`
- `apps/jobs/services/skill_materialization.py`
- any new management command
- templates touched
- tests touched
- `agent_report.md`

Verify:
1. Admin can list active jobs with no materialized skills.
2. Admin can manually add/remove canonical `NormalizedJobSkill`.
3. Admin actions call services/tasks only.
4. Existing enrichment materialization action does not call provider.
5. Export command works and writes reviewable CSV/JSONL.
6. `Unknown` badge is hidden in public job card/detail.
7. Tests cover these cases.
8. No LLM/France Travail live calls are introduced in admin/views/templates.
9. No bulk unmatched candidate promotion.

Run:
```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
git diff --cached --check || true
```

Run safety greps from `tasks.md`.

Also run the export command added by Gemini with a small limit and verify output exists.

Create:
`docs/phases/phase_15c_admin_job_skill_review_unknown_badge_cleanup/codex_report.md`

Verdict:
PASS / REPAIRED_PASS / FAIL
