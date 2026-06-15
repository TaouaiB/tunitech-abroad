# TuniTech Abroad - Technical Architecture v1

<!-- Converted to Markdown for repository/agent context. The original generated PDF/DOCX remains the formatted source-of-truth document. -->


France-first job intelligence platform for Tunisian IT candidates
Planning Document
June 12, 2026
Contents
1
Document Purpose
5
2
Product Summary
5
3
Locked Technical Decisions
6
4
High-Level Architecture
6
5
Runtime Components
7
5.1 Django Web Process . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
7
5.2 PostgreSQL . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
7
5.3 Redis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
8
5.4 Celery Workers . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
8
5.5 Celery Beat
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
8
6
Django Project Structure
8
7
Django Apps
9
7.1 core . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
9
7.2 accounts
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
9
7.3 profiles
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
10
7.4 cvs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
10
7.5 jobs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
10
7.6 skills . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
11
7.7 matching
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
11
7.8 recommendations
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
11
7.9 llm . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
11
7.10notifications
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
12
7.11privacy
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
12
7.12events . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
12
7.13dashboard . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
12
7.14admin_monitoring
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
13
8
Environment Configuration
13
9
Data Architecture Overview
14
9.1 User and Profile
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
14
9.1.1 User . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
14
9.1.2 CandidateProfile . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
14
9.2 CV Models
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
15
9.2.1 CVUpload
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
15
9.2.2 CVParsedData . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
15
1

TuniTech Abroad
Technical Architecture v1
9.3 Job Models . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
16
9.3.1 JobSource . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
16
9.3.2 IngestionRun
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
16
9.3.3 RawJobRecord . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
16
9.3.4 NormalizedJob . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
17
9.4 Skill Taxonomy Models . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
18
9.4.1 Skill . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
18
9.4.2 SkillAlias . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
18
9.4.3 UnmatchedSkillCandidate . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
19
9.5 Matching Models . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
19
9.5.1 MatchResult . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
19
9.5.2 QuickMatchSession . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
20
9.6 Recommendation Models
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
20
9.6.1 JobRecommendation
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
20
9.6.2 RecommendationRun . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
20
9.7 Email Models . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
21
9.7.1 EmailPreference . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
21
9.7.2 EmailBatch
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
21
9.7.3 EmailEvent
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
21
9.8 LLM Models
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
22
9.8.1 PromptVersion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
22
9.8.2 LLMCacheEntry
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
22
9.8.3 LLMUsageLog . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
22
9.9 Privacy Models . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
23
9.9.1 ConsentRecord
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
23
9.9.2 DeletionRequest
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
23
9.10Event Logging Model . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
23
9.10.1UserEvent . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
23
10France Travail Ingestion Architecture
24
10.1Principle
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
24
10.2France Travail Client . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
24
10.3Ingestion Query Strategy
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
24
10.4Ingestion Flow . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
25
10.5Deduplication
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
25
10.6Raw Payload Hash . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
25
10.7Job Freshness Logic
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
25
10.8High-Intent Revalidation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
26
11Job Normalization Architecture
26
11.1Normalizer . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
26
11.2Defensive Mapping Rule . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
26
11.3Job Type Detection . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
26
11.4Remote Type Detection
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
27
12PostgreSQL Full-Text Search Strategy
27
12.1MVP Search Decision . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
27
12.2Searchable Fields
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
27
12.3Search Vector
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
28
12.4Indexes for Search . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
28
13Skill Taxonomy Architecture
28
13.1MVP Strategy
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
28
13.2Taxonomy Structure
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
28
13.3ESCO Strategy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
29
13.4Skill Normalization Flow . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
29
13.5Initial Skill Seed
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
29
13.6Admin Unknown Skill Review
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
30
2

TuniTech Abroad
Technical Architecture v1
14CV Parsing Architecture
30
14.1Parsing Reality . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
30
14.2Upload Flow
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
30
14.3Parsing Worker . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
30
14.4OCR Policy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
31
14.5User Confirmation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
31
15CV LLM JSON Extraction Contract
31
15.1Purpose
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
31
15.2Schema Version
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
31
15.3JSON Contract
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
31
15.4Validation Rules
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
32
16Anonymous Quick Match Architecture
33
16.1Purpose
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
16.2Flow
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
16.3Data Handling . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
17Matching Engine Architecture
33
17.1Principle
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
17.2Fit Score Components
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
17.3Fit Score Formula
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
33
17.4Technical Skills Score
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
34
17.5Experience Score
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
34
17.6Role/Title Score
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
34
17.7Language Score
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
34
17.8Risk Flags vs Profile Signals
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
35
18Recommendation Engine Architecture
35
18.1Principle
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
35
18.2Triggers
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
35
18.3Active User Rule . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
35
18.4Recommendation Flow . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
36
18.5Prefiltering . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
36
18.6Ranking Score . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
36
18.7Dashboard Refresh Behavior . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
36
19LLM Architecture
36
19.1Provider
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
36
19.2Service Structure
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
37
19.3Allowed Use Cases . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
37
19.4Forbidden MVP Use Cases . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
37
19.5Caching
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
37
19.6Limits
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
37
19.7Failure Behavior
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
37
19.8Match Explanation Guardrails
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
38
20Authentication Architecture
38
20.1django-allauth . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
38
20.2Login Methods . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
38
20.3Account Collision Policy
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
38
20.4Profile Creation
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
39
21Email Architecture
39
21.1Email Provider . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
39
21.2Email Types
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
39
21.3Weekly Digest Flow
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
39
21.4Idempotency . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
40
3

TuniTech Abroad
Technical Architecture v1
21.5Unsubscribe
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
40
22Privacy and GDPR-Oriented Architecture
40
22.1Required Pages
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
40
22.2CV Upload Consent
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
40
22.3Delete CV
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
40
22.4Delete Account
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
40
22.5Admin CV Access
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
41
23UI Architecture
41
23.1Language
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
41
23.2Template Strategy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
41
23.3HTMX Use Cases . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
41
24Admin Architecture
41
24.1MVP Admin . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
41
24.2Admin Monitoring Needs . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
42
25Background Task Architecture
42
25.1Task List
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
42
25.2Scheduled Tasks . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
43
25.3Task Idempotency
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
43
26Health Check Architecture
43
27Security Architecture
44
27.1File Security
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
44
27.2Web Security . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
44
27.3Secrets . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
44
27.4Rate Limiting . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
44
28Logging and Monitoring
44
28.1What to Log
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
44
28.2Admin Visibility
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
45
28.3Product Events . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
45
29Testing Strategy
45
29.1Unit Tests
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
45
29.2Integration Tests . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
45
29.3Celery Task Tests . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
46
29.4View Tests
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
46
29.5Regression Fixtures
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
46
30Deployment Architecture
46
30.1MVP Deployment Shape . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
46
30.2Deployment Platforms . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
46
30.3Docker Compose Services . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
47
30.4Process Reliability
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
47
31Implementation Sequence
47
31.1Phase 1: Foundation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
47
31.2Phase 2: Jobs Foundation
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
47
31.3Phase 3: Skill Taxonomy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
48
31.4Phase 4: CV/Profile . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
48
31.5Phase 5: Matching . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
48
31.6Phase 6: Recommendations . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
48
31.7Phase 7: LLM Support
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
49
31.8Phase 8: Emails
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
49
31.9Phase 9: Privacy and Polish
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
49
4

