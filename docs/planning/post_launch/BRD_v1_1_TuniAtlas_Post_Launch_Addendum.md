# BRD v1.1 — TuniAtlas Post-Launch Addendum

Status: Post-launch addendum  
Supersedes: nothing  
Depends on: BRD v1, PRD v1, Technical Architecture v1, Database Schema v1, Service Contracts v1  
Public brand: TuniAtlas  
Product line: TuniAtlas Jobs  
Historical/internal name: TuniTech Abroad

## 1. Purpose

This document updates the business requirements after the first production deployment.

It does not replace BRD v1. BRD v1 remains the original product definition:

```text
A job intelligence platform for Tunisian IT candidates that helps users understand which opportunities are realistic, why they match, which skills are missing, and what to improve before applying.
```

v1.1 adds post-launch operational and quality requirements discovered after the site started running publicly.

## 2. Product identity update

Public identity:

```text
Brand: TuniAtlas
Product line: TuniAtlas Jobs
Tagline direction: Tech careers abroad for Tunisian talent
```

Historical/internal identity:

```text
Original planning name: TuniTech Abroad
Original MVP scope: France-first
Current public copy direction: country-neutral wording
Current hidden/default source country: France
```

Important distinction:

```text
The backend may still ingest France Travail jobs by default.
The public UI should not position the product as France-only.
Job cards may still show France inside job location/address because that is actual job data.
```

Examples:

```text
Wrong public copy: France IT jobs for Tunisians
Better public copy: Tech jobs abroad for Tunisian talent

Wrong public copy: Find France opportunities
Better public copy: Find relevant opportunities abroad

Allowed: Job location = Paris, France
Allowed: Admin source = France Travail
Allowed: Internal config default_country = France
```

## 3. Solo-founder operating model

Current operating model:

```text
Baha is the only developer, admin, designer, and operator.
```

Therefore the business does not currently need enterprise admin layers.

Required now:

```text
owner/superuser admin dashboard
staff-only operational pages
sensitive file access logging
admin email alerts
admin diagnostics
simple configurable ingestion settings
```

Deferred:

```text
multi-admin role hierarchy
team permissions
reviewer/moderator roles
organization accounts
admin approval workflow
training-center admin roles
recruiter admin roles
customer support tooling
```

Reason: building fake enterprise admin now wastes time and creates security complexity before there is a team or revenue.

## 4. Post-launch business risk discovered

The site’s value depends on trust in intelligence quality.

Core risk:

```text
If CV parsing, skill detection, job matching, recommendation ranking, or job search quality is poor, users will treat the website as another weak job board.
```

Concrete observed issue:

```text
A tested CV produced a wrong name extraction: "je me suis".
```

Business interpretation:

```text
Wrong confident extraction is worse than empty extraction.
The system must prefer "not detected" over wrong personal data.
```

## 5. Competitive strength

TuniAtlas must win through product intelligence, not listing volume alone.

The product strength is:

```text
clean CV parsing
canonical skill detection
strong skill alias handling
explainable deterministic matching
missing skill detection
search quality
recommendation quality
clear next action for the candidate
```

Weakness to avoid:

```text
generic job cards
raw keyword matching
LLM-looking output without deterministic quality
wrong CV data
unexplained scores
small or stale job inventory
searches that silently fail
```

## 6. Job supply requirement

Production must explain why job inventory is lower than expected.

Observed problem:

```text
Manual fetch previously produced around 1,000 jobs.
Automatic production ingestion currently appears to show around 100–200 jobs.
```

Business requirement:

```text
The owner/admin must be able to see exactly where jobs are lost:
external source fetched
-> raw records stored
-> normalized jobs
-> active jobs
-> public visible jobs
-> matchable jobs
```

Target:

```text
Automatic ingestion should support a configurable target of around 1,000 fetched jobs per day when the configured source queries and source API provide enough valid jobs.
```

This is a target, not a blind promise. If the source returns fewer relevant jobs under the active config, the system must show that clearly.

