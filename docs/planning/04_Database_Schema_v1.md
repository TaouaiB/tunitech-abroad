# TuniTech Abroad - Database Schema v1

<!-- Converted to Markdown for repository/agent context. The original generated PDF/DOCX remains the formatted source-of-truth document. -->


TuniTech Abroad
Database Schema v1
Final validation draft before Service Contracts and implementation
Generated for the France-first IT job intelligence MVP
Architecture baseline: Django + PostgreSQL + Redis/Celery + OpenRouter + France Travail API
Schema style: normalized relational schema with controlled JSON usage
Public identifier strategy: internal BigAutoField IDs + UUID public_id for public routes

### 1. Document Purpose
This document defines the database schema for TuniTech Abroad MVP. It translates the BRD, PRD, and
Technical Architecture into a Django/PostgreSQL-ready schema. It defines apps, models, fields, relationships,
delete behavior, constraints, indexes, JSON fields, status enums, seed data, and migration order.
### 2. Schema Principles
- PostgreSQL is the source of truth. Redis is only for Celery broker, cache, rate limits, locks, and temporary
counters.
- External job data is stored raw before normalization. RawJobRecord protects against API changes and allows
replay of normalization.
- Final fit score is deterministic. LLM output supports extraction and explanation but is not the scoring
authority.
- User-confirmed profile data is stronger than parsed CV data.
- PostgreSQL full-text search is used for job search from MVP. Avoid large icontains searches on descriptions.
- Privacy is first-class: CV deletion, account deletion, consent records, email opt-out, private CV storage.
### 3. Django Apps and Main Models
App
Models
accounts
User
profiles
CandidateProfile, ProfileSkill
cvs
CVUpload, CVParsedData
jobs
JobSource, IngestionRun, RawJobRecord, NormalizedJob, NormalizedJobSkill
skills
Skill, SkillAlias, UnmatchedSkillCandidate
matching
MatchResult, QuickMatchSession
recommendations
JobRecommendation, RecommendationRun, SavedJob
notifications
EmailPreference, EmailBatch, EmailEvent, EmailUnsubscribeToken
llm
PromptVersion, LLMCacheEntry, LLMUsageLog
privacy
ConsentRecord, DeletionRequest
analytics
UserEvent
core
SystemSetting optional
### 4. Shared Field and ID Conventions
Most business models include id, created_at, and updated_at. Use Django default BigAutoField for internal
primary keys. For public-facing routes, expose UUID public_id instead of integer pk.
public_id = models.UUIDField(
    default=uuid.uuid4,
    unique=True,
    editable=False,
    db_index=True,
)
Public routes must use public_id:
/jobs/<uuid:public_id>/
/matches/<uuid:public_id>/
Never expose internal URLs like:
/jobs/123/
/matches/456/
Public ID required on

- NormalizedJob
- CVUpload
- MatchResult
- QuickMatchSession
### 5. Common Enum Values
Enum
Values
current_level
student, internship_seeker, junior, mid_level, senior, unknown
target_type
summer_internship, standard_internship, pfe_end_of_study, first_job, junior_job,
mid_level_job, unknown
language_level
unknown, A1, A2, B1, B2, C1, C2, native
remote_preference
remote, hybrid, on_site, any, unknown
relocation_preference
willing_to_relocate, remote_only, already_in_france, not_ready, unknown
job_status
active, stale, expired, removed, archived
job_type
internship, full_time_job, apprenticeship, contract, unknown
remote_type
remote, hybrid, on_site, unknown
parse_status
pending, processing, parsed, parsed_with_warnings, failed, deleted
llm_status
not_requested, pending, success, failed, cached, disabled
### 6. Accounts Schema
6.1 accounts.User
Custom User model from the beginning. Email is unique. Supports email/password, Google, GitHub, and
admin accounts.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
username
CharField
no
Optional or auto-generated
email
EmailField
yes
Unique
first_name
CharField
no
Django default
last_name
CharField
no
Django default
password
CharField
no
Empty for pure social users
is_active
BooleanField
yes
Default true
is_staff
BooleanField
yes
Admin access
is_superuser
BooleanField
yes
Superuser access
date_joined
DateTimeField
yes
Auto
last_login
DateTimeField
no
Django default
Constraints:
- unique(email)
Indexes:
- email
- is_active
- is_staff
- last_login
- date_joined
Delete behavior:
- Controlled through privacy/account deletion flow.
### 7. Profiles Schema

