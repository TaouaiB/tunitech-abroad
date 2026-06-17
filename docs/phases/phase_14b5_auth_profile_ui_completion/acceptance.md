# Acceptance Criteria

## Automated acceptance

All must pass:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test apps.accounts apps.profiles apps.cvs apps.recommendations apps.dashboard --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

If an avatar migration is intentionally added, `makemigrations --check --dry-run` must pass after the migration file is created.

## Auth/UI acceptance

- `/accounts/3rdparty/` is styled.
- `/accounts/password/set/` is styled.
- `/accounts/confirm-email/` is styled.
- Password reset/change pages are styled.
- Email management page is styled.
- Social signup/error/connection pages are styled where present.
- No visible allauth page looks default/unbranded.
- Account settings contains Google/GitHub connection status.
- OAuth-created user has a set-password CTA.

## Email acceptance

- No email body or subject contains `example.test`.
- Verification email contains a confirmation link.
- Duplicate-account email explains duplicate account and does not pretend to be a verification link.
- Product name is `TuniTech Abroad`.

## Profile/recommendation acceptance

- `target_country` is not visible on profile/CV/recommendation pages.
- Profile page and recommendation page list the same missing fields.
- If DB has phone/location, missing fields do not include phone/location.
- If only years experience is missing, only years experience appears in the missing field list.
- Recommendations show stored offer cards when profile is usable.
- Incomplete profile shows blocked state, not fake empty/no-match state.

## OAuth/provider acceptance

- Social account provisioning fills full name when available.
- GitHub profile URL fills when available.
- Avatar/photo URL is stored/displayed when available.
- Existing user-entered fields are not overwritten silently.
- No OAuth token is stored in CandidateProfile.
- Connect buttons exist for missing Google/GitHub providers.
- Already-connected provider state is clear.

## Security/privacy acceptance

- No raw CV text rendered.
- No CV file URL rendered.
- No secrets in diff.
- No OpenRouter/LLM calls from views/templates.
- No France Travail live calls from public job search.
- No forbidden frontend stack.

## Human acceptance

Automated tests are not enough. Baha must manually approve in Chrome:

- account pages
- social provider connection page
- set password page
- CV page
- profile page
- recommendations page
- mobile layout

Until Baha approves, verdict is `BLOCKED_HUMAN_VISUAL_SIGNOFF`.
