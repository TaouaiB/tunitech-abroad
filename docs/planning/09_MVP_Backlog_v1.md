# TuniTech Abroad - MVP Backlog v1

<!-- Converted to Markdown for repository/agent context. The original generated PDF/DOCX remains the formatted source-of-truth document. -->


TuniTech Abroad
MVP Backlog v1
Implementation ticket backlog - PDF version
Generated for Baha Edine Taouai - June 2026
### 1. Document Purpose
This document converts the Implementation Roadmap v1 into implementation tickets. Each ticket includes ticket ID,
phase, priority, type, description, dependencies, acceptance criteria, and test expectations.
It comes before Repository Setup Plan v1 and the First Coding Phase.
### 2. Priority System
P0 = mandatory for MVP core
P1 = important, but can be delayed if needed
P2 = useful polish or post-MVP candidate
### 3. Ticket Type System
setup | backend | frontend | service | model | task | admin | test | security | privacy |
integration | llm | email | deployment
### 4. Backlog Overview
Phase
Name
Tickets
0
Repository and Local Environment
5
1
Django Foundation and Authentication
5
2
Core Models and Admin
6
3
Skill Taxonomy
6
4
Job Ingestion and Normalization
8
5
Public Job Search and Pages
5
6
CV Upload, Parsing, Profile Completion
8
7
Matching and Quick Match
6
8
Recommendations and Saved Jobs
6
9
OpenRouter LLM Support
6
10
Email Notifications
4
11
Privacy Deletion
4
12
Admin and Observability
3
13
MVP Polish
3
14
Deployment
4

Phase 0 - Repository and Local Environment
TTA-0001 - Create project repository
Phase
0
Priority
P0
Type
setup
Description
Create the Git repository for TuniTech Abroad.
Dependencies
None
Acceptance Criteria
- Repository exists
- README.md exists
- .gitignore exists
- Initial commit created
Test Expectations
- Repository can be cloned
- No secrets committed
TTA-0002 - Create Django project skeleton
Phase
0
Priority
P0
Type
setup
Description
Create Django project structure with config/ and apps/.
Dependencies
TTA-0001
Acceptance Criteria
- Django project starts
- config/settings package exists
- apps package exists
- manage.py exists
Test Expectations
- python manage.py check passes

TTA-0003 - Configure local PostgreSQL and Redis
Phase
0
Priority
P0
Type
setup
Description
Add Docker Compose for PostgreSQL and Redis.
Dependencies
TTA-0002
Acceptance Criteria
- docker-compose.yml exists
- PostgreSQL container starts
- Redis container starts
- Django connects to PostgreSQL
Test Expectations
- python manage.py migrate works
- Redis ping works
TTA-0004 - Configure Celery and Celery Beat
Phase
0
Priority
P0
Type
setup
Description
Set up Celery worker and Beat with Redis broker.
Dependencies
TTA-0003
Acceptance Criteria
- Celery app configured
- Worker starts
- Beat starts
- Test task can run
Test Expectations
- Simple debug task executes successfully

TTA-0005 - Add environment configuration
Phase
0
Priority
P0
Type
setup
Description
Create .env.example and settings split.
Dependencies
TTA-0002
Acceptance Criteria
- .env.example exists
- local settings exist
- production settings placeholder exists
- Secrets are read from environment
Test Expectations
- Project starts using .env values
- No secrets hardcoded
Phase 1 - Django Foundation and Authentication
TTA-0101 - Create custom User model
Phase
1
Priority
P0
Type
model
Description
Create custom User model before first migration lock-in.
Dependencies
TTA-0002
Acceptance Criteria
- Custom User model exists
- Email is unique
- AUTH_USER_MODEL configured
- Admin can manage users
Test Expectations
- User creation test passes
- Unique email test passes

TTA-0102 - Install and configure django-allauth
Phase
1
Priority
P0
Type
integration
Description
Add allauth for email/password, Google, and GitHub login.
Dependencies
TTA-0101
Acceptance Criteria
- Email/password login works
- Signup works
- Logout works
- Email verification enabled
- Google provider configured
- GitHub provider configured
Test Expectations
- Signup view loads
- Login view loads
- Logout works
- Verified email flow works locally
TTA-0103 - Implement AccountProvisioningService
Phase
1
Priority
P0
Type
service
Description
Create profile and email preferences after signup/login.
Dependencies
TTA-0101
Acceptance Criteria
- CandidateProfile created after signup
- EmailPreference created after signup
- Service is idempotent
Test Expectations
- Calling service twice does not create duplicate profile
- Calling service twice does not create duplicate preferences