TuniTech Abroad
Technical Architecture v1
32Technical Risks and Mitigations
49
32.1France Travail API Access
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
49
32.2Skill Matching Quality
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
49
32.3CV Parsing Quality . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
50
32.4LLM Cost . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
50
32.5Scope Creep . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
50
32.6Email Duplication
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
50
33Architecture Acceptance Criteria
51
34Final Architecture Decision
51
35Next Phase
51
36Reference Notes
52
1
Document Purpose
This document defines the technical architecture for TuniTech Abroad MVP.
It translates the validated BRD and PRD into an implementation-ready architecture. It is intentionally
practical: one developer, one modular Django monolith, one relational database, background workers,
deterministic matching, controlled LLM usage, and a path to production without overengineering.
This document defines:
• System architecture
• Django app/module structure
• Database model direction
• Background workers
• France Travail job ingestion
• Skill taxonomy
• CV parsing and LLM extraction contract
• Matching engine
• Recommendation engine
• Anonymous quick-match flow
• OpenRouter integration
• Authentication
• Email notifications
• Admin monitoring
• GDPR/privacy handling
• Logging, health checks, and event tracking
• Deployment direction
• Testing strategy
• Implementation sequence
This document is not the database schema. Database Schema v1 comes next.
2
Product Summary
Product name: TuniTech Abroad
MVP scope: A France-first job intelligence platform for Tunisian IT candidates, students, bootcamp
graduates, and internship seekers.
Core loop:
France IT jobs
-> CV/profile
5

TuniTech Abroad
Technical Architecture v1
-> matching
-> recommendations
-> missing skills
-> better application targeting
3
Locked Technical Decisions
Area
Decision
Backend framework
Django
Frontend approach
Django templates + HTMX + Tailwind CSS
Database
PostgreSQL
ORM
Django ORM
Background jobs
Celery + Redis
Auth
django-allauth
Social login
Google + GitHub
Email/password signup
Yes
Job source
France Travail API Offres d’emploi
Future job source
La Bonne Alternance API
Search MVP
PostgreSQL Full-Text Search
LLM provider
OpenRouter
LLM usage
Controlled, cached, not final scoring authority
Final match score
Rule-based deterministic fit score
UI language
French first
Admin
Django Admin first
File storage MVP
Private local storage; S3-compatible later
OCR
Deferred; text-based PDF first
Architecture style
Modular Django monolith
4
High-Level Architecture
Browser
|
| HTTP
v
Django Web App
|
|-- Public pages
|-- Dashboard pages
|-- Authentication
|-- CV upload
|-- Job search
|-- Match result pages
|-- Admin
|
+--> PostgreSQL
|
+--> Redis
|
v
Celery Workers
|
|-- Job ingestion worker
|-- Job normalization worker
6

TuniTech Abroad
Technical Architecture v1
|-- Skill extraction worker
|-- CV parsing worker
|-- Matching worker
|-- Recommendation worker
|-- Email worker
|-- LLM worker
|-- Cleanup/privacy worker
|
+--> France Travail API
+--> OpenRouter API
+--> Email provider
5
Runtime Components
5.1
Django Web Process
Responsible for:
• Serving public pages
• Serving authenticated dashboard
• Handling authentication
• Handling CV upload
• Running lightweight synchronous actions
• Reading search results from PostgreSQL
• Displaying match/recommendation results
• Managing user preferences
• Serving Django Admin
• Serving /health/
Should not perform:
• Bulk job ingestion
• Heavy CV parsing
• Bulk recommendation refresh
• Bulk LLM processing
• Email batch sending
Those belong to Celery workers.
5.2
PostgreSQL
PostgreSQL is the permanent source of truth.
Stores:
• Users
• Profiles
• CV metadata and parsed CV data
• Raw job source records
• Normalized jobs
• Skills and aliases
• Match results
• Recommendations
• Saved jobs
• Email preferences and email events
• LLM usage logs and cache entries
• Ingestion runs
• Privacy consent/deletion records
• Product event logs
7

TuniTech Abroad
Technical Architecture v1
5.3
Redis
Used for:
• Celery broker
• Celery result backend, optional
• Short-lived cache
• Rate-limit counters
• Job locks
• Duplicate task prevention
Redis is not the permanent data store.
5.4
Celery Workers
Recommended queues:
default
ingestion
parsing
matching
recommendations
llm
emails
maintenance
For MVP, one worker process may consume all queues. The queue names still preserve clean bound-
aries.
5.5
Celery Beat
Scheduled tasks:
job_ingestion_sync
job_expiry_check
recommendation_nightly_refresh
weekly_digest_generation
cleanup_expired_temp_files
cleanup_expired_quick_matches
privacy_deletion_sweep
6
Django Project Structure
Recommended repository structure:
tunitech-abroad/
README.md
.env.example
.gitignore
docker-compose.yml
Dockerfile
requirements/
base.txt
local.txt
production.txt
manage.py
config/
8

TuniTech Abroad
Technical Architecture v1
settings/
base.py
local.py
production.py
urls.py
wsgi.py
asgi.py
celery.py
apps/
core/
accounts/
profiles/
cvs/
jobs/
skills/
matching/
recommendations/
llm/
notifications/
privacy/
events/
dashboard/
admin_monitoring/
templates/
base.html
components/
partials/
pages/
static/
media_private/
tests/
docs/
7
Django Apps
7.1
core
Shared utilities:
• Base models
• Constants
• Common helpers
• Template helpers
• Health check view
• System settings, optional
7.2
accounts
Authentication:
• Custom user model
• django-allauth integration
• Google OAuth
• GitHub OAuth
9

TuniTech Abroad
Technical Architecture v1
• Email/password signup
• Email verification
• Account linking policy
Use a custom User model from the start:
class User(AbstractUser):
email = models.EmailField(unique=True)
Changing the user model later is painful. Start correctly.
7.3
profiles
Candidate profile:
• Manual profile completion
• Profile completeness calculation
• Target role/type/country
• Language level
• LinkedIn/GitHub/portfolio URLs
Core model:
CandidateProfile
7.4
cvs
CV logic:
• CV upload
• CV parsing status
• Extracted CV data
• CV hash
• Active CV selection
• Delete CV
• CV parsing task orchestration
Core models:
CVUpload
CVParsedData
7.5
jobs
Job source and job records:
• France Travail API integration
• Raw job records
• Normalized jobs
• Job freshness tracking
• PostgreSQL full-text search
• Job detail page
Core models:
JobSource
RawJobRecord
NormalizedJob
IngestionRun
10

