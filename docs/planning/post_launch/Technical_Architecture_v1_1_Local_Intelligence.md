# Technical Architecture v1.1 — Local Intelligence and Post-Launch Hardening

Status: Post-launch technical addendum  
Product: TuniAtlas Jobs  
Purpose: Define architecture for ingestion diagnostics, search hardening, parser quality, skill taxonomy, admin monitoring, and ML-ready data

## 1. Non-negotiable architecture rules

These rules remain active:

```text
Django modular monolith.
Django ORM.
PostgreSQL source of truth.
Redis for broker/cache/rate limits/temporary counters.
Celery/Celery Beat for background work.
django-allauth for auth.
Django templates + HTMX + Tailwind.
No SPA rewrite.
No React/Next.js/Angular.
No FastAPI.
No MongoDB.
No SQLAlchemy.
Views stay thin.
Services own business logic.
Celery tasks call services only.
Models do not call external APIs.
No LLM calls from views.
No live France Travail calls during normal user search.
```

## 2. v1.1 architecture theme

v1.1 adds a local intelligence and quality layer.

This does not mean one new giant app named `intelligence`.

Keep services close to their domain:

```text
apps/jobs/services/ingestion_diagnostics.py
apps/jobs/services/search_quality.py
apps/jobs/services/freshness_audit.py
apps/jobs/services/public_copy_audit.py
apps/cvs/services/name_extraction.py
apps/cvs/services/parser_audit.py
apps/skills/services/alias_audit.py
apps/skills/services/relationships.py
apps/matching/services/score_audit.py
apps/recommendations/services/reason_builder.py
apps/core/services/admin_alerts.py
apps/core/services/health_checks.py
```

## 3. Main post-launch data flows

### 3.1 Job ingestion diagnostics flow

```text
Celery Beat / admin manual run
-> JobIngestionService
-> FranceTravailClient
-> RawJobRecord
-> JobIngestionQueryRun per source query
-> NormalizedJob
-> NormalizedJobSkill
-> JobEligibilityService
-> JobIngestionDiagnosticsService
-> admin dashboard / diagnose command
```

Goal:

```text
Explain external fetched -> raw stored -> normalized -> active -> public visible -> matchable.
```

### 3.2 Search flow with hardening

```text
GET /jobs/
-> JobSearchForm or JobSearchFilterService.clean(raw_filters)
-> normalize q/company/date filters
-> JobSearchService.search(clean_filters, user)
-> PostgreSQL local query
-> SearchQueryLog
-> render results
```

Rules:

```text
Whitespace-only q is treated as empty.
Whitespace-only company is ignored.
Invalid dates never crash.
No external API call.
```

### 3.3 CV parser audit flow

```text
local private CV corpus
-> audit_cv_parser command
-> CVParserAuditService
-> CVParsingService in isolated/audit mode
-> compare actual output to expected JSON
-> CVParserAuditRun / CVParserAuditCase optional DB records
-> CSV/JSON reports
-> regression fixes
```

No real CV corpus files are committed.

### 3.4 CV upload production flow with confidence

```text
User uploads CV
-> CVUploadService validates file
-> parse_cv Celery task
-> CVTextExtractionService
-> CVDeterministicExtractorService
-> CVNameExtractionService
-> optional CVLLMExtractionService if enabled
-> SkillNormalizerService
-> CVParsedData with confidence_json and warnings_json
-> ProfileSkill draft rows
-> user confirms profile
```

Wrong low-confidence data must not overwrite confirmed profile data.

### 3.5 Skill normalization flow

```text
raw skill text
-> normalize accents/case/punctuation/spacing
-> SkillAlias lookup
-> canonical Skill
-> optional SkillRelation partial signal later
-> UnmatchedSkillCandidate if unknown
```

No unknown skill is auto-created into `Skill` without review.

### 3.6 Matching flow

```text
CandidateProfile + ProfileSkill(skill_id)
-> NormalizedJob + NormalizedJobSkill(skill_id)
-> MatchScoringService
-> deterministic FitScoreResult
-> MatchResult snapshot
-> optional LLM explanation later
```

Final score remains deterministic.

## 4. Production stabilization architecture

### 4.1 HTTPS awareness behind Caddy

Production settings should include:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

These must be committed through Git, not manually edited on server.

### 4.2 Canonical domain

Infrastructure should redirect:

```text
https://www.tuniatlas.com/* -> https://tuniatlas.com/*
```

OAuth redirect URIs should support the canonical callback.

### 4.3 OAuth account linking

OAuth duplicate verified-email behavior belongs in accounts/allauth adapter/service logic.

Rules:

```text
verified same email can be linked safely
unverified provider email cannot silently link
no duplicate users for same verified email
clear user message on unsafe collision
```

## 5. Job ingestion architecture

### 5.1 Config model

Use existing config model if present. Do not create duplicate config concepts.

Required fields conceptually:

```text
source
is_active
target_daily_fetch_count
max_jobs_per_run
max_pages_per_query
page_size
queries_json
contract_filters_json
location_filters_json
remote_filters_json
stale_after_hours
removed_after_hours
expire_grace_hours
last_effective_config_json
```

### 5.2 Query-level audit

Add query-level run tracking if missing.

Purpose:

```text
One global run count is not enough.
Admin must know which query produced which jobs and errors.
```

### 5.3 Ingestion target logic