TTA-0104 - Create base templates and homepage shell
Phase
1
Priority
P0
Type
frontend
Description
Create base layout, navbar, footer, homepage shell.
Dependencies
TTA-0002
Acceptance Criteria
- base.html exists
- home.html exists
- Navbar exists
- Footer exists
- Homepage loads
Test Expectations
- GET / returns 200
TTA-0105 - Create dashboard access guard
Phase
1
Priority
P0
Type
backend
Description
Create authenticated dashboard placeholder.
Dependencies
TTA-0102
Acceptance Criteria
- /dashboard/ exists
- Anonymous users redirected to login
- Authenticated users can access
Test Expectations
- Anonymous dashboard request redirects
- Authenticated dashboard request returns 200
Phase 2 - Core Models and Admin

TTA-0201 - Create CandidateProfile model
Phase
2
Priority
P0
Type
model
Description
Create main user profile model.
Dependencies
TTA-0101
Acceptance Criteria
- CandidateProfile model exists
- One profile per user
- Profile fields match Database Schema v1
- Admin registration exists
Test Expectations
- Profile created for user
- Unique user/profile constraint enforced
TTA-0202 - Create EmailPreference model
Phase
2
Priority
P0
Type
model
Description
Store user email preferences.
Dependencies
TTA-0101
Acceptance Criteria
- EmailPreference model exists
- One preference row per user
- Default weekly digest disabled
Test Expectations
- Preference created
- Unique user constraint works

TTA-0203 - Create SystemSetting model and service
Phase
2
Priority
P1
Type
model/service
Description
Create configurable settings for limits and thresholds.
Dependencies
TTA-0002
Acceptance Criteria
- SystemSetting model exists
- SystemSettingService.get() works
- Fallback default works
Test Expectations
- Existing setting returns value
- Missing setting returns default
TTA-0204 - Create ConsentRecord model and ConsentService
Phase
2
Priority
P0
Type
privacy
Description
Track user consent for CV processing, email digest, terms, and privacy policy.
Dependencies
TTA-0101
Acceptance Criteria
- ConsentRecord model exists
- ConsentService.record() works
- Consent includes type, version, text, timestamp
Test Expectations
- Consent can be recorded
- Multiple consent versions can exist

TTA-0205 - Create UserEvent model and service
Phase
2
Priority
P1
Type
analytics
Description
Record lightweight product events.
Dependencies
TTA-0101
Acceptance Criteria
- UserEvent model exists
- UserEventService.record() works
- Anonymous session hash supported
Test Expectations
- Authenticated event can be recorded
- Anonymous event can be recorded
- Analytics failure does not break user flow
TTA-0206 - Register core models in Django Admin
Phase
2
Priority
P0
Type
admin
Description
Register User, CandidateProfile, EmailPreference, ConsentRecord, UserEvent, and SystemSetting.
Dependencies
TTA-0201, TTA-0202, TTA-0203, TTA-0204, TTA-0205
Acceptance Criteria
- Admin pages load
- List display is useful
- Search fields configured
- Filters configured where useful
Test Expectations
- Staff can access admin
- Non-staff cannot access admin
Phase 3 - Skill Taxonomy

TTA-0301 - Create Skill model
Phase
3
Priority
P0
Type
model
Description
Create canonical skill model.
Dependencies
TTA-0206
Acceptance Criteria
- Skill model exists
- canonical_name unique
- slug unique
- category choices exist
- is_active field exists
Test Expectations
- Duplicate slug rejected
- Inactive skill can remain in database
TTA-0302 - Create SkillAlias model
Phase
3
Priority
P0
Type
model
Description
Create alias mapping for raw skill text to canonical Skill.
Dependencies
TTA-0301
Acceptance Criteria
- SkillAlias model exists
- normalized_alias unique
- Alias links to Skill
Test Expectations
- ReactJS maps to React if alias exists
- Duplicate normalized alias rejected

TTA-0303 - Create UnmatchedSkillCandidate model
Phase
3
Priority
P0
Type
model
Description
Store unknown skills for admin review.
Dependencies
TTA-0301
Acceptance Criteria
- Model exists
- status choices exist: pending, mapped, ignored
- occurrence_count exists
- mapped_skill nullable
Test Expectations
- Unknown candidate can be created
- Occurrence count can increment
TTA-0304 - Implement SkillNormalizerService
Phase
3
Priority
P0
Type
service
Description
Normalize raw skill strings into canonical Skill records.
Dependencies
TTA-0301, TTA-0302, TTA-0303
Acceptance Criteria
- Exact alias lookup works
- Text normalization works
- Unknown skill creates/updates UnmatchedSkillCandidate
- Service does not auto-create Skill
Test Expectations
- ReactJS normalizes to React
- Postgres normalizes to PostgreSQL
- Unknown skill creates pending candidate
- Repeated unknown skill increments count

