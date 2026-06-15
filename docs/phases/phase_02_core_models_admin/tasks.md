# Phase 2 — Core Database Models and Admin

## Phase goal

Create the first core database layer after authentication.

This phase adds the user-adjacent and platform support models that future phases need:

- Candidate profile shell
- Profile skill shell
- Email preferences
- Consent records
- User events
- System settings
- Django Admin registration for these models

This phase does **not** implement jobs, CV parsing, matching, recommendations, LLM, or weekly digest logic.

---

## Source documents to read first

Before coding, read:

```text
AGENTS.md
docs/planning/04_Database_Schema_v1.md
docs/planning/05_Service_Contracts_v1.md
docs/planning/08_Implementation_Roadmap_v1.md
docs/planning/09_MVP_Backlog_v1.md
docs/phases/phase_02_core_models_admin/tasks.md
docs/phases/phase_02_core_models_admin/acceptance.md
```

If there is a conflict, follow:

```text
AGENTS.md
→ current phase files
→ planning docs
```

---

## Tickets

## TTA-0201 — Create CandidateProfile model

### App

Create or use:

```text
apps/profiles/
```

### Model

Create:

```text
CandidateProfile
```

### Required fields

Use the existing custom user model from Phase 1.

Suggested fields:

```python
user = OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="candidate_profile")

public_id = UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

full_name = CharField(max_length=255, blank=True)
phone = CharField(max_length=50, blank=True)
location = CharField(max_length=255, blank=True)

linkedin_url = URLField(blank=True)
github_url = URLField(blank=True)
portfolio_url = URLField(blank=True)
website_url = URLField(blank=True)

french_level = CharField(max_length=20, blank=True)
english_level = CharField(max_length=20, blank=True)

target_country = CharField(max_length=100, default="France")
target_roles = JSONField(default=list, blank=True)
target_job_types = JSONField(default=list, blank=True)

relocation_preference = CharField(max_length=50, blank=True)
remote_preference = CharField(max_length=50, blank=True)

profile_completion_score = PositiveSmallIntegerField(default=0)

created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
```

### Important

Do not add CV fields here. CV-specific data belongs to Phase 6.

Do not add matching or recommendation fields here.

---

## TTA-0202 — Create ProfileSkill shell model

### App

```text
apps/profiles/
```

### Model

```text
ProfileSkill
```

### Purpose

This is the user-owned skill association shell.

Skill taxonomy itself comes in Phase 3.

For Phase 2, do **not** create `skills.Skill` yet.

### Fields

Use a temporary raw/canonical text design that can later be linked to `skills.Skill`.

Suggested fields:

```python
profile = ForeignKey(CandidateProfile, on_delete=CASCADE, related_name="profile_skills")

raw_name = CharField(max_length=150)
normalized_name = CharField(max_length=150, db_index=True)

source = CharField(max_length=50, blank=True)
confidence = PositiveSmallIntegerField(default=100)

created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
```

### Constraints

Add a uniqueness constraint to prevent duplicate normalized skills per profile:

```text
profile + normalized_name unique
```

### Important

Do not create the `skills` app or `Skill` model in this phase.

Do not use a ForeignKey to `Skill` yet.

---

## TTA-0203 — Create EmailPreference model

### App

Create or use:

```text
apps/notifications/
```

### Model

```text
EmailPreference
```

### Fields

```python
user = OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="email_preferences")

product_updates_enabled = BooleanField(default=False)
weekly_digest_enabled = BooleanField(default=False)
cv_analysis_email_enabled = BooleanField(default=True)

created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
```

### Important

Do not create EmailBatch, EmailEvent, digest generation, unsubscribe tokens, or real email sending in this phase.

Those belong to later email phases.

---

## TTA-0204 — Create ConsentRecord and ConsentService

### App

Create or use:

```text
apps/privacy/
```

### Model

```text
ConsentRecord
```

### Fields

```python
user = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="consent_records")

consent_type = CharField(max_length=100)
consent_version = CharField(max_length=50)
accepted = BooleanField(default=True)

ip_address = GenericIPAddressField(null=True, blank=True)
user_agent = TextField(blank=True)

created_at = DateTimeField(auto_now_add=True)
```

### Service

Create:

```text
apps/privacy/services/consent.py
```

With:

```python
class ConsentService:
    @staticmethod
    def record_consent(...)
```

### Important

This phase only records consent.

Do not create account deletion or data deletion workflows yet.

---

## TTA-0205 — Create UserEvent and UserEventService

### App

Create or use:

```text
apps/analytics/
```

### Model

```text
UserEvent
```

### Fields

```python
user = ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=SET_NULL, related_name="user_events")

event_type = CharField(max_length=100, db_index=True)
metadata = JSONField(default=dict, blank=True)

created_at = DateTimeField(auto_now_add=True)
```

### Service

Create:

```text
apps/analytics/services/user_event.py
```

With:

```python
class UserEventService:
    @staticmethod
    def record_event(...)
```

### Important

No external analytics tools.

No tracking scripts.

No cookies banner implementation in this phase.

---

## TTA-0206 — Create SystemSetting model

### App

Create or use:

```text
apps/core/
```

### Model

```text
SystemSetting
```

### Fields

```python
key = CharField(max_length=100, unique=True)
value = JSONField(default=dict, blank=True)
description = TextField(blank=True)
is_active = BooleanField(default=True)

created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
```

### Service

Optional but recommended:

```text
apps/core/services/system_setting.py
```

With:

```python
class SystemSettingService:
    @staticmethod
    def get_value(key, default=None)
```

---

## TTA-0207 — Update AccountProvisioningService

Update the Phase 1 provisioning shell so new users automatically receive:

```text
CandidateProfile
EmailPreference
```

### Rules

Must be idempotent.

Use:

```python
get_or_create
```

Do not create duplicate records if called multiple times.

Do not create Phase 3+ objects.

---

## TTA-0208 — Admin registration

Register these models in Django Admin:

```text
CandidateProfile
ProfileSkill
EmailPreference
ConsentRecord
UserEvent
SystemSetting
```

Admin should be simple but useful:

- list display
- search fields where useful
- list filters where useful
- readonly timestamps/public_id where useful

Do not overbuild custom admin pages.

---

## TTA-0209 — Migrations and tests

Create migrations for new models.

Add tests for:

```text
CandidateProfile creation
ProfileSkill uniqueness
EmailPreference creation
ConsentRecord creation through service
UserEvent creation through service
SystemSetting creation/value retrieval
AccountProvisioningService creates profile + email preference idempotently
No Phase 3+ models created
```

Run full checks:

```bash
python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

---

## Phase boundary

This phase must not create:

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

---

## Final deliverable

At the end, generate:

```text
docs/phases/phase_02_core_models_admin/agent_report.md
```

Use the provided report template.