7.1 profiles.CandidateProfile
Stores the candidate's editable/confirmed profile. This is the main source for matching.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
OneToOneField(User)
yes
One profile per user
full_name
CharField
no
Prefilled from auth/CV
phone
CharField
no
Candidate phone
location
CharField
no
Current location
linkedin_url
URLField
no
Manual field
github_url
URLField
no
Manual/OAuth-derived
portfolio_url
URLField
no
Portfolio
website_url
URLField
no
Personal site
current_level
CharField choices
yes
Default unknown
years_experience
DecimalField
no
Example: 1.5
target_country
CharField
yes
MVP default France
target_roles
JSONField
no
List of target roles for MVP
target_type
CharField choices
yes
Job/internship target
french_level
CharField choices
yes
Default unknown
english_level
CharField choices
yes
Default unknown
relocation_preference
CharField choices
yes
Default unknown
remote_preference
CharField choices
yes
Default unknown
profile_completeness_sco
re
PositiveSmallIntegerField
yes
0-100
profile_completeness_stat
us
CharField
yes
incomplete/usable/strong
is_confirmed
BooleanField
yes
User reviewed profile
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Constraints:
- unique(user)
Indexes:
- user
- current_level
- target_country
- target_type
- profile_completeness_status
- updated_at
Implementation note:
- target_roles remains JSONField for MVP.
- If role matching or analytics become slow, migrate later to TargetRole and CandidateProfileTargetRole
  tables.
7.2 profiles.ProfileSkill
Stores canonical skills confirmed or inferred for a candidate profile. Matching should use this relational table,
not raw JSON only.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
profile
ForeignKey(CandidateProfile)
yes
Candidate profile
skill
ForeignKey(Skill)
yes
Canonical skill
source
CharField
yes
user/cv_regex/cv_llm/oauth_github/admin

Field
Type
Required
Notes
confidence
DecimalField
no
0-1
is_confirmed
BooleanField
yes
User confirmed
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Constraints:
- unique(profile, skill)
Indexes:
- profile
- skill
- source
- is_confirmed
Delete behavior:
- profile deleted -> profile skills deleted
- skill should not be deleted normally; use Skill.is_active=false
### 8. CV Schema
8.1 cvs.CVUpload
Stores CV file metadata. Physical file is stored in private media. This model uses soft delete, with a
mandatory safe manager.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
public_id
UUIDField
yes
Unique public identifier
user
ForeignKey(User)
yes
Owner
file
FileField
yes
Private media path
original_filename
CharField
yes
Original upload name
file_hash
CharField
yes
SHA256
file_size
PositiveIntegerField
yes
Bytes
mime_type
CharField
yes
application/pdf
is_active
BooleanField
yes
One active CV
parse_status
CharField choices
yes
pending/processing/etc.
parse_error
TextField
no
Failure reason
text_extraction_status
CharField
no
success/failed/too_little_text
extracted_text_length
PositiveIntegerField
no
Number of chars
uploaded_at
DateTimeField
yes
Auto
parsed_at
DateTimeField
no
Set after parse
deleted_at
DateTimeField
no
Soft delete timestamp
Mandatory implementation:
class ActiveCVManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
class CVUpload(models.Model):
    objects = ActiveCVManager()      # safe default manager
    all_objects = models.Manager()   # admin/privacy/deletion/internal access
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.parse_status = "deleted"

self.save(update_fields=["is_active", "deleted_at", "parse_status"])
Constraints:
- unique(public_id)
- partial unique: unique(user) where is_active=true and deleted_at is null
Indexes:
- user
- public_id
- file_hash
- parse_status
- is_active
- uploaded_at
- deleted_at
8.2 cvs.CVParsedData
Stores parsed and structured CV extraction results. Includes deterministic extraction and LLM structured
extraction.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
cv_upload
OneToOneField(CVUpload)
yes
Parsed data for CV
raw_text
TextField
no
Extracted PDF text
deterministic_json
JSONField
no
Regex extracted fields
llm_json
JSONField
no
Structured LLM output
merged_json
JSONField
no
Combined extraction
extraction_method
CharField
yes
regex_only/regex_llm/manual/failed
llm_schema_version
CharField
no
Example cv_extract_v1
extracted_name
CharField
no
Convenience field
extracted_email
EmailField
no
Convenience field
extracted_phone
CharField
no
Convenience field
extracted_location
CharField
no
Convenience field
extracted_linkedin_url
URLField
no
Convenience field
extracted_github_url
URLField
no
Convenience field
extracted_portfolio_url
URLField
no
Convenience field
estimated_years_experien
ce
DecimalField
no
LLM/user estimated
confidence_json
JSONField
no
Field confidence
warnings_json
JSONField
no
Extraction warnings
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
LLM extraction schema contract:
{
  "candidate": {
    "full_name": null,
    "email": null,
    "phone": null,
    "location": null,
    "linkedin_url": null,
    "github_url": null,
    "portfolio_url": null,
    "website_url": null
  },
  "skills": {"technical": [], "tools": [], "soft": []},
  "experience": [{"title": null, "company": null, "start_date": null, "end_date": null, "description":
  null, "technologies": []}],
  "projects": [{"name": null, "description": null, "technologies": [], "links": []}],
  "education": [{"degree": null, "institution": null, "start_year": null, "end_year": null}],
  "certifications": [],

"languages": [{"language": null, "level": null}],
  "estimated_years_experience": null,
  "warnings": [],
  "confidence": {"identity": 0, "skills": 0, "experience": 0, "education": 0, "languages": 0}
}
Indexes:
- cv_upload
- extraction_method
- llm_schema_version
- created_at
Delete behavior:
- CVUpload deleted -> CVParsedData deleted
### 9. Job Source and Ingestion Schema
9.1 jobs.JobSource
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
name
CharField
yes
Human-readable
slug
SlugField
yes
france_travail
base_url
URLField
no
API base
source_type
CharField
yes
api/manual/fixture
is_active
BooleanField
yes
Enable/disable
last_successful_sync_at
DateTimeField
no
Last success
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Constraints:
- unique(slug)
Indexes:
- slug
- is_active
- last_successful_sync_at
MVP seed:
- slug = france_travail
- source_type = api
9.2 jobs.IngestionRun
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
source
ForeignKey(JobSource)
yes
Source
status
CharField choices
yes
running/success/partial_success/failed
trigger_type
CharField
yes
scheduled/manual_admin/startup_fixture/retry
started_at
DateTimeField
yes
Start time
finished_at
DateTimeField
no
End time
search_params_json
JSONField
no
Query params
fetched_count
PositiveIntegerField
yes
Default 0
created_count
PositiveIntegerField
yes
Default 0
updated_count
PositiveIntegerField
yes
Default 0
unchanged_count
PositiveIntegerField
yes
Default 0
marked_stale_count
PositiveIntegerField
yes
Default 0
marked_expired_count
PositiveIntegerField
yes
Default 0