TuniTech Abroad
Technical Architecture v1
7.6
skills
Skill taxonomy:
• Canonical skills
• Aliases
• Normalization
• Unknown skill review
• Optional ESCO metadata
Core models:
Skill
SkillAlias
UnmatchedSkillCandidate
7.7
matching
Matching logic:
• Fit score calculation
• Score breakdown
• Anonymous quick match
• Authenticated full match
• Risk flags
• Profile signals
Core models:
MatchResult
QuickMatchSession
7.8
recommendations
Recommendation logic:
• Stored recommendations
• Recommendation refresh
• Ranking score
• Stale recommendation detection
• Dashboard recommended jobs
Core models:
JobRecommendation
RecommendationRun
7.9
llm
OpenRouter integration:
• Client wrapper
• Prompt templates
• Prompt versioning
• LLM cache
• JSON schema validation
• Usage logging
• Cost controls
Core models:
11

TuniTech Abroad
Technical Architecture v1
PromptVersion
LLMCacheEntry
LLMUsageLog
7.10
notifications
Email and notification logic:
• Transactional emails
• Weekly digest
• Email preferences
• Email event logging
• Idempotency keys
• Unsubscribe links
Core models:
EmailPreference
EmailBatch
EmailEvent
EmailUnsubscribeToken
7.11
privacy
Privacy/GDPR-oriented functionality:
• Consent records
• CV processing consent
• Account deletion
• Data deletion worker
• Data export later
Core models:
ConsentRecord
DeletionRequest
7.12
events
Internal product analytics:
• Conversion funnel events
• Job search events
• Quick-match events
• CV upload events
• Recommendation click events
Core model:
UserEvent
Do not add Mixpanel/PostHog in MVP. Internal event logging is enough.
7.13
dashboard
User dashboard views and templates:
• Dashboard home
• Profile page
• CV page
• Recommendations page
12

TuniTech Abroad
Technical Architecture v1
• Saved jobs page
• Match history page
• Email preferences page
Usually view/template-heavy, with business logic delegated to services.
7.14
admin_monitoring
Optional custom admin views later:
• Ingestion health
• LLM cost overview
• Email delivery overview
• CV parsing failure rate
• Recommendation freshness
• Unknown skill queue
MVP can start with Django Admin list views and filters.
8
Environment Configuration
Required environment variables:
DJANGO_SECRET_KEY
DJANGO_SETTINGS_MODULE
DATABASE_URL
REDIS_URL
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET
FRANCE_TRAVAIL_CLIENT_ID
FRANCE_TRAVAIL_CLIENT_SECRET
FRANCE_TRAVAIL_BASE_URL
FRANCE_TRAVAIL_TOKEN_URL
OPENROUTER_API_KEY
OPENROUTER_DEFAULT_MODEL
EMAIL_PROVIDER
EMAIL_HOST
EMAIL_PORT
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL
MEDIA_ROOT
MEDIA_URL
PRIVATE_MEDIA_ROOT
LLM_DAILY_LIMIT_FREE_USER
MAX_CV_UPLOAD_SIZE_MB
13

TuniTech Abroad
Technical Architecture v1
Use django-environ or python-decouple to load settings cleanly.
9
Data Architecture Overview
This section describes model direction only. Full Database Schema v1 comes next.
9.1
User and Profile
9.1.1
User
Fields:
id
email
username
password
is_active
is_staff
is_superuser
date_joined
last_login
Use custom User model.
9.1.2
CandidateProfile
Fields:
id
user_id
full_name
phone
location
linkedin_url
github_url
portfolio_url
website_url
current_level
years_experience
target_country
target_roles
target_type
french_level
english_level
relocation_preference
remote_preference
profile_completeness_score
profile_completeness_status
created_at
updated_at
current_level values:
student
internship_seeker
junior
mid_level
senior
14

TuniTech Abroad
Technical Architecture v1
target_type values:
summer_internship
standard_internship
pfe_end_of_study
first_job
junior_job
mid_level_job
9.2
CV Models
9.2.1
CVUpload
Fields:
id
user_id
file
original_filename
file_hash
file_size
mime_type
is_active
parse_status
parse_error
uploaded_at
parsed_at
deleted_at
Parse statuses:
pending
processing
parsed
parsed_with_warnings
failed
deleted
9.2.2
CVParsedData
Fields:
id
cv_upload_id
raw_text
parsed_json
llm_schema_version
extraction_method
extracted_name
extracted_email
extracted_phone
extracted_location
extracted_linkedin_url
extracted_github_url
extracted_portfolio_url
estimated_years_experience
confidence_json
warnings_json
created_at
15

TuniTech Abroad
Technical Architecture v1
extraction_method values:
text_rules_only
text_rules_plus_llm
manual_only
failed_unreadable_pdf
9.3
Job Models
9.3.1
JobSource
Fields:
id
name
slug
base_url
is_active
source_type
last_successful_sync_at
created_at
updated_at
MVP source:
france_travail
Future source:
la_bonne_alternance
9.3.2
IngestionRun
Fields:
id
source_id
status
started_at
finished_at
search_params_json
fetched_count
created_count
updated_count
unchanged_count
marked_stale_count
marked_expired_count
error_count
error_message
Statuses:
running
success
partial_success
failed
9.3.3
RawJobRecord
Fields:
16

TuniTech Abroad
Technical Architecture v1
id
source_id
source_job_id
raw_payload_json
payload_hash
first_seen_at
last_seen_at
last_fetched_at
source_status
normalization_status
normalization_error
created_at
updated_at
Unique constraint:
source_id + source_job_id
9.3.4
NormalizedJob
Fields:
id
source_id
raw_record_id
source_job_id
title
company_name
location
country
city
department
region
contract_type
remote_type
job_type
experience_level
description
source_url
published_at
expires_at
first_seen_at
last_seen_at
last_fetched_at
status
normalization_version
skill_extraction_status
required_skills_json
optional_skills_json
language_requirements_json
search_vector
created_at
updated_at
Job statuses:
active
stale
expired
17

TuniTech Abroad
Technical Architecture v1
removed
archived
Job type values:
internship
full_time_job
apprenticeship
contract
unknown
9.4
Skill Taxonomy Models
9.4.1
Skill
Fields:
id
canonical_name
slug
category
source
esco_uri nullable
is_active
created_at
updated_at
source values:
manual
esco
imported
admin
Categories:
programming_language
frontend
backend
database
devops
cloud
testing
data_ai
mobile
tools
methodology
soft_skill
other
9.4.2
SkillAlias
Fields:
id
skill_id
alias
normalized_alias
language
created_at
updated_at
18