TTA-0305 - Implement initial skill seed command
Phase
3
Priority
P0
Type
backend
Description
Seed 200-300 canonical skills and initial aliases.
Dependencies
TTA-0304
Acceptance Criteria
- Management command exists
- Seed is idempotent
- Core IT skill categories populated
Test Expectations
- Running seed twice does not duplicate records
TTA-0306 - Add admin skill review actions
Phase
3
Priority
P1
Type
admin
Description
Allow admin to map or ignore unmatched skill candidates.
Dependencies
TTA-0303, TTA-0304
Acceptance Criteria
- Admin can map candidate to existing Skill
- Admin can ignore candidate
- reviewed_by and reviewed_at set
Test Expectations
- Only staff can review
- Mapped candidate status changes to mapped
- Ignored candidate status changes to ignored
Phase 4 - Job Ingestion and Normalization

TTA-0401 - Create JobSource and IngestionRun models
Phase
4
Priority
P0
Type
model
Description
Store external job source and ingestion run history.
Dependencies
TTA-0206
Acceptance Criteria
- JobSource model exists
- IngestionRun model exists
- france_travail source can be created
- Run status and counts are stored
Test Expectations
- JobSource slug unique
- IngestionRun links to source
TTA-0402 - Create RawJobRecord model
Phase
4
Priority
P0
Type
model
Description
Store raw external job payloads.
Dependencies
TTA-0401
Acceptance Criteria
- RawJobRecord model exists
- raw_payload_json exists
- payload_hash exists
- unique(source, source_job_id) enforced
Test Expectations
- Duplicate source/source_job_id rejected
- Payload hash stored

TTA-0403 - Create NormalizedJob and NormalizedJobSkill models
Phase
4
Priority
P0
Type
model
Description
Store clean searchable jobs and their canonical skills.
Dependencies
TTA-0402, TTA-0301
Acceptance Criteria
- NormalizedJob model exists
- public_id UUID exists
- search_vector exists
- NormalizedJobSkill model exists
- Job skill uniqueness enforced
Test Expectations
- Job has UUID public_id
- Public ID is unique
- Job skill duplicates prevented
TTA-0404 - Implement JobFixtureIngestionService
Phase
4
Priority
P0
Type
service
Description
Load sample France Travail-like payloads for development.
Dependencies
TTA-0402
Acceptance Criteria
- Fixture file can create RawJobRecord
- Payload hash calculated
- Existing records updated, not duplicated
Test Expectations
- Fixture ingestion creates raw records
- Running fixture twice does not duplicate records
- Changed fixture updates payload hash

TTA-0405 - Implement JobClassificationService
Phase
4
Priority
P0
Type
service
Description
Classify job type, remote type, experience level, and language requirements.
Dependencies
TTA-0403
Acceptance Criteria
- stage/PFE detected as internship
- alternance/apprentissage detected as apprenticeship
- CDI/CDD detected where possible
- remote/hybrid/on-site detected
- French/English requirements extracted
Test Expectations
- Classification tests for stage, PFE, alternance, CDI, remote, hybrid
TTA-0406 - Implement JobNormalizationService
Phase
4
Priority
P0
Type
service
Description
Normalize RawJobRecord into NormalizedJob.
Dependencies
TTA-0403, TTA-0405
Acceptance Criteria
- Raw payload maps to NormalizedJob
- Missing fields do not crash
- Raw normalization_status updated
- search_vector populated
Test Expectations
- Valid raw job normalizes successfully
- Missing company/location handled
- Failed normalization stores error

TTA-0407 - Implement JobFreshnessService
Phase
4
Priority
P0
Type
service
Description
Mark jobs active, stale, expired, removed.
Dependencies
TTA-0403, TTA-0203
Acceptance Criteria
- Expired jobs marked expired
- Old unseen jobs marked stale/removed
- Active jobs remain active
Test Expectations
- expires_at past marks expired
- last_seen_at older than threshold marks stale
- last_seen_at older than removed threshold marks removed
TTA-0408 - Add ingestion Celery tasks
Phase
4
Priority
P0
Type
task
Description
Create tasks for ingestion and normalization.
Dependencies
TTA-0404, TTA-0406, TTA-0407
Acceptance Criteria
- normalize_raw_job_record task exists
- mark_stale_and_expired_jobs task exists
- Tasks call services only
Test Expectations
- Task executes normalization service
- Task handles missing record safely
Phase 5 - Public Job Search and Pages