Field
Type
Required
Notes
error_count
PositiveIntegerField
yes
Default 0
error_message
TextField
no
Summary
created_at
DateTimeField
yes
Auto
Indexes:
- source
- status
- started_at
- finished_at
- trigger_type
Delete behavior:
- source deleted -> protect
9.3 jobs.RawJobRecord
Stores original external API payload. Do not normalize external data without this record.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
source
ForeignKey(JobSource)
yes
Source
source_job_id
CharField
yes
External ID
raw_payload_json
JSONField
yes
Original payload
payload_hash
CharField
yes
SHA256 canonical JSON
first_seen_at
DateTimeField
yes
First import
last_seen_at
DateTimeField
yes
Last seen in source
last_fetched_at
DateTimeField
yes
Last fetched detail
source_status
CharField
no
Source-specific status
normalization_status
CharField
yes
pending/success/failed/skipped_unchanged
normalization_error
TextField
no
Error
ingestion_run
ForeignKey(IngestionRun)
no
Last run
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Constraints:
- unique(source, source_job_id)
Indexes:
- source
- source_job_id
- payload_hash
- last_seen_at
- last_fetched_at
- normalization_status
- ingestion_run
Delete behavior:
- source deleted -> protect
- ingestion_run deleted -> set null
9.4 jobs.NormalizedJob
Stores clean searchable jobs used by the application.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
public_id
UUIDField
yes
Unique public route ID
source
ForeignKey(JobSource)
yes
Source

Field
Type
Required
Notes
raw_record
OneToOneField(RawJobRecor
d)
yes
Raw payload
source_job_id
CharField
yes
External ID duplicate for lookup
title
CharField
yes
Job title
company_name
CharField
no
Company
location
CharField
no
Full location label
country
CharField
yes
MVP France
city
CharField
no
City
department
CharField
no
French department
region
CharField
no
Region
contract_type
CharField
no
CDI/CDD/etc.
remote_type
CharField choices
yes
remote/hybrid/on_site/unknown
job_type
CharField choices
yes
internship/full_time/etc.
experience_level
CharField
yes
internship/junior/mid_level/senior/unknown
description
TextField
yes
Clean description
source_url
URLField
no
External apply/details link
published_at
DateTimeField
no
Source publication
expires_at
DateTimeField
no
Source expiry if available
first_seen_at
DateTimeField
yes
From raw
last_seen_at
DateTimeField
yes
From raw
last_fetched_at
DateTimeField
yes
From raw
status
CharField choices
yes
active/stale/etc.
normalization_version
CharField
yes
Example ft_v1
skill_extraction_status
CharField
yes
pending/success/failed/not_enough_text
required_skills_json
JSONField
no
Raw/canonical labels snapshot
optional_skills_json
JSONField
no
Raw/canonical labels snapshot
language_requirements_j
son
JSONField
no
French/English requirements
search_vector
SearchVectorField
no
PostgreSQL FTS
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Constraints:
- unique(source, source_job_id)
- unique(raw_record)
- unique(public_id)
Indexes:
- public_id
- source
- source_job_id
- status
- job_type
- contract_type
- remote_type
- experience_level
- country, city, department, region
- published_at, expires_at
- last_seen_at, last_fetched_at
- search_vector GIN
Full-text search weights:
- title: A
- required skills: A
- optional skills: B
- company: B