TuniTech Abroad
Technical Architecture v1
9.4.3
UnmatchedSkillCandidate
Fields:
id
raw_skill_text
normalized_text
source_type
source_id
occurrence_count
status
reviewed_by
reviewed_at
created_at
updated_at
Statuses:
pending
mapped
ignored
9.5
Matching Models
9.5.1
MatchResult
Fields:
id
user_id
profile_id
cv_upload_id
job_id
fit_score
technical_skills_score
experience_score
role_title_score
language_score
location_score
strong_skills_json
missing_required_skills_json
missing_optional_skills_json
risk_flags_json
profile_signals_json
recommended_actions_json
llm_explanation_status
llm_explanation_text
created_at
updated_at
Fit score components:
Technical skills: 45%
Experience level: 20%
Role/title match: 15%
Language fit: 10%
Location/remote/relocation fit: 10%
Recency is not part of fit score.
19

TuniTech Abroad
Technical Architecture v1
9.5.2
QuickMatchSession
Anonymous quick match.
Fields:
id
session_key
job_id
entered_skills_json
experience_level
french_level
estimated_fit_score
matched_skills_json
missing_skills_json
created_at
expires_at
No CV file. No account required. No LLM required. Expire after 24 hours.
9.6
Recommendation Models
9.6.1
JobRecommendation
Fields:
id
user_id
profile_id
cv_upload_id
job_id
fit_score
ranking_score
rank
strong_skills_json
missing_skills_json
risk_flags_json
profile_signals_json
reason_summary
computed_at
status
Recommendation status:
active
stale
dismissed
expired_job
Ranking score:
ranking_score =
fit_score
+ freshness_boost
+ target_type_boost
+ user_preference_boost
- stale_job_penalty
9.6.2
RecommendationRun
Fields:
20

TuniTech Abroad
Technical Architecture v1
id
user_id
trigger_type
status
started_at
finished_at
candidate_jobs_count
scored_jobs_count
stored_recommendations_count
error_message
Trigger types:
cv_uploaded
cv_replaced
profile_updated
new_jobs_imported
dashboard_stale_refresh
nightly_refresh
manual_admin
9.7
Email Models
9.7.1
EmailPreference
Fields:
id
user_id
weekly_digest_enabled
product_updates_enabled
instant_alerts_enabled
created_at
updated_at
MVP fields:
weekly_digest_enabled
product_updates_enabled
9.7.2
EmailBatch
Purpose: prevent duplicate weekly digests.
Fields:
id
batch_type
period_start
period_end
status
created_at
completed_at
9.7.3
EmailEvent
Fields:
id
batch_id nullable
user_id
21

TuniTech Abroad
Technical Architecture v1
email_type
recipient_email
subject
provider
provider_message_id
idempotency_key unique
status
error_message
sent_at
created_at
Example idempotency key:
weekly_digest:user_id:2026-W24
9.8
LLM Models
9.8.1
PromptVersion
Fields:
id
name
version
purpose
template_text
is_active
created_at
Prompt purposes:
cv_extraction
job_skill_extraction
match_explanation
cv_advice
9.8.2
LLMCacheEntry
Fields:
id
cache_key
purpose
input_hash
prompt_version_id
response_json
response_text
created_at
expires_at
9.8.3
LLMUsageLog
Fields:
id
user_id
purpose
provider
model
prompt_version_id
22

TuniTech Abroad
Technical Architecture v1
cache_hit
input_token_estimate
output_token_estimate
cost_estimate
status
error_message
created_at
9.9
Privacy Models
9.9.1
ConsentRecord
Fields:
id
user_id
consent_type
consent_text
accepted_at
ip_address
user_agent
Consent types:
cv_processing
email_digest
terms
privacy_policy
9.9.2
DeletionRequest
Fields:
id
user_id
status
requested_at
processed_at
error_message
Statuses:
pending
processing
completed
failed
9.10
Event Logging Model
9.10.1
UserEvent
Fields:
id
user_id nullable
session_key nullable
event_type
metadata_json
created_at
Events:
23

TuniTech Abroad
Technical Architecture v1
job_search
job_detail_view
quick_match_started
quick_match_completed
signup_started
signup_completed
cv_uploaded
profile_completed
recommendation_clicked
source_apply_clicked
10
France Travail Ingestion Architecture
10.1
Principle
The website must not call France Travail API for every user search.
Correct flow:
France Travail API
-> scheduled ingestion
-> raw records
-> normalized jobs
-> local PostgreSQL search
-> local recommendations
10.2
France Travail Client
Create service:
apps/jobs/services/france_travail/client.py
Responsibilities:
• Authenticate with API credentials
• Manage access token
• Refresh token when needed
• Search job offers
• Fetch job details if endpoint supports it
• Handle pagination/range
• Handle HTTP errors
• Apply retry/backoff
• Apply rate limiting/token bucket if needed
• Log request metadata without leaking secrets
Never expose API secrets to frontend.
10.3
Ingestion Query Strategy
MVP should ingest France IT jobs using controlled search themes.
Initial search themes:
développeur
developpeur
informatique
logiciel
web
python
24

TuniTech Abroad
Technical Architecture v1
java
javascript
react
django
devops
data
cybersécurité
alternance développeur
stage développeur
stage informatique
Later improvement: use France Travail métier/sector referentials where available.
10.4
Ingestion Flow
Celery Beat triggers job_ingestion_sync
-> create IngestionRun
-> FranceTravailClient searches configured queries
-> store/update RawJobRecord
-> update first_seen_at / last_seen_at / last_fetched_at
-> enqueue normalization task per new/changed raw record
-> enqueue skill extraction task per normalized job
-> mark stale/expired jobs
-> finish IngestionRun
10.5
Deduplication
Primary dedupe:
source_id + source_job_id
Secondary duplicate detection later:
title + company + location + description hash
Do not overbuild duplicate detection in MVP.
10.6
Raw Payload Hash
Use payload hash to detect changes:
payload_hash = sha256(canonical_json(raw_payload))
If payload hash unchanged:
update last_seen_at
skip normalization
If changed:
update raw_payload_json
update payload_hash
enqueue normalization
10.7
Job Freshness Logic
Statuses:
active
stale
expired
25

TuniTech Abroad
Technical Architecture v1
removed
archived
Rules:
if expires_at exists and expires_at < now:
status = expired
elif job not seen for 24 hours:
status = stale
elif job not seen for 72 hours:
status = removed
else:
status = active
Values should be configurable.
10.8
High-Intent Revalidation
When user opens an old job detail or clicks source/apply:
if job.last_fetched_at older than 6 hours:
enqueue or perform lightweight refresh
If refresh says job no longer exists:
mark stale/expired
show warning
11
Job Normalization Architecture
11.1
Normalizer
Create:
apps/jobs/services/normalizers/france_travail.py
Responsibilities:
• Map raw source payload to NormalizedJob
• Extract title/company/location/contract
• Detect job type
• Detect experience level
• Detect remote type
• Detect language requirements
• Preserve unknown fields in raw payload only
11.2
Defensive Mapping Rule
Do not assume all fields exist.
Every normalized field must handle missing data safely.
Example:
company_name = payload.get("company", {}).get("name") or "Non précisé"
11.3
Job Type Detection
Job type values:
26