TTA-0501 - Implement JobSearchService
Phase
5
Priority
P0
Type
service
Description
Search local PostgreSQL jobs using full-text search.
Dependencies
TTA-0403
Acceptance Criteria
- Search uses local database
- Only active jobs shown by default
- Filters supported
- Pagination supported
Test Expectations
- Search returns matching jobs
- Expired jobs hidden by default
- Filters work
- Pagination works
TTA-0502 - Implement JobQueryService
Phase
5
Priority
P0
Type
service
Description
Retrieve public jobs by UUID public_id.
Dependencies
TTA-0403
Acceptance Criteria
- get_public_job(public_id) works
- Internal integer ID not used in public view
- Not found handled safely
Test Expectations
- Existing public_id returns job
- Unknown public_id raises not found

TTA-0503 - Build public job search page
Phase
5
Priority
P0
Type
frontend
Description
Create /jobs/ page.
Dependencies
TTA-0501
Acceptance Criteria
- GET /jobs/ returns 200
- Search form visible
- Job cards visible
- Pagination visible
Test Expectations
- Anonymous user can access
- Search query returns filtered result
TTA-0504 - Build job detail page
Phase
5
Priority
P0
Type
frontend
Description
Create /jobs/<uuid:public_id>/ page.
Dependencies
TTA-0502
Acceptance Criteria
- Job detail loads by UUID
- Job title, company, location, description visible
- Skills visible
- Stale/expired label visible when relevant
Test Expectations
- Valid job returns 200
- Unknown job returns 404
- Internal ID route does not exist

TTA-0505 - Implement JobRevalidationService shell
Phase
5
Priority
P1
Type
service
Description
Create safe service shell for high-intent job refresh.
Dependencies
TTA-0502
Acceptance Criteria
- Service exists
- Checks last_fetched_at threshold
- If external client not configured, safely returns existing job
Test Expectations
- Old job triggers revalidation path
- External failure does not break job detail
Phase 6 - CV Upload, Parsing, Profile Completion
TTA-0601 - Create CVUpload and CVParsedData models
Phase
6
Priority
P0
Type
model
Description
Create CV metadata and parsed data models.
Dependencies
TTA-0201
Acceptance Criteria
- CVUpload model exists
- CVParsedData model exists
- public_id UUID exists
- CVUpload.objects excludes deleted CVs
- CVUpload.all_objects includes all CVs
- One active CV constraint exists
Test Expectations
- Deleted CV excluded by default manager
- all_objects returns deleted CV
- Only one active CV allowed

TTA-0602 - Implement CVUploadService
Phase
6
Priority
P0
Type
service
Description
Validate and store CV uploads.
Dependencies
TTA-0601, TTA-0204
Acceptance Criteria
- PDF accepted
- Non-PDF rejected
- File size limit enforced
- Consent required
- Previous active CV deactivated
- parse_cv task enqueued
Test Expectations
- Valid PDF creates CVUpload
- Invalid file rejected
- Missing consent rejected
- Old CV becomes inactive
TTA-0603 - Implement CVTextExtractionService
Phase
6
Priority
P0
Type
service
Description
Extract text from PDF using PyMuPDF or pdfplumber.
Dependencies
TTA-0601
Acceptance Criteria
- Text extraction works for text-based PDF
- Unreadable/scanned PDFs detected
- Text length stored
Test Expectations
- Sample PDF extracts text
- Empty/scanned-like PDF returns too_little_text

TTA-0604 - Implement CVDeterministicExtractorService
Phase
6
Priority
P0
Type
service
Description
Extract exact fields from CV text.
Dependencies
TTA-0603
Acceptance Criteria
- Email extracted
- Phone extracted where possible
- LinkedIn URL extracted
- GitHub URL extracted
- Portfolio/website URL extracted
Test Expectations
- Regex extracts known sample values
- No crash if fields missing
TTA-0605 - Implement CVParsingService
Phase
6
Priority
P0
Type
service
Description
Coordinate full CV parsing flow.
Dependencies
TTA-0602, TTA-0603, TTA-0604, TTA-0304
Acceptance Criteria
- parse_status moves pending -> processing -> parsed/failed
- CVParsedData created
- ProfileSkill rows created
- CandidateProfile draft fields updated where empty
- Profile completeness recalculated
Test Expectations
- Parse task creates CVParsedData
- Extracted skill maps to ProfileSkill
- Unreadable CV marks failed
- Deleted CV parsing aborts