- location: C
- description: D
Delete behavior:
- raw_record deleted -> normalized job deleted
- source deleted -> protect
- normal operational deletion should be status update, not delete
9.5 jobs.NormalizedJobSkill
Stores canonical skills attached to a job. Matching uses this relational table.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
job
ForeignKey(NormalizedJob)
yes
Job
skill
ForeignKey(Skill)
yes
Canonical skill
requirement_type
CharField
yes
required/optional/detected/unknown
source
CharField
yes
rule/llm/admin/source_api
confidence
DecimalField
no
0-1
created_at
DateTimeField
yes
Auto
Constraints:
- unique(job, skill, requirement_type)
Indexes:
- job
- skill
- requirement_type
- source
- confidence
Delete behavior:
- job deleted -> job skills deleted
- skill deleted -> protect
### 10. Skill Taxonomy Schema
10.1 skills.Skill
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
canonical_name
CharField
yes
Python, Django, Docker
slug
SlugField
yes
python
category
CharField choices
yes
backend/devops/etc.
is_active
BooleanField
yes
Use false instead of delete
source
CharField
yes
manual/esco/imported/admin
esco_uri
URLField
no
Optional ESCO reference
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Categories:
programming_language, frontend, backend, database, devops, cloud, testing,
data_ai, mobile, tools, methodology, soft_skill, other
Constraints:
- unique(slug)
- unique(canonical_name)
Indexes:
- slug
- canonical_name

- category
- is_active
- source
Delete behavior:
- Do not delete skills normally. Use is_active=false.
10.2 skills.SkillAlias
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
skill
ForeignKey(Skill)
yes
Canonical skill
alias
CharField
yes
Original alias
normalized_alias
CharField
yes
Lowercase normalized form
language
CharField
no
fr/en/unknown
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Examples:
- ReactJS -> React
- Postgres -> PostgreSQL
- Python3 -> Python
Constraints:
- unique(normalized_alias)
Indexes:
- skill
- normalized_alias
- language
Delete behavior:
- skill deleted -> protect
10.3 skills.UnmatchedSkillCandidate
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
raw_skill_text
CharField
yes
Original text
normalized_text
CharField
yes
Normalized text
source_type
CharField
yes
cv/job/quick_match/manual
source_model
CharField
no
CVUpload/NormalizedJob
source_object_id
BigIntegerField
no
Source ID
occurrence_count
PositiveIntegerField
yes
Default 1
status
CharField choices
yes
pending/mapped/ignored
mapped_skill
ForeignKey(Skill)
no
If mapped
reviewed_by
ForeignKey(User)
no
Admin
reviewed_at
DateTimeField
no
Review time
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Constraints:
- unique(normalized_text, source_type)
Indexes:
- normalized_text
- source_type
- status
- mapped_skill
- reviewed_by

- occurrence_count
- created_at
Delete behavior:
- mapped_skill deleted -> set null
- reviewed_by deleted -> set null
### 11. Matching Schema
11.1 matching.MatchResult
Stores a full match calculation between a user/profile/CV and a job. Includes snapshots to preserve past
match context.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
public_id
UUIDField
yes
Public-safe ID
user
ForeignKey(User)
yes
Owner
profile
ForeignKey(CandidateProfil
e)
yes
Profile snapshot source
cv_upload
ForeignKey(CVUpload)
no
Active CV used
job
ForeignKey(NormalizedJob)
yes
Matched job
profile_snapshot_json
JSONField
yes
Profile at calculation time
job_snapshot_json
JSONField
yes
Job at calculation time
fit_score
PositiveSmallIntegerField
yes
0-100
technical_skills_score
PositiveSmallIntegerField
yes
0-100
experience_score
PositiveSmallIntegerField
yes
0-100
role_title_score
PositiveSmallIntegerField
yes
0-100
language_score
PositiveSmallIntegerField
yes
0-100
location_score
PositiveSmallIntegerField
yes
0-100
strong_skills_json
JSONField
no
Matched skills
missing_required_skills_jso
n
JSONField
no
Missing required
missing_optional_skills_jso
n
JSONField
no
Missing optional
risk_flags_json
JSONField
no
Score-relevant risks
profile_signals_json
JSONField
no
Non-score profile signals
recommended_actions_jso
n
JSONField
no
Deterministic actions
llm_explanation_status
CharField choices
yes
not_requested/etc.
llm_explanation_text
TextField
no
AI explanation
scoring_version
CharField
yes
Example score_v1
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Fit score formula:
fit_score =
  technical_skills_score * 0.45
+ experience_score * 0.20
+ role_title_score * 0.15
+ language_score * 0.10
+ location_score * 0.10
No unique(user, job): user may recompute after CV/profile changes.
Indexes:
- public_id

