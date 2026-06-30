# PRD v1.1 — Product Intelligence Quality Requirements

Status: Post-launch product requirements addendum  
Product: TuniAtlas Jobs  
Historical base: TuniTech Abroad PRD v1  
Purpose: Define quality requirements for ingestion, search, CV parsing, skills, matching, admin monitoring, and future ML readiness

## 1. Purpose

This PRD addendum defines post-launch requirements needed to make TuniAtlas reliable as a job intelligence product.

It focuses on:

```text
job ingestion reliability
job freshness correctness
job search hardening
country-neutral public copy
CV parser quality
skill taxonomy accuracy
matching accuracy
admin monitoring
admin alerts
future ML readiness
```

It does not change the approved stack or the core MVP user journey.

## 2. Product quality principle

The product’s value is not “more pages.”

The product’s value is:

```text
Can the user trust the job inventory?
Can the user search reliably?
Can the system parse CV data without embarrassing errors?
Can the system understand skills correctly?
Can the match score explain why the job fits or does not fit?
Can the admin see and fix data quality problems?
```

## 3. Public positioning requirement

Public UI must be country-neutral.

### 3.1 Required public wording direction

Use wording like:

```text
Tech jobs abroad
International tech opportunities
Relevant opportunities
Job intelligence for Tunisian tech talent
Understand your fit
Find what to improve before applying
```

Avoid wording like:

```text
France IT jobs
France-first job intelligence
France opportunities
France recruiters
French market only
```

### 3.2 Allowed France references

These are allowed:

```text
job location/address, e.g. Paris, France
source name in admin/internal UI, e.g. France Travail
source configuration
internal docs
raw source payload
legal/source attribution if needed
```

### 3.3 Current country behavior

For now:

```text
No public country dropdown.
No public country checkbox.
No public country marketing copy.
Backend still defaults to France/source config.
```

Future multi-country functionality is a separate phase.

## 4. Job ingestion requirements

### 4.1 Problem statement

Manual ingestion previously produced around 1,000 jobs. Automatic production ingestion currently appears to show around 100–200 jobs.

This must be diagnosed and fixed.

### 4.2 Required ingestion visibility

Admin must see the full funnel:

```text
configured source queries
configured daily target fetch count
configured max jobs per run
configured page size/range
configured max pages per query
external fetched count
raw records stored
created count
updated count
unchanged count
normalization success count
normalization failure count
active jobs
stale jobs
expired jobs
removed jobs
public visible jobs
public matchable jobs
hidden/excluded reason counts
```

### 4.3 Configurable target

Admin must be able to configure:

```text
target_daily_fetch_count
max_jobs_per_run
max_pages_per_query
page_size
queries_json
stale_after_hours
removed_after_hours
expire_grace_hours
```

Default target:

```text
target_daily_fetch_count = 1000
```

Constraint:

```text
The system must not fake this number. If the source/API/config only returns 600 relevant jobs, admin diagnostics must report the real reason.
```

### 4.4 Ingestion diagnostics command

Required management command:

```bash
python manage.py diagnose_job_ingestion --settings=config.settings.production
```

Output must include:

```text
latest ingestion runs
per-query fetch counts
created/updated/unchanged counts
normalization statuses
skill extraction statuses
freshness statuses
public eligibility counts
Celery Beat status summary if available
last error summaries
```

### 4.5 Acceptance criteria

```text
Admin can explain why visible jobs differ from fetched jobs.
Automatic ingestion can reach the configured target when source results exist.
The system reports when the source/config cannot satisfy the target.
No user-facing search calls the external API.
Raw source data remains stored before normalization.
```

## 5. Job freshness and expiry requirements

### 5.1 Correct ordering

Freshness logic must check strongest terminal conditions first:

```python
if expires_at and expires_at < now - expire_grace:
    status = "expired"
elif last_seen_at and last_seen_at < now - removed_after:
    status = "removed"
elif last_seen_at and last_seen_at < now - stale_after:
    status = "stale"
else:
    status = "active"
```

### 5.2 Safety rules

```text
Do not mass-stale jobs after a failed ingestion run.
Do not mass-remove jobs after a failed ingestion run.
Do not expire date-only jobs before the end of that date plus configured grace.
If expires_at is missing, rely on last_seen_at thresholds.
Use the latest successful source sync as freshness reference.
External API failure must not destroy public inventory.
```