TTA-0606 - Build CV management page
Phase
6
Priority
P0
Type
frontend
Description
Create /dashboard/cv/.
Dependencies
TTA-0602, TTA-0605
Acceptance Criteria
- User can upload CV
- Consent checkbox visible
- Parse status visible
- Delete CV button visible
- Replace CV supported
Test Expectations
- Anonymous user redirected
- Authenticated user can upload
- Only owner can view own CV
TTA-0607 - Build profile edit page
Phase
6
Priority
P0
Type
frontend
Description
Create /dashboard/profile/.
Dependencies
TTA-0201, TTA-0304
Acceptance Criteria
- User can edit profile fields
- User can edit skills
- Completeness updates
- Recommendations marked stale after meaningful changes
Test Expectations
- Profile update persists
- Invalid URLs rejected
- Profile completeness updates

TTA-0608 - Implement CVDeletionService
Phase
6
Priority
P0
Type
privacy
Description
Safely delete CV data and file.
Dependencies
TTA-0601
Acceptance Criteria
- Physical file deleted
- CVUpload soft-deleted
- CVParsedData deleted or cleared
- Unconfirmed CV-only ProfileSkill rows removed
- Recommendations marked stale
Test Expectations
- Deleted CV is not used in matching
- Deleted CV not returned by CVUpload.objects
- File no longer exists
Phase 7 - Matching and Quick Match
TTA-0701 - Create MatchResult and QuickMatchSession models
Phase
7
Priority
P0
Type
model
Description
Store full match results and anonymous quick match sessions.
Dependencies
TTA-0403, TTA-0601
Acceptance Criteria
- MatchResult model exists
- QuickMatchSession model exists
- public_id UUIDs exist
- Snapshots stored in JSON fields
Test Expectations
- MatchResult links user/profile/job
- QuickMatchSession expires_at exists

TTA-0702 - Implement MatchScoringService
Phase
7
Priority
P0
Type
service
Description
Build deterministic scoring engine.
Dependencies
TTA-0304, TTA-0403, TTA-0607
Acceptance Criteria
- Fit score formula implemented
- Technical skill score implemented
- Experience score implemented
- Role/title score implemented
- Language score implemented
- Location score implemented
- Risk flags returned
- Profile signals returned
Test Expectations
- Score always 0-100
- Required skill missing reduces technical score
- Profile signals do not reduce score
- French missing flag works
TTA-0703 - Implement MatchResultService
Phase
7
Priority
P0
Type
service
Description
Create stored match result from user and job.
Dependencies
TTA-0701, TTA-0702
Acceptance Criteria
- Service validates profile
- Service loads active CV if available
- Service stores score breakdown
- Service stores profile and job snapshots
Test Expectations
- Usable profile can create match
- Incomplete profile blocked or warned
- MatchResult created

TTA-0704 - Implement QuickMatchService
Phase
7
Priority
P0
Type
service
Description
Anonymous teaser match from manually entered skills.
Dependencies
TTA-0701, TTA-0304, TTA-0403
Acceptance Criteria
- No login required
- No CV required
- No LLM used
- Rate limit supported
- QuickMatchSession stored
Test Expectations
- Anonymous quick match returns score
- Unknown skill goes to UnmatchedSkillCandidate
- Rate limit works
TTA-0705 - Build match endpoints and pages
Phase
7
Priority
P0
Type
frontend
Description
Create full match and match detail UI.
Dependencies
TTA-0703
Acceptance Criteria
- /jobs/<uuid>/match/ creates match
- Redirects to match detail
- Match detail shows score breakdown
- Only owner can view match
Test Expectations
- Anonymous full match redirects to login
- Owner can view match
- Other user cannot view match

TTA-0706 - Build quick match HTMX UI
Phase
7
Priority
P0
Type
frontend
Description
Add quick match form/result on job detail page.
Dependencies
TTA-0704, TTA-0504
Acceptance Criteria
- Quick match form visible to anonymous users
- HTMX result renders
- CTA to signup/CV upload visible
Test Expectations
- Valid quick match returns partial HTML
- Invalid input returns validation message
Phase 8 - Recommendations and Saved Jobs
TTA-0801 - Create recommendation models
Phase
8
Priority
P0
Type
model
Description
Create JobRecommendation, RecommendationRun, and SavedJob.
Dependencies
TTA-0701
Acceptance Criteria
- JobRecommendation exists
- RecommendationRun exists
- SavedJob exists
- unique user/job saved job constraint exists
Test Expectations
- Duplicate saved job rejected
- Recommendation links user/profile/job