- user, profile, cv_upload, job
- fit_score
- created_at
- llm_explanation_status
- scoring_version
- (user, job)
- (user, created_at)
- (job, fit_score)
11.2 matching.QuickMatchSession
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
public_id
UUIDField
yes
Public-safe ID
session_key_hash
CharField
yes
Hashed session key
ip_hash
CharField
no
For rate limiting
job
ForeignKey(NormalizedJob)
yes
Tested job
entered_skills_json
JSONField
yes
User-entered skills
normalized_skills_json
JSONField
no
Canonical skills
experience_level
CharField
yes
User input
french_level
CharField
yes
User input
estimated_fit_score
PositiveSmallIntegerField
yes
0-100
matched_skills_json
JSONField
no
Matched
missing_skills_json
JSONField
no
Missing
created_at
DateTimeField
yes
Auto
expires_at
DateTimeField
yes
24h default
Constraints:
- unique(public_id)
Indexes:
- public_id
- session_key_hash
- ip_hash
- job
- created_at
- expires_at
- estimated_fit_score
### 12. Recommendation Schema
12.1 recommendations.JobRecommendation
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
ForeignKey(User)
yes
Owner
profile
ForeignKey(CandidateProfil
e)
yes
Profile used
cv_upload
ForeignKey(CVUpload)
no
CV used
job
ForeignKey(NormalizedJob)
yes
Recommended job
fit_score
PositiveSmallIntegerField
yes
Candidate-job fit
ranking_score
DecimalField
yes
Final rank
rank
PositiveIntegerField
yes
1, 2, 3...
strong_skills_json
JSONField
no
Matched
missing_skills_json
JSONField
no
Missing
risk_flags_json
JSONField
no
Risks

Field
Type
Required
Notes
profile_signals_json
JSONField
no
Non-score signals
reason_summary
TextField
no
Short deterministic summary
recommendation_version
CharField
yes
reco_v1
computed_at
DateTimeField
yes
Calculation time
status
CharField choices
yes
active/stale/dismissed/expired_job
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Ranking score:
ranking_score = fit_score + freshness_boost + target_type_boost + user_preference_boost -
  stale_job_penalty
Constraints:
- unique(user, job, recommendation_version) for MVP
Indexes:
- user, profile, cv_upload, job
- fit_score, ranking_score, rank
- status, computed_at, recommendation_version
- (user, status, ranking_score)
- (user, rank)
- (job, status)
12.2 recommendations.RecommendationRun
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
ForeignKey(User)
no
Null for bulk run
trigger_type
CharField
yes
cv_uploaded/profile_updated/etc.
status
CharField choices
yes
running/success/partial_success/failed
started_at
DateTimeField
yes
Start
finished_at
DateTimeField
no
End
candidate_jobs_count
PositiveIntegerField
yes
Default 0
scored_jobs_count
PositiveIntegerField
yes
Default 0
stored_recommendations
_count
PositiveIntegerField
yes
Default 0
error_message
TextField
no
Error
created_at
DateTimeField
yes
Auto
Trigger types:
cv_uploaded, cv_replaced, profile_updated, new_jobs_imported,
dashboard_stale_refresh, nightly_refresh, manual_admin
Indexes:
- user
- trigger_type
- status
- started_at
- finished_at
Delete behavior:
- user deleted -> set null
12.3 recommendations.SavedJob
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
ForeignKey(User)
yes
Owner

Field
Type
Required
Notes
job
ForeignKey(NormalizedJob)
yes
Saved job
notes
TextField
no
Future
saved_at
DateTimeField
yes
Auto
Constraints:
- unique(user, job)
Indexes:
- user
- job
- saved_at
### 13. LLM Schema
13.1 llm.PromptVersion
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
name
CharField
yes
cv_extract
version
CharField
yes
v1
purpose
CharField
yes
cv_extraction/etc.
template_text
TextField
yes
Prompt
output_schema_json
JSONField
no
Expected schema
is_active
BooleanField
yes
Active version
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Purposes:
cv_extraction, job_skill_extraction, match_explanation, cv_advice, missing_skill_roadmap
Constraints:
- unique(name, version)
Indexes:
- name
- purpose
- is_active
- created_at
13.2 llm.LLMCacheEntry
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
cache_key
CharField
yes
Unique
purpose
CharField
yes
cv_extraction/etc.
input_hash
CharField
yes
Hash of input
prompt_version
ForeignKey(PromptVersion)
yes
Prompt used
response_json
JSONField
no
JSON result
response_text
TextField
no
Raw text
status
CharField
yes
success/failed
created_at
DateTimeField
yes
Auto
expires_at
DateTimeField
no
Optional
Constraints:
- unique(cache_key)
Indexes:

- cache_key
- purpose
- input_hash
- prompt_version
- status
- created_at
- expires_at
Delete behavior:
- prompt_version deleted -> protect
13.3 llm.LLMUsageLog
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
ForeignKey(User)
no
Null for system jobs
purpose
CharField
yes
cv_extraction/etc.
provider
CharField
yes
openrouter
model
CharField
yes
Model name
prompt_version
ForeignKey(PromptVersion)
no
Prompt
cache_hit
BooleanField
yes
True/false
input_token_estimate
PositiveIntegerField
no
Optional
output_token_estimate
PositiveIntegerField
no
Optional
cost_estimate
DecimalField
no
Optional
status
CharField
yes
success/failed/cached/skipped_limit
error_message
TextField
no
Error
created_at
DateTimeField
yes
Auto
Indexes:
- user
- purpose
- provider
- model
- cache_hit
- status
- created_at
- prompt_version
Delete behavior:
- user deleted -> set null
- prompt_version protected
### 14. Notification Schema
14.1 notifications.EmailPreference
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
OneToOneField(User)
yes
One preferences row
weekly_digest_enabled
BooleanField
yes
Default false
product_updates_enabled
BooleanField
yes
Default false
instant_alerts_enabled
BooleanField
yes
Default false, hidden MVP
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Constraints:
- unique(user)
Indexes:

- user
- weekly_digest_enabled
- product_updates_enabled
- instant_alerts_enabled
14.2 notifications.EmailBatch
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
batch_type
CharField
yes
weekly_digest/product_update/system_notice
period_start
DateTimeField
yes
Week start
period_end
DateTimeField
yes
Week end
status
CharField
yes
running/success/partial_success/failed
created_at
DateTimeField
yes
Auto
completed_at
DateTimeField
no
End time
error_message
TextField
no
Error
Constraints:
- unique(batch_type, period_start, period_end)
Indexes:
- batch_type
- status
- period_start
- period_end
- created_at
14.3 notifications.EmailEvent
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
ForeignKey(User)
no
Recipient user
batch
ForeignKey(EmailBatch)
no
For digest/batch
email_type
CharField
yes
verification/digest/etc.
recipient_email
EmailField
yes
Recipient
subject
CharField
yes
Subject
provider
CharField
yes
resend/brevo/etc.
provider_message_id
CharField
no
Provider ID
idempotency_key
CharField
yes
Unique send key
status
CharField
yes
queued/sent/failed/skipped
error_message
TextField
no
Failure
sent_at
DateTimeField
no
Send time
created_at
DateTimeField
yes
Auto
Constraints:
- unique(idempotency_key)
Example idempotency keys:
- weekly_digest:user_id:2026-W24
- email_verification:user_id:token_hash
- password_reset:user_id:token_hash
Indexes:
- user, batch, email_type, recipient_email, provider, provider_message_id
- idempotency_key
- status
- sent_at
- created_at

14.4 notifications.EmailUnsubscribeToken
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
ForeignKey(User)
yes
User
token_hash
CharField
yes
Store hash, not raw token
purpose
CharField
yes
digest/product_updates
created_at
DateTimeField
yes
Auto
expires_at
DateTimeField
no
Optional
used_at
DateTimeField
no
Optional
Constraints:
- unique(token_hash)
Indexes:
- user
- token_hash
- purpose
- expires_at
- used_at
### 15. Privacy Schema
15.1 privacy.ConsentRecord
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
ForeignKey(User)
yes
User
consent_type
CharField
yes
cv_processing/etc.
consent_text
TextField
yes
Text accepted
consent_version
CharField
yes
Version
accepted_at
DateTimeField
yes
Acceptance time
ip_address_hash
CharField
no
Hashed IP
user_agent
TextField
no
Browser info
Consent types:
- cv_processing
- email_digest
- terms
- privacy_policy
- cookie_session_notice
Indexes:
- user
- consent_type
- consent_version
- accepted_at
15.2 privacy.DeletionRequest
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
ForeignKey(User)
no
Set null after deletion if needed
status
CharField
yes
pending/processing/completed/failed
requested_at
DateTimeField
yes
Request time
processed_at
DateTimeField
no
Completion time
error_message
TextField
no
Error

Field
Type
Required
Notes
metadata_json
JSONField
no
Counts deleted/anonymized
Indexes:
- user
- status
- requested_at
- processed_at
Delete behavior:
- user deleted -> set null
### 16. Analytics Schema
16.1 analytics.UserEvent
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
user
ForeignKey(User)
no
Null for anonymous
session_key_hash
CharField
no
Anonymous tracking
event_type
CharField
yes
Event name
metadata_json
JSONField
no
Extra context
created_at
DateTimeField
yes
Auto
Event types:
job_search, job_detail_view, quick_match_started, quick_match_completed,
signup_started, signup_completed, cv_uploaded, cv_parse_failed,
profile_completed, match_generated, recommendation_clicked, saved_job_created,
source_apply_clicked, email_digest_clicked, account_deleted
Indexes:
- user
- session_key_hash
- event_type
- created_at
Delete behavior:
- user deleted -> set null and remove personal metadata during deletion
### 17. Optional Core Schema
17.1 core.SystemSetting
Recommended early because it avoids hardcoding thresholds.
Field
Type
Required
Notes
id
BigAutoField
yes
Primary key
key
CharField
yes
Unique
value_json
JSONField
yes
Setting value
description
TextField
no
Admin help
is_active
BooleanField
yes
Active
created_at
DateTimeField
yes
Auto
updated_at
DateTimeField
yes
Auto
Example keys:
- job_stale_after_hours
- job_removed_after_hours
- quick_match_daily_limit
- llm_daily_limit_free_user
- recommendation_refresh_hours