## 7. Job search quality requirement

Public job search must behave predictably.

Search should handle:

```text
empty query
whitespace-only query
multi-space query
invalid filters
company name filter
published exact date filter
published date range filter
skill aliases
punctuation-heavy skills like .NET, C#, C++, Node.js
pagination edge cases
anonymous best-match fallback
```

Business requirement:

```text
A user searching with blank spaces must not see a false empty state.
Whitespace-only search should behave like no query and show active jobs.
```

## 8. CV parsing quality requirement

CV parsing must be measured, not guessed.

Requirement:

```text
Build a private local regression corpus with 100+ CVs and expected JSON outputs.
Run automated parser audits.
Track extraction accuracy and failures.
Never commit real CVs.
Never expose private CV text in logs.
```

Key principle:

```text
Wrong empty is acceptable.
Wrong confident value is not acceptable.
```

For example:

```text
Good: full_name = None, warning = low_confidence_name
Bad: full_name = "je me suis"
```

## 9. Skill taxonomy and matching requirement

The system must understand skill variants and aliases.

Examples:

```text
.NET Core
.net core
dotnet
.NET
ASP.NET Core
C# .NET
```

These must map intentionally into canonical skills and/or related skills.

Business rule:

```text
Canonical taxonomy is not temporary work. It is the stable label space for current deterministic matching and future ML.
```

## 10. ML/DL business decision

Current decision:

```text
Do not build ML/DL now.
Build ML-ready taxonomy, correction data, parser audits, and feedback labels now.
```

Reason:

```text
Production ML needs labeled real data. The product does not yet have enough real corrected CV fields, skill labels, job-quality labels, or matching feedback.
```

No double-work architecture:

```text
Now:
raw CV/job text -> deterministic extractor -> canonical Skill IDs -> deterministic matching

Future:
raw CV/job text -> ML extractor -> canonical Skill IDs -> deterministic matching
```

The taxonomy remains in both versions.

## 11. Admin monitoring requirement

As owner/admin, Baha must see enough operational data to run the product alone.

Required dashboards:

```text
operations dashboard
data quality dashboard
search quality dashboard
CV parser quality dashboard
job ingestion diagnostics
skill taxonomy review
admin alert log
```

Admin must see:

```text
users
CV uploads
CV parse statuses
CV parse warnings
jobs fetched/normalized/active/public/matchable
freshness status counts
zero-skill jobs
unknown skill candidates
searches with zero results
space-only searches
normalization errors
recommendation errors
email failures
Celery heartbeat
LLM usage/cost if enabled
```

## 12. Sensitive admin access

Admin may need to download uploaded CVs for debugging and user support.

Requirement:

```text
CV download must be admin-only, served through a protected Django view/service, never through public media.
Every admin CV access must be logged.
```

No public CV URL is allowed.

For OAuth/GitHub/Gmail pictures:

```text
Do not build download/storage handling now unless there is a real product reason.
Store provider avatar URL only if needed.
Treat avatars as personal data.
Delete with account deletion.
```

## 13. Updated success metrics

Add these to existing product metrics:

```text
automatic ingestion target versus actual fetched jobs
public visible jobs count
public matchable jobs count
jobs hidden by eligibility reason
job freshness status counts
zero-skill job count
unknown skill candidate count
search zero-result rate
whitespace search count
CV parse success rate
CV parsed_with_warnings rate
name extraction acceptable accuracy
email extraction accuracy
phone extraction accuracy
skill precision
skill recall
false skill rate
match score explanation completeness
recommendation reason completeness
admin alert count by severity
```

## 14. Deferred business scope

Still deferred:

```text
payments
subscriptions
recruiter dashboard
training center dashboard
multi-country public filters
country dropdown/checkbox UI
mobile app
auto-apply
chatbot
salary prediction
legal immigration advice
AI-only scoring
bulk LLM ranking
enterprise admin hierarchy
```
