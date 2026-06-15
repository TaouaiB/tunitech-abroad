# Phase 2 Prompt — Core Database Models and Admin

You are working in the TuniTech Abroad repository.

## Read first

Read these files before coding:

```text
AGENTS.md
docs/planning/04_Database_Schema_v1.md
docs/planning/05_Service_Contracts_v1.md
docs/planning/08_Implementation_Roadmap_v1.md
docs/planning/09_MVP_Backlog_v1.md
docs/phases/phase_02_core_models_admin/tasks.md
docs/phases/phase_02_core_models_admin/acceptance.md
docs/phases/phase_02_core_models_admin/agent_report_template.md
```

## Current phase

Implement **Phase 2 only**:

```text
Phase 2 — Core Database Models and Admin
```

You may complete all tickets inside this phase automatically.

Do not ask me for approval between small tickets.

## Hard boundary

Do **not** implement Phase 3 or later.

Do **not** create:

```text
skills.Skill
skills.SkillAlias
skills.UnmatchedSkillCandidate
jobs.JobSource
jobs.RawJobRecord
jobs.NormalizedJob
cvs.CVUpload
cvs.CVParsedData
matching.MatchResult
recommendations.JobRecommendation
llm.PromptVersion
notifications.EmailBatch
notifications.EmailEvent
notifications.EmailUnsubscribeToken
privacy.DeletionRequest
```

Do not implement:

```text
CV upload
CV parsing
job ingestion
job search
matching score
recommendations
OpenRouter
LLM calls
weekly digest
real email sending
account deletion
frontend redesign
```

## Environment rule

Use the terminal environment.

If the IDE shows a Python interpreter warning, do **not** block on it.

Use:

```bash
source .venv/bin/activate
```

Run commands from terminal.

## Fedora/Linux command style

Use bash commands.

Do not use PowerShell.

## Dependency rule

Do not add new external packages unless strictly required.

If a package is needed, add it to the correct requirements file and explain why in the report.

For local development use:

```bash
pip install -r requirements/local.txt
```

## Required implementation

Implement these tickets:

```text
TTA-0201 — CandidateProfile model
TTA-0202 — ProfileSkill shell model
TTA-0203 — EmailPreference model
TTA-0204 — ConsentRecord and ConsentService
TTA-0205 — UserEvent and UserEventService
TTA-0206 — SystemSetting model and optional service
TTA-0207 — Update AccountProvisioningService
TTA-0208 — Admin registration
TTA-0209 — Migrations and tests
```

Follow `tasks.md` and `acceptance.md`.

## Architecture rules

Respect the project architecture:

```text
Views stay thin.
Business logic goes in services.
Celery tasks call services only.
Models store data.
Services own business logic.
```

For this phase, services should be simple and idempotent.

## Account provisioning rule

Update:

```text
apps/accounts/services/account_provisioning.py
```

It must create:

```text
CandidateProfile
EmailPreference
```

Use `get_or_create`.

Calling the service multiple times must not create duplicates.

## Admin rule

Register all Phase 2 models in Django Admin:

```text
CandidateProfile
ProfileSkill
EmailPreference
ConsentRecord
UserEvent
SystemSetting
```

Use simple admin configuration.

No custom admin dashboard.

## Tests

Create or update tests for Phase 2.

Use standard Django TestCase and Client where needed.

Do not use invalid monkeypatches.

Do not use RequestFactory just to bypass test client issues.

Do not skip tests.

Tests should verify:

```text
CandidateProfile creation
ProfileSkill uniqueness
EmailPreference creation
ConsentService.record_consent
UserEventService.record_event
SystemSetting creation/value lookup
AccountProvisioningService idempotency
No Phase 3+ models created
```

## Browser/manual testing

After terminal checks pass, run the Django dev server if possible:

```bash
python manage.py runserver 127.0.0.1:8000 --settings=config.settings.local
```

Then use Antigravity browser testing if available.

Test these pages in browser/manual mode:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/accounts/login/
http://127.0.0.1:8000/accounts/signup/
http://127.0.0.1:8000/dashboard/
http://127.0.0.1:8000/admin/
```

Expected browser behavior:

```text
Homepage loads.
Login page loads.
Signup page loads.
Dashboard redirects anonymous user to login.
Admin login page loads.
If a superuser/browser session is available, verify Phase 2 models appear in admin.
```

If browser testing cannot be performed, state clearly why in `agent_report.md`.

## Required final terminal checks

Run all:

```bash
python --version
python -m django --version
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py test --settings=config.settings.local
git status --short
git diff --stat
```

## Final report

Create:

```text
docs/phases/phase_02_core_models_admin/agent_report.md
```

Use:

```text
docs/phases/phase_02_core_models_admin/agent_report_template.md
```

The report must include:

```text
completed tickets
files created/changed
migrations created
tests added
commands run
final check results
browser/manual testing result
phase boundary confirmation
security/secrets confirmation
git status
remaining risks/manual steps
```

## Git rule

Do not commit.

Do not merge.

Do not push.

The user will review and commit manually.

## Goal

Complete Phase 2 cleanly, with terminal checks passing, browser/manual checks attempted where useful, and no Phase 3+ work.