Constraints:
- unique(key)
Indexes:
- key
- is_active
### 18. Full Relationship Map
User
  |-- CandidateProfile
  |     |-- ProfileSkill -> Skill
  |-- CVUpload
  |     |-- CVParsedData
  |-- MatchResult -> NormalizedJob
  |-- JobRecommendation -> NormalizedJob
  |-- SavedJob -> NormalizedJob
  |-- EmailPreference
  |-- EmailEvent
  |-- LLMUsageLog
  |-- ConsentRecord
  |-- DeletionRequest
  |-- UserEvent
JobSource
  |-- IngestionRun
  |-- RawJobRecord
  |     |-- NormalizedJob
  |           |-- NormalizedJobSkill -> Skill
  |-- NormalizedJob
Skill
  |-- SkillAlias
  |-- ProfileSkill
  |-- NormalizedJobSkill
  |-- UnmatchedSkillCandidate(mapped_skill)
PromptVersion
  |-- LLMCacheEntry
  |-- LLMUsageLog
EmailBatch
  |-- EmailEvent
### 19. Index Strategy Summary
19.1 Critical Indexes
User.email unique
CandidateProfile.user unique
CVUpload.user + is_active partial unique where deleted_at is null
RawJobRecord.source + source_job_id unique
NormalizedJob.source + source_job_id unique
NormalizedJob.public_id unique
NormalizedJob.search_vector GIN
Skill.slug unique
SkillAlias.normalized_alias unique
ProfileSkill.profile + skill unique
NormalizedJobSkill.job + skill + requirement_type unique
SavedJob.user + job unique
EmailEvent.idempotency_key unique
LLMCacheEntry.cache_key unique
19.2 Worker/Admin Indexes
IngestionRun.status + started_at
RawJobRecord.normalization_status
CVUpload.parse_status

UnmatchedSkillCandidate.status
LLMUsageLog.status + created_at
EmailEvent.status + created_at
DeletionRequest.status
### 20. JSON Field Strategy
Use JSONField for flexible nested data, snapshots, raw payloads, LLM output, warnings, and metadata. Use
relational tables for searched, filtered, joined, counted, and scored data.
Use JSONField For
Use Relational Tables For
RawJobRecord.raw_payload_json
User
IngestionRun.search_params_json
CandidateProfile
CVParsedData.deterministic_json / llm_json / merged_json
CVUpload
CVParsedData.confidence_json / warnings_json
NormalizedJob
MatchResult.profile_snapshot_json / job_snapshot_json
Skill and SkillAlias
MatchResult strong/missing/risk/profile/action JSON
ProfileSkill and NormalizedJobSkill
JobRecommendation strong/missing/risk/profile JSON
MatchResult and JobRecommendation
UserEvent.metadata_json
EmailEvent
### 21. Deletion and Privacy Behavior
21.1 Delete CV
### 1. Remove physical file.
### 2. Set CVUpload.deleted_at.
### 3. Set parse_status=deleted.
### 4. Delete or clear CVParsedData.
### 5. Remove ProfileSkill rows sourced only from that CV if not confirmed.
### 6. Mark related recommendations stale.
21.2 Replace CV
### 1. Existing active CV becomes inactive.
### 2. New CVUpload created as active.
### 3. Parse task queued.
### 4. Profile review required.
### 5. Recommendations refreshed after confirmation.
21.3 Delete Account
### 1. Create DeletionRequest.
### 2. Disable user login.
### 3. Delete CV files.
### 4. Delete CVParsedData.
### 5. Delete CVUpload rows or anonymize.
### 6. Delete CandidateProfile.
### 7. Delete ProfileSkill.
### 8. Delete SavedJob.
### 9. Delete MatchResult.
### 10. Delete JobRecommendation.
### 11. Delete EmailPreference.
### 12. Delete social accounts.
### 13. Remove/anonymize UserEvent personal metadata.
### 14. Delete or anonymize User.
### 15. Mark DeletionRequest completed.
MVP recommendation:
Hard-delete user-owned candidate data.
Keep anonymized operational logs only where useful.

