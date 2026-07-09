# TuniAtlas Project Context for New ChatGPT Conversations — v1.1

Use this file when starting a new conversation about TuniAtlas after deployment.

## 1. Identity

Public product:

```text
TuniAtlas
TuniAtlas Jobs
Tech careers abroad for Tunisian talent
```

Historical/internal project name:

```text
TuniTech Abroad
```

Do not rebrand repo/folders casually unless explicitly planned.

## 2. Product

TuniAtlas is a job intelligence platform for Tunisian IT candidates, students, bootcamp graduates, internship seekers, and junior/mid-level developers.

It is not a generic job board.

Core loop:

```text
Tunisian IT profile
-> jobs/internships abroad, currently default France source
-> CV/profile parsing
-> canonical skills
-> deterministic job matching
-> missing skill detection
-> recommendations
-> optional LLM explanations
```

The strength of the website must be:

```text
CV parsing quality
skill detection quality
skill alias/taxonomy quality
matching score quality
missing skill explanation
recommendation quality
job ingestion/search quality
admin visibility
```

## 3. Approved stack

Use only:

```text
Django
Django ORM
PostgreSQL
Redis
Celery
Celery Beat
django-allauth
Django templates
HTMX
Tailwind CSS
Alpine.js only where needed
OpenRouter for controlled optional LLM
PyMuPDF/pdfplumber for CV text extraction
```

Do not use:

```text
React
Next.js
Angular
FastAPI
MongoDB
SQLAlchemy
SPA architecture
```

## 4. Architecture rules

```text
Views stay thin.
Business logic goes in services.
Celery tasks call services only.
Models store data and do not call external APIs.
No OpenRouter/LLM calls from Django views.
No France Travail live API calls during normal user job search.
User job search reads local PostgreSQL only.
Public URLs use UUID public_id, never internal integer IDs.
CV files are private and must not be publicly exposed.
CVUpload.objects excludes soft-deleted CVs.
CVUpload.all_objects is only for admin/privacy/deletion/internal tasks.
LLM can extract, explain, and suggest, but cannot decide the final fit score.
```

## 5. Production context

The website has been running publicly for a few days.

Known production/post-launch topics:

```text
Google OAuth redirect_uri_mismatch was caused by www versus non-www mismatch.
Caddy canonical redirect was fixed: www.tuniatlas.com -> tuniatlas.com.
Django HTTPS awareness still needed repo-level production settings fix if not already done.
Real service name is tuniatlas.service, not tuniatlas-web.service.
Normal bot scanning observed in logs.
No crash/OOM/500 outage found in reviewed logs.
```

Pending/fixed depending on current repo state:

```text
SECURE_PROXY_SSL_HEADER
ACCOUNT_DEFAULT_HTTP_PROTOCOL
SECURE_SSL_REDIRECT
SESSION_COOKIE_SECURE
CSRF_COOKIE_SECURE
```

## 6. New v1.1 planning docs

Add these to the repo:

```text
docs/planning/post_launch/
  README_v1_1_Index.md
  BRD_v1_1_TuniAtlas_Post_Launch_Addendum.md
  PRD_v1_1_Product_Intelligence_Quality.md
  Technical_Architecture_v1_1_Local_Intelligence.md
  Database_Schema_v1_1_Quality_Admin_Monitoring.md
  Service_Contracts_v1_1_Quality_Services.md
  Implementation_Roadmap_v1_1_Post_Launch.md
  Project_Context_For_ChatGPT_v1_1.md
```

Do not replace original v1 PDFs.

## 7. Post-launch phase order

```text
16A — Production Stabilization
16B — Job Ingestion, Freshness, Search, and Country-Neutral UI Hardening
16C — CV Parser Quality Framework
16D — Skill Taxonomy and Alias Accuracy
16E — Job Skill Extraction and Data Quality
16F — Matching and Recommendation Accuracy
16G — Admin Monitoring and Alerts
16H — UI/UX Decision System
16I — Email Professionalization
16J — Future ML/LLM Platform
```

## 8. Current strategic decisions

### 8.1 No timeline blocks

Do not say “week 1, week 2.” Use ordered steps/phases only.

### 8.2 Country-neutral public UI

Remove public copy that markets the product as France-only.

Keep France where it is actual data:

```text
job address/location
France Travail source in admin/internal config
backend hidden default country/source
internal docs
```

Do not build multi-country selector now.

### 8.3 Job ingestion issue

Need to diagnose:

```text
Why automatic production ingestion shows around 100–200 jobs when manual ingestion previously fetched around 1,000.
```

Add:

```text
diagnose_job_ingestion command
admin configurable target_daily_fetch_count, default 1000
query-level ingestion runs
freshness/expiry hardening
public visible/matchable funnel counts
```

### 8.4 Search hardening

Add search support for:

```text
empty query
whitespace-only query
company name
published exact date
published min/max date
invalid date handling
skill aliases
pagination edge cases
```

Whitespace-only search must behave like no query and show active jobs.

### 8.5 CV parser quality

Observed bug:

```text
A friend’s CV detected name as "je me suis".
```

Rule:

```text
Wrong empty is acceptable.
Wrong confident value is not acceptable.
```

Add:

```text
CVNameExtractionService
parser confidence/warnings
private 100+ CV audit corpus
audit_cv_parser command
parser metrics
regression loop
```

Do not commit real CVs.

### 8.6 Skill taxonomy

Taxonomy is not throwaway work.

It is the stable label space for:

```text
current deterministic matching
future ML extraction
future model evaluation
```

`.NET Core`, `.NET`, `dotnet`, `ASP.NET Core`, `C#`, `Node.js`, `PostgreSQL`, etc. must be handled through canonical Skill + SkillAlias and later optional SkillRelation.

### 8.7 ML decision

Do not build ML/DL now.

Build:

```text
taxonomy
aliases
parser audit corpus
correction data
skill feedback labels
job feedback labels
deterministic matching
```

Future ML should predict canonical Skill IDs + confidence. It must not replace deterministic scoring.

### 8.8 Solo-admin model

Baha is the only admin/operator/developer/designer now.

Build:

```text
owner/superuser dashboard
staff-only admin operations
sensitive file access logging
admin alert emails
admin diagnostics
```

Do not build:

```text
multi-role admin hierarchy
reviewer/moderator workflow
team permissions
organization accounts
```

## 9. Commands likely needed in future phases

```bash
python manage.py diagnose_job_ingestion --settings=config.settings.production
python manage.py audit_job_search --settings=config.settings.production
python manage.py audit_public_copy --settings=config.settings.local
python manage.py audit_cv_parser --cv-dir private_test_corpus/cvs --expected-dir private_test_corpus/expected --output private_test_corpus/reports/latest.csv --settings=config.settings.local
python manage.py audit_skill_aliases --settings=config.settings.local
python manage.py rematerialize_job_skills --settings=config.settings.production
python manage.py rebuild_job_search_vectors --settings=config.settings.production
python manage.py inspect_public_job_eligibility --settings=config.settings.production
```

## 10. Review checklist for generated code

When reviewing agent output, check:

```text
Did it stay inside current phase?
Did it use approved stack only?
Are views thin?
Is business logic in services?
Do Celery tasks call services only?
Are migrations reasonable?
Are tests present?
Are public routes using UUID public_id?
Are CV files private?
Is CVUpload.objects safe?
Are secrets protected?
Did it avoid public France-only marketing copy?
Did it avoid fake ML/LLM authority?
Did it avoid overbuilding admin roles?
Did it add diagnostics instead of guessing?
Did it avoid committing private test CVs?
```