TuniTech Abroad
Technical Architecture v1
internship
full_time_job
apprenticeship
contract
unknown
Detection inputs:
• Contract type from API
• Job title
• Description keywords
French keyword examples:
stage
stagiaire
PFE
fin d'études
alternance
apprentissage
contrat d'apprentissage
CDI
CDD
freelance
mission
11.4
Remote Type Detection
Values:
remote
hybrid
on_site
unknown
Keywords:
télétravail
remote
hybride
présentiel
sur site
12
PostgreSQL Full-Text Search Strategy
12.1
MVP Search Decision
Use PostgreSQL Full-Text Search from the start.
Avoid icontains across large job descriptions as the main search mechanism.
Use:
SearchVector
SearchQuery
SearchRank
12.2
Searchable Fields
Search over:
27

TuniTech Abroad
Technical Architecture v1
title
description
company_name
location
canonical skills
contract type
job type
experience level
12.3
Search Vector
Store or compute search_vector on NormalizedJob.
Recommended weighted vector:
title: A
skills: A
company_name: B
location: C
description: D
12.4
Indexes for Search
Database Schema v1 should include:
GIN index on NormalizedJob.search_vector
btree index on status
btree index on published_at
btree index on job_type
btree index on contract_type
btree index on last_seen_at
Later if needed:
pg_trgm extension for typo/fuzzy matching
Meilisearch for advanced search UX
Do not add Meilisearch in MVP unless PostgreSQL search becomes insufficient.
13
Skill Taxonomy Architecture
13.1
MVP Strategy
Use a flat canonical skill taxonomy with aliases.
Do not start with a complex hierarchy.
Do not rely on LLM-only normalization.
13.2
Taxonomy Structure
Skill
canonical_name
category
source
esco_uri nullable
SkillAlias
alias
28

TuniTech Abroad
Technical Architecture v1
normalized_alias
skill_id
Example:
Skill: Python
Aliases:
- python
- Python 3
- Python3
- dev python
13.3
ESCO Strategy
ESCO can be used as a reference/source for initial IT skill seeding, but do not import full ESCO blindly.
MVP approach:
Use ESCO as inspiration/reference.
Seed a curated IT subset.
Keep flat Skill + SkillAlias model.
Add optional esco_uri metadata.
13.4
Skill Normalization Flow
raw text
-> lowercase
-> strip punctuation
-> normalize accents
-> collapse whitespace
-> exact alias lookup
-> fuzzy alias lookup, optional
-> canonical skill
If no match:
create UnmatchedSkillCandidate
13.5
Initial Skill Seed
MVP should seed 200-300 canonical IT skills.
Categories:
programming_language
frontend
backend
database
devops
cloud
testing
data_ai
mobile
tools
methodology
soft_skill
other
Examples:
29

TuniTech Abroad
Technical Architecture v1
Programming: Python, JavaScript, TypeScript, Java, C#, PHP, Go, Rust, C++, SQL
Frontend: HTML, CSS, Tailwind CSS, Vue.js, React, Angular, Svelte, Bootstrap
Backend: Django, FastAPI, Flask, Node.js, Express.js, NestJS, Spring Boot, Laravel, ASP.NET C
Database: PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, SQLite, Oracle, SQL Server
DevOps: Docker, Kubernetes, CI/CD, GitHub Actions, GitLab CI, Linux, Nginx, Terraform, Ansibl
Cloud: AWS, Azure, Google Cloud, Heroku, Vercel, Render, OVHcloud
Testing: Pytest, Jest, Cypress, Playwright, Unit Testing, Integration Testing
Data/AI: Pandas, NumPy, Scikit-learn, TensorFlow, PyTorch, Power BI, ETL
Tools: Git, GitHub, GitLab, Jira, Postman, Figma
Methodology: Agile, Scrum, Kanban, REST API, GraphQL, Microservices
13.6
Admin Unknown Skill Review
Unknown skill candidates must be reviewable from Django Admin.
Admin actions:
• Map to existing skill
• Create new skill
• Ignore candidate
• Bulk ignore low-value noise
14
CV Parsing Architecture
14.1
Parsing Reality
CV parsing must be practical.
Regex is reliable for exact fields:
email
phone
LinkedIn URL
GitHub URL
portfolio URL
website URL
Regex is not reliable for structured work history, projects, education, or years of experience, especially
with modern two-column PDFs.
Therefore:
Text extraction -> exact regex extractors -> LLM JSON structured extraction -> user confirmat
14.2
Upload Flow
User uploads PDF
-> validate file type/size
-> save to private media
-> create CVUpload(parse_status=pending)
-> enqueue parse_cv_task
-> show processing state
14.3
Parsing Worker
parse_cv_task(cv_upload_id)
-> set status processing
-> extract raw text with PyMuPDF/pdfplumber
30

TuniTech Abroad
Technical Architecture v1
-> if text length below threshold: mark failed_unreadable_pdf
-> run regex extractors for exact fields
-> call OpenRouter for structured JSON extraction
-> validate JSON schema
-> normalize skills through SkillAlias
-> create/update CVParsedData
-> update CandidateProfile draft fields
-> set status parsed or parsed_with_warnings
14.4
OCR Policy
OCR is not MVP.
If PDF has no readable text:
We could not read enough text from this CV. Upload a text-based PDF or complete your profile
OCR can be added later behind the same text extraction interface.
14.5
User Confirmation
Parsed fields are not final truth.
Flow:
parsed CV data
-> show profile review page
-> user confirms/edits fields
-> profile becomes usable
-> recommendations triggered
15
CV LLM JSON Extraction Contract
15.1
Purpose
The LLM receives raw CV text plus deterministic regex findings and returns strict JSON.
The LLM must not invent missing facts. Unknown values should be null or empty arrays.
15.2
Schema Version
MVP schema:
cv_extraction_schema_v1
15.3
JSON Contract
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
31

TuniTech Abroad
Technical Architecture v1
"skills": {
"technical": [],
"tools": [],
"soft": []
},
"experience": [
{
"title": null,
"company": null,
"start_date": null,
"end_date": null,
"description": null,
"technologies": []
}
],
"projects": [
{
"name": null,
"description": null,
"technologies": [],
"links": []
}
],
"education": [
{
"degree": null,
"institution": null,
"start_year": null,
"end_year": null
}
],
"certifications": [],
"languages": [
{
"language": null,
"level": null
}
],
"estimated_years_experience": null,
"warnings": [],
"confidence": {
"identity": 0,
"skills": 0,
"experience": 0,
"education": 0,
"languages": 0
}
}
15.4
Validation Rules
• Required top-level keys must exist.
• Confidence values must be 0-100.
• Arrays must be arrays even when empty.
• Unknown values must be null, not hallucinated.
• Skills must be normalized after extraction.
• LLM output never directly overwrites confirmed user profile fields without user confirmation.
32

