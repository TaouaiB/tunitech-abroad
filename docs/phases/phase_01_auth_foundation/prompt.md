# Phase 1 — Agent Prompt

Place this file at:

```text
docs/phases/phase_01_auth_foundation/prompt.md
```

Paste the prompt below into Antigravity/Gemini in goal mode.

```text
Read AGENTS.md first.

Then read these Phase 1 files:

- docs/phases/phase_01_auth_foundation/tasks.md
- docs/phases/phase_01_auth_foundation/acceptance.md
- docs/phases/phase_01_auth_foundation/agent_report_template.md

Also consult the planning documents in docs/planning/ when needed, especially:

- Implementation_Roadmap_v1
- MVP_Backlog_v1
- Working_Agreement_v1
- Database_Schema_v1
- Service_Contracts_v1
- Page_URL_View_Map_v1

Implement Phase 1 only: Django foundation and authentication.

You may work automatically through all Phase 1 tickets:

- TTA-0101 — Create custom User model
- TTA-0102 — Install and configure django-allauth
- TTA-0103 — Implement AccountProvisioningService shell
- TTA-0104 — Create base templates and homepage shell
- TTA-0105 — Create dashboard access guard

Critical Phase 1 rule:
Create the custom User model and set AUTH_USER_MODEL before normal auth/admin migrations are applied.
The final database must use accounts.User and must not create auth_user.

Phase boundary:
Do not implement Phase 2.
Do not create CandidateProfile, ProfileSkill, EmailPreference, ConsentRecord, UserEvent database model, or SystemSetting.
The roadmap mentions provisioning CandidateProfile and EmailPreference after signup, but those models belong to Phase 2. For Phase 1, implement and wire AccountProvisioningService as an idempotent shell/hook only. Add comments/tests showing real profile/preference creation is deferred to Phase 2.

Implementation requirements:

1. Custom User/auth foundation
- Create apps/accounts.
- Implement accounts.User.
- Email must be unique.
- Configure AUTH_USER_MODEL = "accounts.User".
- Enable Django auth/admin safely.
- Register custom User in admin.
- Add tests for user creation and duplicate email rejection.

2. django-allauth
- Add django-allauth to runtime requirements.
- Install using the project .venv only.
- Do not install globally.
- Do not use pip --user.
- Configure email/password signup/login.
- Configure email verification for local console email backend.
- Configure Google and GitHub provider placeholders using environment variables only.
- Use allauth setting names compatible with the installed allauth version. If warnings appear because a setting is deprecated, fix the setting properly; do not suppress the warning.
- Include allauth URLs under /accounts/.
- Add minimal templates for login/signup/logout/email verification where needed.

3. AccountProvisioningService
- Create apps/accounts/services/account_provisioning.py.
- Implement AccountProvisioningService.provision_new_user(user, provider=None).
- It must be safe to call more than once.
- Wire it to signup/login via an allauth adapter or signal.
- Do not import or create Phase 2 models.

4. Homepage/base templates
- Create a minimal homepage at /.
- Create templates/base.html.
- Create templates/core/home.html.
- Add simple navigation for login/signup/dashboard/logout states.
- Use Django templates. No React. No SPA.
- Keep UI minimal. Do not polish heavily.

5. Dashboard access guard
- Create /dashboard/ placeholder.
- Require authentication.
- Anonymous users redirect to login.
- Authenticated users receive 200.
- Do not implement real dashboard widgets yet.

6. Tests/checks
After each logical block, run relevant checks.
At minimum, run at the end:

source .venv/bin/activate
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py check --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py test --settings=config.settings.local

Also verify:

source .venv/bin/activate
python manage.py shell --settings=config.settings.local -c "from django.db import connection; c=connection.cursor(); c.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;\"); print([r[0] for r in c.fetchall()])"

Expected:
- accounts_user exists
- auth_user does not exist

Security rules:
- Create or update .env.example with variable names only if needed.
- Never commit .env.
- Never print .env.
- Never print OAuth secrets.
- Never hardcode secrets.
- Use environment variables only.

Git behavior:
- Do not commit.
- Do not merge.
- Do not push.

Hard boundary:
- Do not implement Phase 2.
- Do not add jobs, skills, CV, matching, recommendations, LLM, weekly email digest, privacy deletion, or public job search.
- Do not add React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.

At the end, produce the final report using:

docs/phases/phase_01_auth_foundation/agent_report_template.md
```
