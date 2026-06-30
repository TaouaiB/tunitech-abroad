# Codex Verify Prompt — Phase 14B.5

You are the independent verifier. Do not implement broad changes. Verify the agent's Phase 14B.5 work.

Read:

```text
docs/phases/phase_14b5_auth_profile_ui_completion/acceptance.md
docs/phases/phase_14b5_auth_profile_ui_completion/regression_security_checks.md
docs/phases/phase_14b5_auth_profile_ui_completion/agent_report.md
```

Then run:

```bash
source .venv/bin/activate
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test apps.accounts apps.profiles apps.cvs apps.recommendations apps.dashboard --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Verify manually/with client:

- `/accounts/3rdparty/` is styled
- `/accounts/password/set/` is styled
- `/accounts/confirm-email/` is styled
- `/dashboard/account/connections/` works
- account settings shows Google/GitHub connection status
- set-password CTA exists for OAuth-created user
- no auth email says `example.test`
- target country is not rendered in templates
- profile and recommendation missing fields agree
- phone/location are not listed missing if DB has them
- no CV raw text or file URL rendered
- no OpenRouter/LLM in views/templates
- no France Travail live call from public search
- no forbidden frontend stack added

Final verifier verdict must be one of:

```text
FAIL
BLOCKED_HUMAN_VISUAL_SIGNOFF
```

Do not write PASS. Baha decides visual/product PASS in Chrome.