TTA-0802 - Implement RecommendationService
Phase
8
Priority
P0
Type
service
Description
Generate stored recommendations using MatchScoringService.
Dependencies
TTA-0801, TTA-0702
Acceptance Criteria
- Creates RecommendationRun
- Prefilters jobs
- Scores candidate jobs
- Stores top recommendations
- Marks old recommendations stale
Test Expectations
- Recommendations generated for usable profile
- Incomplete profile skipped
- Running twice does not duplicate rows
TTA-0803 - Implement RecommendationQueryService
Phase
8
Priority
P0
Type
service
Description
Read dashboard recommendations and enqueue refresh when needed.
Dependencies
TTA-0802
Acceptance Criteria
- Fresh recommendations returned
- Stale recommendations returned with refresh enqueue
- No recommendations returns pending state
Test Expectations
- Fresh path works
- Stale path enqueues task
- Empty path enqueues task

TTA-0804 - Build recommendations dashboard page
Phase
8
Priority
P0
Type
frontend
Description
Create /dashboard/recommendations/.
Dependencies
TTA-0803
Acceptance Criteria
- User sees recommendations
- Score and missing skills visible
- Stale state visible
- Pending state visible
Test Expectations
- Authenticated user can access
- Anonymous user redirected
- Dashboard does not compute heavy matching synchronously
TTA-0805 - Implement SavedJobService and buttons
Phase
8
Priority
P0
Type
service/frontend
Description
Allow users to save and unsave jobs.
Dependencies
TTA-0801, TTA-0504
Acceptance Criteria
- Save job works
- Unsave job works
- HTMX button updates
- Saving is idempotent
Test Expectations
- Authenticated user can save
- Anonymous user redirected
- Duplicate save returns existing saved job

TTA-0806 - Build saved jobs page
Phase
8
Priority
P1
Type
frontend
Description
Create /dashboard/saved-jobs/.
Dependencies
TTA-0805
Acceptance Criteria
- Saved jobs listed
- Stale/expired labels shown
- User can remove saved jobs
Test Expectations
- Only current user saved jobs shown
Phase 9 - OpenRouter LLM Support
TTA-0901 - Create LLM models
Phase
9
Priority
P0
Type
model
Description
Create PromptVersion, LLMCacheEntry, and LLMUsageLog.
Dependencies
TTA-0206
Acceptance Criteria
- PromptVersion exists
- LLMCacheEntry exists
- LLMUsageLog exists
- cache_key unique
Test Expectations
- Prompt version can be stored
- Cache entry can be retrieved by key
- Usage log can be created

TTA-0902 - Implement OpenRouterClient
Phase
9
Priority
P0
Type
llm
Description
Low-level OpenRouter API client.
Dependencies
TTA-0901
Acceptance Criteria
- Client reads API key from env
- Timeout configured
- Errors normalized
- No key logged
Test Expectations
- Mocked API success works
- Mocked API error raises LLMServiceError
TTA-0903 - Implement PromptRunnerService
Phase
9
Priority
P0
Type
llm
Description
Run versioned prompts with cache and usage logging.
Dependencies
TTA-0901, TTA-0902
Acceptance Criteria
- Active prompt resolved
- Cache hit avoids API call
- Cache miss calls client
- Usage log recorded
Test Expectations
- Cache hit test
- Cache miss test
- Failed call logs failure

TTA-0904 - Implement LLM rate limits and output validation
Phase
9
Priority
P0
Type
llm/security
Description
Prevent uncontrolled OpenRouter usage and validate outputs.
Dependencies
TTA-0903
Acceptance Criteria
- Daily user limit enforced
- Match explanation limit enforced
- CV extraction JSON validated
- Unsafe explanation content blocked or sanitized
Test Expectations
- Rate limit blocks after threshold
- Invalid JSON rejected
- Explanation cannot alter fit score
TTA-0905 - Enable CV LLM extraction
Phase
9
Priority
P1
Type
llm
Description
Use OpenRouter for structured CV extraction.
Dependencies
TTA-0605, TTA-0903, TTA-0904
Acceptance Criteria
- CV extraction prompt exists
- LLM output stored in CVParsedData.llm_json
- Failure marks parsed_with_warnings if deterministic data exists
Test Expectations
- Mocked LLM response creates structured data
- LLM failure does not delete CV

