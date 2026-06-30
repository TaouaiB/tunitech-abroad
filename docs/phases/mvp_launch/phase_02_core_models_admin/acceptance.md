# Phase 2 — Acceptance Criteria

Phase: Core Database Models and Admin

## 1. Required models exist

The following models must exist:

```text
apps.profiles.models.CandidateProfile
apps.profiles.models.ProfileSkill
apps.notifications.models.EmailPreference
apps.privacy.models.ConsentRecord
apps.analytics.models.UserEvent
apps.core.models.SystemSetting
```

## 2. Required apps exist and are configured

The following apps must exist and be installed correctly:

```text
apps.profiles
apps.notifications
apps.privacy
apps.analytics
apps.core
```

If `apps.core` already existed from Phase 1, it should be reused, not recreated incorrectly.

## 3. Public ID rule

`CandidateProfile` must have:

```python
public_id = models.UUIDField(..., unique=True, db_index=True, editable=False)
```

Public URLs are not required yet, but the field must be ready.

## 4. ProfileSkill boundary rule

`ProfileSkill` must not depend on a `Skill` model yet.

Allowed:

```text
raw_name
normalized_name
source
confidence
```

Forbidden in Phase 2:

```python
ForeignKey("skills.Skill")
```

because the skill taxonomy starts in Phase 3.

## 5. EmailPreference boundary rule

Allowed:

```text
EmailPreference
```

Forbidden:

```text
EmailBatch
EmailEvent
EmailUnsubscribeToken
weekly digest sender
real email provider integration
```

Email delivery is not Phase 2.

## 6. Privacy boundary rule

Allowed:

```text
ConsentRecord
ConsentService.record_consent
```

Forbidden:

```text
DeletionRequest
account deletion workflow
CV deletion workflow
data export workflow
```

Those come later.

## 7. Analytics boundary rule

Allowed:

```text
UserEvent
UserEventService.record_event
```

Forbidden:

```text
external analytics
tracking scripts
cookie banner
marketing pixels
```

## 8. Account provisioning

`AccountProvisioningService` must:

```text
create CandidateProfile for new user
create EmailPreference for new user
be idempotent
use get_or_create
not create duplicate objects
```

Calling it twice for the same user must not fail and must not duplicate records.

## 9. Admin

The following models must be visible in Django Admin:

```text
CandidateProfile
ProfileSkill
EmailPreference
ConsentRecord
UserEvent
SystemSetting
```

Admin should include useful:

```text
list_display
search_fields
list_filter
readonly_fields
```

No custom admin dashboard should be built.

## 10. Migrations

Migrations must be created and clean.

Required checks:

```bash
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
```

Expected:

```text
No model changes pending after migrations.
Migrations apply cleanly.
```

## 11. Tests

Tests must cover:

```text
CandidateProfile creation
ProfileSkill unique normalized skill per profile
EmailPreference creation
ConsentService.record_consent
UserEventService.record_event
SystemSettingService.get_value or SystemSetting creation
AccountProvisioningService idempotency
Admin registration smoke where practical
```

Required test command:

```bash
python manage.py test --settings=config.settings.local
```

Expected:

```text
OK
```

## 12. Browser/manual checks

If the Django server can run, Antigravity should also perform browser/manual checks where useful:

```text
Homepage still loads.
Login page still loads.
Signup page still loads.
Dashboard still redirects anonymous users to login.
Admin login page loads.
After superuser login, new Phase 2 models are visible in Django Admin if credentials are available or if the browser session is already authenticated.
```

If browser testing is not possible, the agent must state why in the report and still run terminal tests.

## 13. Phase boundary

The phase must not create or implement:

```text
skills app/models
jobs app/models
CV upload/parsing
matching/scoring
recommendations
LLM/OpenRouter integration
weekly digest
real email sending
privacy deletion workflow
frontend redesign
```

## 14. Final checks required

The final report must show all of these passing:

```bash
python --version
python -m django --version
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

## 15. Git behavior

The agent must not:

```text
commit
merge
push
```

The user will commit manually after review.