### 22. Migration Order
Batch
Models
### 1. Foundation
accounts.User; core.SystemSetting optional
### 2. Skills
skills.Skill; skills.SkillAlias; skills.UnmatchedSkillCandidate
### 3. Profiles
profiles.CandidateProfile; profiles.ProfileSkill
### 4. Jobs
jobs.JobSource; jobs.IngestionRun; jobs.RawJobRecord; jobs.NormalizedJob;
jobs.NormalizedJobSkill
### 5. CVs
cvs.CVUpload; cvs.CVParsedData
### 6. Matching
matching.MatchResult; matching.QuickMatchSession
### 7. Recommendations
recommendations.JobRecommendation; RecommendationRun; SavedJob
### 8. LLM
llm.PromptVersion; LLMCacheEntry; LLMUsageLog
### 9. Notifications
notifications.EmailPreference; EmailBatch; EmailEvent; EmailUnsubscribeToken
### 10. Privacy and Analytics
privacy.ConsentRecord; DeletionRequest; analytics.UserEvent
### 23. Seed Data Requirements
23.1 Required Seed Data
- JobSource: france_travail
- Skill categories
- Initial 200-300 skills
- Initial aliases
- System settings
- Prompt versions
23.2 Initial System Settings
job_stale_after_hours = 24
job_removed_after_hours = 72
job_revalidate_after_hours = 6
recommendation_stale_after_hours = 24
active_user_days = 14
quick_match_expiry_hours = 24
max_cv_upload_size_mb = 5
max_quick_matches_per_ip_day = 10
max_llm_calls_per_user_day = 10
max_match_explanations_per_user_day = 5
23.3 Initial Prompt Versions
cv_extraction:v1
job_skill_extraction:v1
match_explanation:v1
cv_advice:v1
### 24. MVP Tables List
accounts_user
profiles_candidateprofile
profiles_profileskill
cvs_cvupload
cvs_cvparseddata
jobs_jobsource
jobs_ingestionrun
jobs_rawjobrecord
jobs_normalizedjob

jobs_normalizedjobskill
skills_skill
skills_skillalias
skills_unmatchedskillcandidate
matching_matchresult
matching_quickmatchsession
recommendations_jobrecommendation
recommendations_recommendationrun
recommendations_savedjob
notifications_emailpreference
notifications_emailbatch
notifications_emailevent
notifications_emailunsubscribetoken
llm_promptversion
llm_llmcacheentry
llm_llmusagelog
privacy_consentrecord
privacy_deletionrequest
analytics_userevent
Optional but recommended:
core_systemsetting
### 25. Implementation Safety Notes
25.1 Soft-deleted CVs
CVUpload must use a default manager that excludes deleted_at records.
A secondary all_objects manager is required for admin/privacy/deletion operations.
Normal app code uses CVUpload.objects.
Deletion/privacy/admin code uses CVUpload.all_objects.
Do not soft-delete everything. Use soft delete only where it has value.
25.2 Target roles
CandidateProfile.target_roles remains JSONField for MVP.
This is acceptable because recommendation workers usually load one user profile and compare in memory.
If role matching or analytics become slow, migrate later to:
- TargetRole
- CandidateProfileTargetRole
25.3 Public IDs
All public-facing models must use UUID public_id with:
- default=uuid.uuid4
- unique=True
- editable=False
- db_index=True
Public routes must use public_id, never internal pk.
### 26. Schema Risks
Too Many JSON Fields
Mitigation: Use relational tables for skills, job skills, profile skills, recommendations, match scores, and email
events. Use JSON only for snapshots, raw payloads, LLM output, warnings, and metadata.
Skill Taxonomy Pollution

Mitigation: Admin review for unmatched skills. Unique normalized aliases. Never auto-create Skill records
directly from LLM output.
Recommendation Staleness
Mitigation: Mark recommendations stale after profile/CV update. Store recommendation_version and
computed_at. Refresh via Celery.
Privacy Deletion Complexity
Mitigation: Central DeletionRequest worker. Clear deletion order. Private CV storage. No public CV URLs.
Search Vector Maintenance
Mitigation: Update search_vector during normalization/save. Rebuild after skill extraction updates. Add
management command to rebuild search index.
### 27. Database Schema Acceptance Criteria
- User/auth data model is clear.
- Candidate profile model is clear.
- CV upload and parsing model is clear.
- Raw and normalized job models are clear.
- France Travail source support is clear.
- Skill taxonomy and aliases are defined.
- Unknown skill review is supported.
- PostgreSQL full-text search is supported.
- Match result storage is defined.
- Recommendation storage is defined.
- Email digest idempotency is defined.
- LLM cache and usage logging are defined.
- Consent and deletion flows are supported.
- Product event logging is supported.
- Indexes and constraints are defined.
- Migration order is clear.
- Soft-delete manager requirements are documented.
- Public UUID routing is documented.
### 28. Final Schema Decision
Build the database as a normalized Django/PostgreSQL schema with controlled JSON usage.
Users and profiles are relational.
Jobs are raw + normalized.
Skills are canonical relational entities.
Matching results are stored with score breakdowns.
Recommendations are precomputed and stored.
LLM output is cached and logged.
Privacy deletion is first-class.
Search uses PostgreSQL full-text search.
Public URLs use UUID public_id, not internal integer IDs.
Soft-deleted CV records are hidden by default manager.
Next document after validation: Service Contracts v1.