TuniTech Abroad
Technical Architecture v1
16
Anonymous Quick Match Architecture
16.1
Purpose
Reduce signup friction.
Anonymous user can test a basic match without account.
16.2
Flow
User opens job detail
-> clicks "Tester mon profil rapidement"
-> enters:
- 3-5 skills
- experience level
- French level
-> system runs lightweight match
-> displays teaser result
-> full analysis requires signup and CV upload
16.3
Data Handling
Store in QuickMatchSession.
No CV file. No personal identity. No LLM.
Recommended expiry:
24 hours
Session key must be UUID/random, not sequential.
The site should mention that a necessary session cookie is used for quick match/session continuity.
17
Matching Engine Architecture
17.1
Principle
Final fit score is deterministic.
LLM can explain but not decide the score.
17.2
Fit Score Components
Technical skills: 45%
Experience level: 20%
Role/title match: 15%
Language fit: 10%
Location/remote/relocation fit: 10%
17.3
Fit Score Formula
fit_score =
technical_skills_score * 0.45
+ experience_score * 0.20
+ role_title_score * 0.15
+ language_score * 0.10
+ location_score * 0.10
33

TuniTech Abroad
Technical Architecture v1
Each component returns 0-100.
17.4
Technical Skills Score
Inputs:
profile canonical skills
job required canonical skills
job optional canonical skills
Basic MVP:
required_match_ratio = matched_required / total_required
optional_match_ratio = matched_optional / total_optional
technical_score =
required_match_ratio * 80
+ optional_match_ratio * 20
If no required skills detected:
use optional/all detected skills
add lower-confidence flag
17.5
Experience Score
Inputs:
profile years_experience
profile current_level
job experience_level
job description signals
Examples:
job junior + profile junior = high
job senior + profile junior = low
job internship + profile student/internship_seeker = high
17.6
Role/Title Score
Inputs:
profile target_roles
job title
job normalized role terms
Example:
target role: backend developer
job title: développeur backend Python
-> high
17.7
Language Score
Inputs:
profile French level
profile English level
job language requirements
French levels:
34

TuniTech Abroad
Technical Architecture v1
unknown
A1
A2
B1
B2
C1
C2
native
If job requires French and profile French is unknown:
language score reduced
risk flag = french_level_missing
17.8
Risk Flags vs Profile Signals
Risk flags affect interpretation.
Examples:
experience_too_low
missing_required_skills
french_level_missing
profile_incomplete
job_may_be_expired
internship_type_unclear
Profile signals do not reduce score unless explicitly relevant.
Examples:
profile_signal_missing_github
profile_signal_missing_linkedin
profile_signal_missing_portfolio
Missing GitHub should not penalize strong developers unless the job explicitly requests GitHub or
portfolio.
18
Recommendation Engine Architecture
18.1
Principle
Recommendations are stored, not computed on every dashboard load.
18.2
Triggers
Generate/refresh recommendations when:
CV uploaded
CV replaced
Profile updated
New jobs imported
Dashboard recommendations stale
Nightly refresh
Admin manual refresh
18.3
Active User Rule
Active user:
35

TuniTech Abroad
Technical Architecture v1
logged in within last 14 days
AND has usable profile
AND has active CV or enough manual profile data
This same 14-day rule is used for recommendation refresh and weekly digest eligibility.
18.4
Recommendation Flow
get active user profile
-> prefilter active jobs
-> calculate fit score
-> calculate ranking score
-> store top recommendations
18.5
Prefiltering
Before scoring, reduce candidate jobs using:
country = France
status = active
job_type matches target_type if possible
skill overlap exists
role/title rough match
not already dismissed
18.6
Ranking Score
Fit score measures candidate-job fit.
Ranking score orders recommendations.
ranking_score =
fit_score
+ freshness_boost
+ target_type_boost
+ user_preference_boost
- stale_job_penalty
Recency affects ranking, not fit.
18.7
Dashboard Refresh Behavior
if fresh recommendations exist:
show them
elif stale recommendations exist:
show current recommendations
enqueue refresh
else:
enqueue generation
show pending state
Do not block dashboard on recommendation generation.
19
LLM Architecture
19.1
Provider
Use OpenRouter.
36

TuniTech Abroad
Technical Architecture v1
19.2
Service Structure
Create:
apps/llm/services/openrouter_client.py
apps/llm/services/prompt_runner.py
apps/llm/services/cache.py
apps/llm/services/schemas.py
19.3
Allowed Use Cases
cv_extraction_assist
job_skill_extraction
match_explanation
cv_improvement_advice
missing_skill_roadmap
19.4
Forbidden MVP Use Cases
Do not use LLM to:
generate final fit score
bulk-score all jobs
run on every search result
provide legal immigration advice
promise employment
promise visa/relocation
19.5
Caching
Cache keys:
CV analysis:
cv_hash + prompt_version + schema_version
Job analysis:
source_job_id + payload_hash + prompt_version
Match explanation:
cv_hash + job_id + prompt_version
Prompt version changes invalidate cache naturally because the version is part of the key.
19.6
Limits
Configurable limits:
max_cv_llm_analysis_per_user_per_day
max_match_explanations_per_user_per_day
max_tokens_per_request
max_total_llm_calls_per_user_per_day
19.7
Failure Behavior
If OpenRouter fails:
show rule-based result
hide or mark AI explanation unavailable
37

TuniTech Abroad
Technical Architecture v1
log error
do not fail core match
19.8
Match Explanation Guardrails
When generating explanations, pass structured facts only:
• Fit score
• Score breakdown
• Canonical matched skills
• Canonical missing skills
• Risk flags
• Profile signals
The LLM must not invent skills, employers, experience, visa status, or employment guarantees.
20
Authentication Architecture
20.1
django-allauth
Use django-allauth for:
email/password signup
email verification
Google OAuth
GitHub OAuth
social account linking
password reset
20.2
Login Methods
MVP:
Google
GitHub
Email/password
Later:
LinkedIn
Facebook
20.3
Account Collision Policy
The system should avoid duplicate accounts when a user signs up with email/password and later logs
in with Google/GitHub using the same verified email.
Implementation concept:
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True
Exact setting names must be verified against the installed django-allauth version during implementa-
tion.
Rule:
Only auto-link OAuth account if provider email is verified.
38

TuniTech Abroad
Technical Architecture v1
If not safe:
ask user to log in with existing account first
20.4
Profile Creation
On first signup:
create CandidateProfile
prefill full name/email where available
redirect to onboarding/profile completion
21
Email Architecture
21.1
Email Provider
Use one transactional provider.
Abstract provider behind:
apps/notifications/services/email_sender.py
Candidate providers:
Resend
Mailgun
SendGrid
Brevo
Provider can be swapped because email logic is behind the service.
21.2
Email Types
Transactional:
email_verification
password_reset
MVP optional:
cv_analysis_completed
weekly_recommendation_digest
21.3
Weekly Digest Flow
Celery Beat triggers weekly digest task
-> create EmailBatch for week
-> select users:
- verified email
- opted in
- active within 14 days
- usable profile
- new relevant recommendations
-> create EmailEvent with unique idempotency_key
-> send through provider
-> log status
39

