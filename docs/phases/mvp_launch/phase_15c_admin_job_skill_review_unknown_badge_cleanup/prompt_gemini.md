You are Gemini acting as implementation agent for TuniTech Abroad.

Current phase: Phase 15C — Admin Job Skill Review + Unknown Badge Cleanup.

Context:
Phase 15A fixed job skill materialization.
Phase 15B made high-value skill aliases permanent and reached ~91.57% active job skill coverage.
Now there are still some clearly IT jobs with no visible skills. Example: `Apprenti(e) Technicien Informatique (H/F)` has systems/network/security/cloud/support content but shows no skills and `Signal technique insuffisant`. Admin needs a practical review queue and manual skill assignment workflow. Public UI also shows an ugly `Unknown` badge that must be hidden.

Strict rules:
- Do not change matching score formula.
- Do not redesign UI.
- Do not call OpenRouter from views/admin/templates.
- Do not call France Travail from views/templates.
- Admin actions may call service layer or Celery tasks only.
- Do not bulk-create skills from unmatched candidates.
- Do not add all unmatched candidates as skills.
- Do not commit.
- Do not add React/Next/Vue/Angular/FastAPI/MongoDB/SQLAlchemy.
- Keep views thin and business logic in services.

Read first:
- `docs/phases/phase_15c_admin_job_skill_review_unknown_badge_cleanup/tasks.md`
- `problem_examples.md`
- `admin_review_policy.md`
- `apps/jobs/models.py`
- `apps/jobs/admin.py`
- `apps/jobs/services/presentation.py`
- `apps/jobs/services/skill_materialization.py`
- `apps/jobs/services/skill_extraction.py`
- `apps/skills/models.py`
- relevant job card/detail templates

Implement:
1. Admin list/filter for active jobs with no materialized `NormalizedJobSkill`.
2. Admin inline or dedicated admin editor for manual canonical `NormalizedJobSkill` assignment/removal.
3. Safe admin action to re-run deterministic skill extraction/materialization using services only.
4. Safe admin action to materialize from existing enrichment data if available, no provider call.
5. Export command/report for jobs needing skill review.
6. Public UI badge cleanup: hide `Unknown`/placeholder badges.
7. Tests for admin/query/actions, manual job skill assignment, export command, and Unknown badge filtering.

Example job expected from manual/admin review:
`Apprenti(e) Technicien Informatique (H/F)` may legitimately get skills such as:
- System Administration
- Network Administration / Network Security
- IT Support
- Hardware Maintenance
- Troubleshooting
- Cybersecurity
- Cloud
- Technical Documentation
only if supported by the stored job text.

Do not fake skills.

Run:
```bash
source .venv/bin/activate

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test --settings=config.settings.local --parallel 1
npm run css:build
python manage.py collectstatic --dry-run --noinput --settings=config.settings.local
git diff --check
```

Run safety greps from `tasks.md`.

Create:
`docs/phases/phase_15c_admin_job_skill_review_unknown_badge_cleanup/agent_report.md`

Report:
- files changed
- admin workflow added
- actions added
- export command output example
- Unknown badge fix
- tests/checks
- safety greps
- remaining risks
- commit recommendation

Do not commit.