TTA-0906 - Enable match explanation
Phase
9
Priority
P1
Type
llm/frontend
Description
Generate optional AI explanation for MatchResult.
Dependencies
TTA-0705, TTA-0903, TTA-0904
Acceptance Criteria
- Explanation endpoint exists
- Uses structured score payload only
- Updates MatchResult explanation fields
- HTMX partial updates page
Test Expectations
- Owner can generate explanation
- Non-owner blocked
- Cache reused
- Score unchanged
Phase 10 - Email Notifications
TTA-1001 - Create email models
Phase
10
Priority
P0
Type
model
Description
Create EmailBatch, EmailEvent, EmailUnsubscribeToken.
Dependencies
TTA-0202
Acceptance Criteria
- EmailEvent.idempotency_key unique
- EmailBatch tracks status
- Unsubscribe token hash stored
Test Expectations
- Duplicate idempotency key rejected

TTA-1002 - Implement EmailSenderService
Phase
10
Priority
P0
Type
email
Description
Abstract email provider and idempotent sending.
Dependencies
TTA-1001
Acceptance Criteria
- Creates queued EmailEvent
- Sends through provider abstraction
- Updates sent/failed status
- Duplicate idempotency key returns existing event
Test Expectations
- Mock provider success
- Mock provider failure
- Idempotency prevents duplicate send
TTA-1003 - Implement EmailPreferenceService
Phase
10
Priority
P0
Type
email
Description
Update email preferences and unsubscribe.
Dependencies
TTA-0202, TTA-1001
Acceptance Criteria
- User can enable/disable weekly digest
- Unsubscribe token disables relevant preference
- Consent recorded when digest enabled
Test Expectations
- Preference update works
- Invalid unsubscribe token safe
- Valid token disables digest

TTA-1004 - Implement WeeklyDigestService
Phase
10
Priority
P1
Type
email
Description
Send weekly recommendation digest to eligible users.
Dependencies
TTA-0804, TTA-1002, TTA-1003
Acceptance Criteria
- Only opted-in users included
- Only verified emails included
- Only active users included
- Idempotency key used per user/week
Test Expectations
- Unverified user excluded
- Opted-out user excluded
- Duplicate digest not sent
Phase 11 - Privacy Deletion
TTA-1101 - Build privacy and terms pages
Phase
11
Priority
P0
Type
privacy/frontend
Description
Create /privacy/ and /terms/.
Dependencies
TTA-0104
Acceptance Criteria
- Privacy page exists
- Terms page exists
- No employment guarantee stated
- No visa/legal advice stated
- CV processing explained
Test Expectations
- GET /privacy/ returns 200
- GET /terms/ returns 200

TTA-1102 - Create DeletionRequest model
Phase
11
Priority
P0
Type
model/privacy
Description
Track account deletion requests.
Dependencies
TTA-0101
Acceptance Criteria
- DeletionRequest model exists
- status choices exist
- processed_at and error_message exist
Test Expectations
- Deletion request can be created
- Status can move pending -> processing -> completed
TTA-1103 - Implement AccountDeletionService
Phase
11
Priority
P0
Type
privacy
Description
Delete/anonymize user-owned data.
Dependencies
TTA-1102, TTA-0608, TTA-0801, TTA-0701
Acceptance Criteria
- User login disabled
- CV files deleted
- Profile deleted
- Saved jobs deleted
- Matches deleted
- Recommendations deleted
- Events anonymized or deleted
- DeletionRequest completed
Test Expectations
- Account deletion removes private candidate data
- Failed deletion marks request failed
- Retry possible

TTA-1104 - Build delete account page
Phase
11
Priority
P0
Type
privacy/frontend
Description
Create delete account UI.
Dependencies
TTA-1103
Acceptance Criteria
- User must confirm deletion
- DeletionRequest created
- Deletion task enqueued
Test Expectations
- Anonymous user redirected
- Authenticated user can request deletion
Phase 12 - Admin and Observability
TTA-1201 - Harden Django Admin registrations
Phase
12
Priority
P0
Type
admin
Description
Add list displays, filters, search, readonly fields.
Dependencies
All core models
Acceptance Criteria
- Admin usable for jobs
- Admin usable for users/profiles
- Admin usable for CVs
- Admin usable for LLM/email logs
Test Expectations
- Admin pages return 200 for staff