TuniTech Abroad
Technical Architecture v1
21.4
Idempotency
Weekly digest must never be sent twice for the same user/week.
Use:
EmailEvent.idempotency_key unique
Example:
weekly_digest:user_id:2026-W24
If Celery retries, the unique key prevents duplicate sends.
21.5
Unsubscribe
Every digest email must include:
manage preferences link
unsubscribe link
22
Privacy and GDPR-Oriented Architecture
22.1
Required Pages
MVP must include:
/privacy
/terms
22.2
CV Upload Consent
Before CV upload, user must accept:
I agree that my CV will be processed by TuniTech Abroad to extract my profile, generate job m
Store consent in ConsentRecord.
22.3
Delete CV
User can delete active CV.
Deletion should:
remove file
mark CVUpload deleted
delete/clear parsed CV data
invalidate related recommendations if needed
22.4
Delete Account
User can request/delete account.
Deletion should remove or anonymize:
profile
CV files
parsed CV data
match results
recommendations
saved jobs
40

TuniTech Abroad
Technical Architecture v1
email preferences
social accounts
Keep system logs only if necessary and anonymized.
22.5
Admin CV Access
CV files must not be publicly accessible.
Admin access must be restricted.
Never expose CV download links publicly.
23
UI Architecture
23.1
Language
MVP UI language: French.
Internal code/model names remain English.
Arabic and English UI are future.
23.2
Template Strategy
Use Django templates with HTMX and Tailwind.
Start with built-in template partials:
templates/components/
templates/partials/
templates/pages/
Do not add a component framework immediately.
Later if template complexity grows:
django-components
django-cotton
23.3
HTMX Use Cases
Good HTMX targets:
• Quick match form result
• Save/unsave job button
• Profile completeness partial refresh
• Recommendation refresh status
• Filtered job search partials, if needed
Avoid turning the app into a pseudo-SPA.
24
Admin Architecture
24.1
MVP Admin
Use Django Admin.
Register:
41

TuniTech Abroad
Technical Architecture v1
User
CandidateProfile
CVUpload
CVParsedData
JobSource
RawJobRecord
NormalizedJob
Skill
SkillAlias
UnmatchedSkillCandidate
MatchResult
QuickMatchSession
JobRecommendation
RecommendationRun
EmailPreference
EmailBatch
EmailEvent
LLMUsageLog
LLMCacheEntry
PromptVersion
IngestionRun
ConsentRecord
DeletionRequest
UserEvent
24.2
Admin Monitoring Needs
Admin should be able to diagnose:
failed ingestion runs
failed CV parses
failed LLM calls
failed emails
unknown skill candidates
stale recommendations
high LLM usage users
job normalization failures
MVP can use admin filters/search first.
25
Background Task Architecture
25.1
Task List
Ingestion:
sync_france_travail_jobs
normalize_raw_job_record
extract_job_skills
mark_stale_and_expired_jobs
CV:
parse_cv
extract_cv_skills
apply_cv_parsed_data_to_profile_draft
Matching:
42

TuniTech Abroad
Technical Architecture v1
calculate_match_result
generate_match_explanation
Recommendations:
refresh_user_recommendations
refresh_active_users_recommendations
refresh_recommendations_for_new_jobs
Emails:
send_email_verification
send_password_reset
send_weekly_digest
Privacy/maintenance:
process_account_deletion
delete_orphaned_cv_files
cleanup_expired_quick_matches
25.2
Scheduled Tasks
Recommended schedule:
Job ingestion: every 3-6 hours
Job stale/expiry check: every 6-12 hours
Recommendation nightly refresh: daily
Weekly digest: weekly
Cleanup: daily
25.3
Task Idempotency
Tasks must be safe to retry.
Examples:
normalizing same raw job twice should not duplicate job
sending same digest twice should be prevented by idempotency_key
refreshing recommendations should update existing records
26
Health Check Architecture
Add endpoint:
/health/
Checks:
Django process alive
PostgreSQL connection
Redis connection
Example response:
{
"status": "ok",
"database": "ok",
"redis": "ok"
}
This endpoint supports PaaS/VPS monitoring.
43

TuniTech Abroad
Technical Architecture v1
27
Security Architecture
27.1
File Security
• Validate uploaded file type.
• Limit file size.
• Store CVs outside public static directory.
• Do not serve CV files through public URLs.
• Admin-only CV access.
• Delete file when user deletes CV/account.
27.2
Web Security
Use Django defaults:
CSRF protection
secure password hashing
session security
XSS escaping in templates
Production settings:
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS > 0
27.3
Secrets
Store in environment variables.
Never commit:
OAuth client secrets
France Travail secrets
OpenRouter key
Email SMTP/API keys
Django secret key
27.4
Rate Limiting
MVP rate limits:
anonymous quick match per IP/session
CV uploads per user/day
LLM explanations per user/day
login attempts
28
Logging and Monitoring
28.1
What to Log
Log:
job ingestion start/end
API failures
normalization errors
CV parsing failures
LLM failures
44

TuniTech Abroad
Technical Architecture v1
email failures
recommendation run failures
account deletion failures
Do not log full CV text in normal logs.
28.2
Admin Visibility
Admin should see:
failed ingestion runs
failed CV parses
failed LLM calls
failed emails
unknown skill candidates
28.3
Product Events
Track minimal product events internally:
job_search
job_detail_view
quick_match_started
quick_match_completed
signup_started
signup_completed
cv_uploaded
profile_completed
recommendation_clicked
source_apply_clicked
This is enough for MVP conversion analysis.
29
Testing Strategy
29.1
Unit Tests
Test:
skill alias normalization
profile completeness
fit score calculation
recommendation ranking
job freshness rules
CV regex extractors
CV LLM JSON schema validation
privacy deletion logic
email digest idempotency
29.2
Integration Tests
Test:
job ingestion with mocked France Travail response
raw job to normalized job flow
normalized job to search vector flow
CV upload to parse task flow
profile update to recommendation task
45

TuniTech Abroad
Technical Architecture v1
OAuth account creation, where feasible
email event logging
29.3
Celery Task Tests
Test tasks with:
CELERY_TASK_ALWAYS_EAGER = True
For deeper integration later, use Redis in CI or Docker Compose.
29.4
View Tests
Test:
anonymous job search
job detail
quick match
dashboard access requires login
CV upload requires login
saved jobs require login
admin access restricted
privacy and terms pages exist
29.5
Regression Fixtures
Create sample files:
sample_cv_backend.pdf
sample_cv_frontend.pdf
sample_cv_student.pdf
sample_france_travail_job_backend.json
sample_france_travail_job_internship.json
30
Deployment Architecture
30.1
MVP Deployment Shape
Recommended:
Web service: Django + Gunicorn
Worker service: Celery worker
Scheduler service: Celery Beat
Database: PostgreSQL
Broker/cache: Redis
Static files: Whitenoise first
Media files: Private local volume first; S3-compatible later
30.2
Deployment Platforms
Acceptable MVP options:
Railway
Render
Fly.io
Hetzner VPS
OVH VPS
46

