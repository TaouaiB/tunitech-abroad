# Phase 14B Independent Verification Prompt

Use this after Gemini finishes Phase 14B.

```text
You are verifying Phase 14B — Professional UI/UX Redesign for TuniTech Abroad.

Do not implement new features unless a critical regression prevents verification.
Do not deploy.
Do not commit.
Do not print secrets.

Read:
- AGENTS.md
- docs/phases/phase_14b_professional_ui_ux_redesign/acceptance.md
- docs/phases/phase_14b_professional_ui_ux_redesign/agent_report.md
- git diff

Verify:
1. No forbidden frontend stack was added.
2. No architecture rule was broken.
3. Views remain thin.
4. /jobs/ still reads local PostgreSQL only.
5. Quick match remains anonymous and LLM-free.
6. CV private file URLs are not exposed.
7. Raw CV text is not exposed.
8. No secrets in diff/report.
9. Custom 404 under DEBUG=False does not expose URLconf.
10. Main pages look coherent and mobile-safe.
11. Full Django tests pass.

Run:
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test --settings=config.settings.local

Run grep checks from:
docs/phases/phase_14b_professional_ui_ux_redesign/regression_security_checks.md

Browser-check:
- /
- /jobs/
- one job detail
- quick match
- login
- dashboard
- profile
- CV
- recommendations
- match detail
- saved jobs
- account/delete
- privacy/terms
- DEBUG=False 404

Final verdict:
PASS / FAIL / BLOCKED

Report:
- issues found
- exact files involved
- whether Phase 14B can be committed
- what must be fixed before commit
```