TTA-1202 - Add admin reprocessing actions
Phase
12
Priority
P1
Type
admin
Description
Add admin actions that call services.
Dependencies
TTA-1201
Acceptance Criteria
- Re-normalize raw jobs action
- Re-extract job skills action
- Refresh recommendations action
- Re-parse CV action
- Map unmatched skills action
Test Expectations
- Admin actions call service layer
- Non-staff cannot call actions
TTA-1203 - Implement health endpoint
Phase
12
Priority
P0
Type
backend
Description
Create /health/.
Dependencies
TTA-0003
Acceptance Criteria
- Checks database
- Checks Redis
- Returns JSON
- Does not expose secrets
Test Expectations
- Healthy system returns ok
- Redis failure returns degraded
Phase 13 - MVP Polish

TTA-1301 - Add empty, loading, and error states
Phase
13
Priority
P1
Type
frontend
Description
Improve UX for no jobs, no CV, parsing pending, no recommendations.
Dependencies
Core pages complete
Acceptance Criteria
- No blank pages
- Clear CTAs
- Useful error messages
Test Expectations
- Pages render correctly with empty database
TTA-1302 - Add production security settings
Phase
13
Priority
P0
Type
security
Description
Configure production security baseline.
Dependencies
TTA-0005
Acceptance Criteria
- DEBUG false in production
- Allowed hosts configured
- CSRF secure settings configured
- Session cookie secure configured
- Secrets from env only
Test Expectations
- Production settings check passes
- No secrets committed

TTA-1303 - Verify private media protection
Phase
13
Priority
P0
Type
security/privacy
Description
Ensure CV files are not publicly accessible.
Dependencies
TTA-0602
Acceptance Criteria
- CV files stored privately
- No direct public URL exposes CV
- Only owner/admin service can access
Test Expectations
- Anonymous user cannot access CV file
- Other authenticated user cannot access CV file
Phase 14 - Deployment
TTA-1401 - Prepare deployment environment
Phase
14
Priority
P0
Type
deployment
Description
Prepare production web, worker, beat, PostgreSQL, Redis.
Dependencies
Phase 13 complete
Acceptance Criteria
- Production env variables configured
- Database provisioned
- Redis provisioned
- Web service configured
- Worker service configured
- Beat service configured
Test Expectations
- Production health endpoint works
- Worker receives task
- Beat schedules task

TTA-1402 - Configure OAuth and email provider in production
Phase
14
Priority
P0
Type
deployment/integration
Description
Configure Google/GitHub OAuth and email provider.
Dependencies
TTA-1401
Acceptance Criteria
- Google OAuth redirect URL configured
- GitHub OAuth redirect URL configured
- Email provider env vars configured
- Verification email sends
Test Expectations
- Google login works
- GitHub login works
- Email verification works
TTA-1403 - Run production seed and initial ingestion
Phase
14
Priority
P0
Type
deployment
Description
Seed skills, system settings, source, and initial jobs.
Dependencies
TTA-1401, TTA-0305, TTA-0404
Acceptance Criteria
- Skills seeded
- System settings seeded
- France Travail source exists
- Initial jobs ingested
- Admin account exists
Test Expectations
- Admin can log in
- Job search returns results

TTA-1404 - Final MVP smoke test
Phase
14
Priority
P0
Type
test
Description
Run full manual MVP validation.
Dependencies
TTA-1401, TTA-1402, TTA-1403
Acceptance Criteria
- Signup works
- Login works
- Job search works
- CV upload works
- Profile edit works
- Quick match works
- Full match works
- Recommendations work
- Saved jobs work
- Delete CV works
- Delete account request works
Test Expectations
- No critical blocker remains

### 5. Critical MVP Cut Line
The minimum useful MVP is complete after Phase 0 through Phase 8.
Phase 0 -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 5 -> Phase 6 -> Phase 7 -> Phase 8
At that point, the product can demonstrate:
- job ingestion
- job search
- candidate profile
- CV upload
- skill extraction
- matching
- recommendations
- saved jobs
### 6. Backlog Acceptance Criteria
- Every roadmap phase has tickets.
- Each ticket has clear acceptance criteria.
- Each ticket has test expectations.
- Dependencies are visible.
- P0 tickets define the real MVP core.
- Deferred features are not mixed into MVP.
- The next document can define repository setup.
### 7. Next Document
After MVP Backlog v1, the next and last planning document before coding is Repository Setup Plan v1.
After Repository Setup Plan v1, the First Coding Phase begins.