`target_daily_fetch_count` is a limit/target, not a guarantee.

Architecture must support:

```text
multiple configured queries
page/range iteration
deduplication by source/source_job_id
stop when target reached
stop when source has no more results
clear report when target not reached
```

### 5.4 Freshness protection

Freshness service must be defensive:

```text
failed ingestion run must not mass-stale jobs
failed ingestion run must not mass-remove jobs
removed threshold must be checked before stale threshold
date-only expiration must use end-of-day plus grace
```

## 6. Search architecture

### 6.1 Filter cleaning service

Add or formalize:

```python
JobSearchFilterService.clean(raw_filters: dict) -> JobSearchFilters
```

Responsibilities:

```text
strip q
strip company
normalize whitespace
parse dates
validate enum filters
apply exact-date precedence
return stable filter object
```

### 6.2 Search service

`JobSearchService.search()` receives cleaned filters only.

It handles:

```text
active jobs by default
company filter
published date exact/range filters
query full-text search
skill alias search when possible
pagination
sort fallback
```

### 6.3 Search logging

Create `SearchQueryLog` through service.

Failure to log analytics must not break user search.

## 7. CV parser architecture

### 7.1 Name extractor

`CVNameExtractionService` should return structured output:

```python
{
    "value": str | None,
    "confidence": float,
    "candidates": list[dict],
    "warnings": list[str],
}
```

It must reject sentence-like candidates.

### 7.2 Deterministic extractor

`CVDeterministicExtractorService` owns:

```text
email
phone
LinkedIn
GitHub
portfolio URL
website URL
simple language signals
basic section detection
```

### 7.3 Parser coordinator

`CVParsingService` owns:

```text
parse status transitions
text extraction
field extraction
optional LLM call
skill normalization
CVParsedData creation
ProfileSkill draft creation
confidence/warnings
```

### 7.4 Parser audit service

`CVParserAuditService` must be usable from management command and tests.

It must not depend on production CV files.

## 8. Skill taxonomy architecture

### 8.1 Canonical skill rules

Skill taxonomy is the stable label space.

Current deterministic system uses it.
Future ML uses it.

### 8.2 Alias normalization

Required normalization:

```text
lowercase
trim
normalize accents
normalize punctuation carefully
collapse whitespace
preserve meaningful skill symbols when needed: .NET, C#, C++, CI/CD, Node.js
lookup SkillAlias.normalized_alias
```

Warning: blindly stripping punctuation can break `.NET`, `C#`, `C++`, `Node.js`, `CI/CD`.

### 8.3 Skill relationships later

Add later only if needed:

```text
SkillRelation(parent_skill, child_skill, relation_type, weight)
```

Use cases:

```text
.NET parent of ASP.NET Core
JavaScript ecosystem relation to React/Node.js
Python relation to Django/FastAPI, but FastAPI not project stack
```

Do not let relationships over-credit missing exact skills.

## 9. Admin monitoring architecture

### 9.1 Owner dashboard

Build for one owner.

```text
staff/superuser access
no team roles
no organization model
no enterprise RBAC
```

### 9.2 Dashboard sources

Dashboards call services:

```text
OperationsDashboardService
DataQualityDashboardService
SearchQualityDashboardService
CVParserDashboardService
IngestionDiagnosticsService
AdminAlertQueryService
```

Views render service results.

### 9.3 Admin CV download

Serve protected file through service/view.

```text
no public media URL
no Caddy static private media exposure
superuser or explicit permission
access logged
no full path shown
```

## 10. Admin alerts architecture

### 10.1 Service

```python
AdminAlertService.check_and_send_alerts() -> dict
```

### 10.2 Email destination

```text
ADMIN_ALERT_EMAIL
```

No hardcoded production email.

### 10.3 Alert types

```text
celery_heartbeat_missing
ingestion_failed
job_count_drop
zero_visible_jobs
cv_parse_failure_rate_high
normalization_failure_rate_high
search_zero_result_rate_high
email_failure_rate_high
oauth_error_spike
server_error_spike
disk_usage_high
redis_unavailable
database_unavailable
```

### 10.4 Delivery

Use Celery task.

Avoid sending inside long transactions.

## 11. Future ML architecture

### 11.1 Current decision

No production ML/DL now.

### 11.2 ML-ready architecture now

Add data collection:

```text
CVFieldCorrection
SkillExtractionFeedback
JobQualityFeedback
SearchQueryLog
CVParserAuditRun
CVParserAuditCase
```

### 11.3 Future ML plug-in point

Future model can be introduced as a service:

```python
MLSkillExtractionService.extract(text: str, source_type: str) -> SkillExtractionResult
```

It must output:

```text
canonical Skill IDs
confidence
raw evidence
warnings
```

It must not output uncontrolled raw skills directly into matching.

### 11.4 Future model evaluation

Evaluation will use:

```text
parser audit corpus
correction labels
admin-reviewed unknown skill candidates
job quality feedback
skill extraction feedback
```

## 12. Forbidden shortcuts

Do not do these:

```text
rewrite frontend to SPA
call France Travail during user search
trust LLM raw output as final skills
let LLM change score
serve CVs through public media
commit real CV test corpus
add fake enterprise admin roles
hardcode admin alert email
strip punctuation in a way that breaks .NET/C#/C++
mark jobs stale/removed after failed ingestion
```