### 5.3 Tests

Required tests:

```text
expired date becomes expired only after grace
removed threshold wins over stale threshold
stale threshold marks stale
fresh job remains active
missing expires_at uses last_seen_at
failed ingestion run does not mass-stale active jobs
failed ingestion run does not mass-remove active jobs
```

## 6. Job search requirements

### 6.1 Search input hardening

Search must handle:

```text
empty query
whitespace-only query
multi-space query
uppercase/lowercase differences
accent variations
invalid filters
punctuation-heavy terms
page too high
anonymous best-match fallback
```

Expected behavior:

```text
/jobs/?q=
/jobs/?q=%20%20%20
```

Both behave like `/jobs/` and show active jobs with pagination.

### 6.2 Company filter

Add filter:

```text
company
```

Examples:

```text
/jobs/?company=Capgemini
/jobs/?company=Orange
```

Rules:

```text
empty/space-only company ignored
company search matches company_name
invalid text does not crash
pagination preserves company filter
```

### 6.3 Published date filters

Add filters:

```text
published_exact
published_from
published_to
```

Examples:

```text
/jobs/?published_exact=2026-06-30
/jobs/?published_from=2026-06-01&published_to=2026-06-30
```

Rules:

```text
published_exact applies start/end of same day
published_from applies >= start of day
published_to applies <= end of day
if published_exact is valid, it takes precedence over from/to
invalid dates show safe form error or are ignored cleanly
invalid dates never produce 500
```

### 6.4 Skill search aliases

Search should understand canonical skills and aliases where practical.

Examples:

```text
.net
.NET Core
dotnet
node js
node.js
reactjs
postgres
c sharp
csharp
c++
ci/cd
```

Search by skill should find jobs where the skill exists in `NormalizedJobSkill` even if not obvious in the title/description.

### 6.5 Search logging

Log search quality data:

```text
raw query
normalized query
filters
result count
anonymous session hash or user
created_at
```

Track:

```text
zero-result searches
space-only searches
invalid filter attempts
popular company filters
popular skill searches
```

### 6.6 Acceptance criteria

```text
Whitespace-only query returns active jobs.
Company filter works.
Exact published date filter works.
Published date range works.
Invalid date does not crash.
Pagination works with filters.
Anonymous best-match falls back cleanly.
Expired jobs hidden by default.
Search uses local PostgreSQL only.
```

## 7. CV parser quality requirements

### 7.1 Principle

```text
Wrong empty is acceptable.
Wrong confident value is not acceptable.
```

Examples:

```text
Good: full_name = None with warning low_confidence_name
Bad: full_name = "je me suis"
```

### 7.2 Required confidence behavior

Every extracted field should have confidence and warnings where relevant:

```text
full_name
email
phone
linkedin_url
github_url
portfolio_url
website_url
location
skills
estimated years experience
languages
```

Low-confidence fields must not silently overwrite confirmed profile data.

### 7.3 Name extraction requirements

Name extractor must reject:

```text
sentences
first-person phrases
"je me suis"
"j'ai"
"I am"
"my"
profile summaries
section headers
job titles
emails
URLs
phones
dates
all-lowercase prose
strings with too many words
```

Candidate sources:

```text
explicit labels: Nom, Nom et prénom, Name, Full name
top text lines from first page
email local-part hint
authenticated user profile name
LLM output only as supporting signal if enabled
```

### 7.4 Parser audit corpus

Create local-only private corpus:

```text
private_test_corpus/cvs/
private_test_corpus/expected/
private_test_corpus/reports/
```

Add to `.gitignore`:

```gitignore
private_test_corpus/
```

For each CV:

```text
private_test_corpus/cvs/cv_001.pdf
private_test_corpus/expected/cv_001.json
```

Expected JSON example:

```json
{
  "full_name": "Example Person",
  "email": "example@example.com",
  "phone": "+21600000000",
  "linkedin_url": "https://www.linkedin.com/in/example",
  "github_url": "https://github.com/example",
  "skills": ["Python", "Django", "PostgreSQL", "Docker"]
}
```

Do not commit real CV PDFs or private expected data.

### 7.5 Parser audit command

Required command:

```bash
python manage.py audit_cv_parser \
  --cv-dir private_test_corpus/cvs \
  --expected-dir private_test_corpus/expected \
  --output private_test_corpus/reports/latest.csv \
  --settings=config.settings.local
```

Command must:

```text
parse all CVs
compare actual results to expected JSON
calculate field metrics
calculate skill precision/recall
save CSV and JSON reports
exit non-zero if thresholds fail
```

### 7.6 Parser metrics

Track:

```text
name_exact_accuracy
name_acceptable_accuracy
email_accuracy
phone_accuracy
linkedin_accuracy
github_accuracy
portfolio_accuracy
skill_precision
skill_recall
false_skill_rate
parse_failed_count
low_confidence_count
```

### 7.7 Regression loop

Required workflow:

```text
run audit_cv_parser
inspect failures
fix extractor/normalizer
add regression unit test for exact failure
rerun full corpus
accept only if corpus score improves or remains stable
```

## 8. Skill taxonomy requirements

### 8.1 Canonical matching

Matching must use canonical skills, not raw extracted strings.

Required target:

```text
ProfileSkill.skill_id matches NormalizedJobSkill.skill_id
```

Avoid:

```text
raw string equality
case-sensitive text matching
uncontrolled fuzzy matching
LLM raw skills directly affecting score
```

### 8.2 Alias examples

Must handle:

```text
.NET
.NET Core
dotnet
dot net
ASP.NET
ASP.NET Core
C#
csharp
C sharp
Node.js
node js
ReactJS
Postgres
PostgreSQL
CI/CD
C++
```

### 8.3 Related skills

Later matching may support related skills:

```text
exact skill match = full credit
related skill match = partial credit
parent ecosystem match = small credit
```

Example:

```text
Job requires ASP.NET Core.
Candidate has ASP.NET Core -> full match.
Candidate has .NET + C# -> partial signal.
Candidate has Java only -> no match.
```

Do not over-credit related skills.

## 9. Matching and recommendation quality requirements

### 9.1 Fit score formula

Fit score must follow the product contract:

```text
technical skills: 45%
experience: 20%
role/title: 15%
language: 10%
location/remote/relocation: 10%
```

LLM cannot change score.

### 9.2 Low-confidence job skills

If job skill extraction is weak:

```text
do not destroy score blindly
add profile/job signal: low_confidence_job_skills
show warning/explanation
use detected skills carefully
```

### 9.3 Recommendation explanations

Recommendation card/detail should show:

```text
why this job is recommended
matched required skills
missing required skills
missing optional skills
language risk
location/remote risk
freshness
next action
```

## 10. Admin monitoring requirements

### 10.1 Solo-admin dashboard

Admin is currently one owner/operator.

Required:

```text
operations dashboard
data quality dashboard
search quality dashboard
CV parser dashboard
job ingestion diagnostics
skill review dashboard
admin alert log
```

Not required now:

```text
multi-admin roles
reviewer workflows
team assignments
organization hierarchy
```

### 10.2 CV admin access

Admin can download CV only through protected admin service/view.

Rules:

```text
superuser-only or explicit staff permission
served through Django, not public media
uses CVUpload.all_objects only inside internal/admin service
logs access
no filesystem path exposure
no public caching
```

### 10.3 Admin alerts

Send admin alerts to environment-configured address:

```text
ADMIN_ALERT_EMAIL=contact@tuniatlas.com
```

Do not hardcode email in code.

Alert triggers:

```text
Celery heartbeat missing
full ingestion failure
CV parse failure rate above threshold
normalization failure rate above threshold
job count drops sharply
zero visible jobs
email failures spike
OAuth failures spike
500 errors spike
disk usage high
Redis/database unavailable
```

## 11. Future ML readiness requirements

Do not build production ML now.

Build ML-ready data:

```text
CVFieldCorrection
SkillExtractionFeedback
JobQualityFeedback
SearchQueryLog
CVParserAuditRun
CVParserAuditCase
```

Future ML must predict into the same canonical skill taxonomy.

Required future architecture compatibility:

```text
Now:
raw text -> deterministic extraction -> canonical Skill IDs -> deterministic score

Future:
raw text -> ML extraction -> canonical Skill IDs -> deterministic score
```

The deterministic score remains final.