TuniTech Abroad
Technical Architecture v1
For learning and control:
VPS + Docker Compose
For speed:
Render/Railway style PaaS
30.3
Docker Compose Services
web
worker
beat
postgres
redis
Optional later:
nginx
30.4
Process Reliability
If using VPS:
Docker Compose restart: unless-stopped
or supervisord/systemd
Keep Celery worker and beat alive.
31
Implementation Sequence
31.1
Phase 1: Foundation
Deliver:
Django project
PostgreSQL
Redis
Celery
Custom User
django-allauth
Google/GitHub/email auth
Base templates
Tailwind setup
Django Admin
Privacy/Terms placeholder pages
Health endpoint
31.2
Phase 2: Jobs Foundation
Deliver:
JobSource
RawJobRecord
NormalizedJob
IngestionRun
France Travail client skeleton
Mock ingestion using fixture JSON
Normalization service
47

TuniTech Abroad
Technical Architecture v1
PostgreSQL full-text search
Public jobs page
Job detail page
31.3
Phase 3: Skill Taxonomy
Deliver:
Skill
SkillAlias
UnmatchedSkillCandidate
Seed initial skills
Skill normalizer service
Admin review flow
Optional ESCO metadata field
31.4
Phase 4: CV/Profile
Deliver:
CandidateProfile
CVUpload
CVParsedData
PDF upload
Text extraction
Regex exact extraction
OpenRouter structured CV extraction
CV JSON schema validation
Profile review/edit page
Profile completeness
CV consent record
Delete CV
31.5
Phase 5: Matching
Deliver:
Fit score service
MatchResult
QuickMatchSession
Anonymous quick match
Authenticated full match
Score breakdown page
Risk/profile signal output
31.6
Phase 6: Recommendations
Deliver:
JobRecommendation
RecommendationRun
Recommendation worker
Dashboard recommendations
Saved jobs
Recommendation stale refresh
48

TuniTech Abroad
Technical Architecture v1
31.7
Phase 7: LLM Support
Deliver:
OpenRouter client
PromptVersion
LLMCacheEntry
LLMUsageLog
Cached match explanation
Optional job extraction assist
LLM limits
Note: CV LLM extraction starts in Phase 4 because it is core to parsing quality.
31.8
Phase 8: Emails
Deliver:
EmailPreference
EmailBatch
EmailEvent
Verification/password reset
Weekly digest
Idempotency key
Unsubscribe/manage preferences
31.9
Phase 9: Privacy and Polish
Deliver:
Account deletion
Data deletion worker
Admin monitoring filters
UserEvent logging
Error states
Empty states
Security hardening
32
Technical Risks and Mitigations
32.1
France Travail API Access
Risk:
• API registration/configuration may take time.
• Available fields may differ from expected structure.
Mitigation:
• Build source adapter pattern.
• Store raw payload.
• Use fixtures first.
• Do not hardcode one perfect payload shape.
• Avoid scraping fallback in MVP.
32.2
Skill Matching Quality
Risk:
49

TuniTech Abroad
Technical Architecture v1
• Bad taxonomy creates bad match scores.
Mitigation:
• Start with curated flat taxonomy.
• Use aliases.
• Store unknown skills.
• Review unknown skills in admin.
• Keep score explainable.
32.3
CV Parsing Quality
Risk:
• PDF formats vary.
• Two-column PDFs produce messy text extraction.
• Scanned PDFs may have no extractable text.
Mitigation:
• Use PyMuPDF/pdfplumber to extract raw text.
• Use regex only for exact fields.
• Use LLM JSON extraction for structured fields.
• Show parsed data to user.
• Allow manual correction.
• Defer OCR.
32.4
LLM Cost
Risk:
• OpenRouter cost grows if used too often.
Mitigation:
• Deterministic scoring.
• Cache LLM calls.
• Limit per user.
• Use LLM only where it gives clear value.
• Avoid bulk LLM scoring.
32.5
Scope Creep
Risk:
• Adding too many countries/sources early.
Mitigation:
• France only.
• One official source first.
• La Bonne Alternance later.
• No recruiter/training center dashboard in MVP.
32.6
Email Duplication
Risk:
• Celery retries send duplicate weekly digests.
Mitigation:
• EmailBatch.
50

TuniTech Abroad
Technical Architecture v1
• EmailEvent idempotency key.
• Unique constraint on idempotency key.
33
Architecture Acceptance Criteria
Architecture is accepted when:
Django app structure is clear.
Database entities are defined at architecture level.
Job ingestion flow is clear.
France Travail source is locked.
Skill taxonomy strategy is clear.
PostgreSQL full-text search is selected.
CV parsing flow is realistic.
LLM CV JSON schema is defined.
Matching score formula is clear.
Recommendation refresh logic is clear.
LLM boundaries are clear.
Auth collision policy is clear.
Email digest idempotency is defined.
Privacy deletion flow is defined.
Admin monitoring scope is defined.
Health endpoint is included.
Implementation phases are ordered.
34
Final Architecture Decision
Build TuniTech Abroad as a Django-first modular monolith with background workers.
Architecture style:
Modular Django monolith
+ PostgreSQL
+ PostgreSQL Full-Text Search
+ Redis/Celery
+ scheduled job ingestion
+ flat skill taxonomy
+ deterministic matching
+ cached OpenRouter support
+ Django Admin monitoring
+ privacy/deletion flows
Do not split into microservices.
Do not build a SPA.
Do not use live external API calls for every user search.
Do not use LLM as scoring authority.
Do not spend MVP time on OCR, scraping, or multi-country expansion.
This architecture is strong enough for MVP, simple enough for one developer, and extensible enough
for future sources, paid reports, recruiters, and training center dashboards.
35
Next Phase
Next document:
51

TuniTech Abroad
Technical Architecture v1
Database Schema v1 must convert the architecture into concrete Django models, fields, constraints,
indexes, enums, JSON fields, and relationships.
Priority schema decisions:
custom User model
CandidateProfile
CVUpload/CVParsedData
RawJobRecord/NormalizedJob
PostgreSQL search_vector
Skill/SkillAlias/UnmatchedSkillCandidate
MatchResult
JobRecommendation
EmailBatch/EmailEvent idempotency
ConsentRecord/DeletionRequest
UserEvent
LLM cache/logs
36
Reference Notes
These references are implementation checks, not external dependencies for the product logic:
• France Travail API Offres d’emploi: https://www.data.gouv.fr/dataservices/api-offres-demploi
• La Bonne Alternance developer space: https://labonnealternance.apprentissage.beta.gouv.fr/espace-
developpeurs
• Django: https://www.djangoproject.com/
• Django PostgreSQL full-text search: https://docs.djangoproject.com/en/stable/ref/contrib/postgres/search/
• django-allauth configuration: https://docs.allauth.org/
• PyMuPDF text extraction notes: https://pymupdf.readthedocs.io/en/latest/recipes-text.html
• ESCO: https://esco.ec.europa.eu/en/about-esco/what-esco
52