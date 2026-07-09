# TuniAtlas v1.1 Post-Launch Planning Pack

Status: Draft baseline for post-launch hardening  
Project: TuniAtlas, formerly TuniTech Abroad  
Purpose: Restore clear direction after deployment and prevent phase drift

## 1. How to use this pack

Keep the original v1 planning PDFs. They are the historical source of truth for the MVP build. Do not delete them and do not pretend they never existed.

Add this v1.1 pack as a post-launch addendum:

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

The original v1 documents remain in:

```text
docs/planning/
  BRD_v1.pdf
  PRD_v1.pdf
  Technical_Architecture_v1.pdf
  Database_Schema_v1.pdf
  Service_Contracts_v1.pdf
  Data_Flow_Sequence_Diagrams_v1.pdf
  Page_URL_View_Map_v1.pdf
  Implementation_Roadmap_v1.pdf
  MVP_Backlog_v1.pdf
  Repository_Setup_Plan_v1.pdf
```

## 2. v1 versus v1.1 rule

v1 is the MVP foundation.  
v1.1 is the post-launch correction layer.

v1 answers:

```text
What is the product?
What is the approved stack?
What are the core models/services/pages?
How should the MVP be built phase by phase?
```

v1.1 answers:

```text
What did production reveal?
What must be hardened after launch?
How do we improve CV parsing, skills, matching, search, ingestion, and admin monitoring?
How do we prepare for future ML without rebuilding the system later?
```

When v1 and v1.1 conflict, use this rule:

```text
Use v1 for original architecture boundaries.
Use v1.1 for post-launch priorities, quality requirements, admin monitoring, ingestion diagnostics, and public copy direction.
```

Do not use v1.1 to justify stack changes. The stack remains Django, PostgreSQL, Redis, Celery, django-allauth, Django templates, HTMX, Tailwind CSS, and controlled OpenRouter usage.

## 3. Current post-launch reality

The site is live. Production revealed these priorities:

1. OAuth and HTTPS awareness must be correct.
2. Public domain canonicalization must be stable.
3. Job ingestion must explain why production shows fewer jobs than manual runs.
4. Search must handle empty/space queries, company filters, and date filters.
5. Public UI should not market the product as France-only, even if France remains the hidden default source/country for now.
6. CV parsing quality is a core product risk. A friend’s CV produced a wrong name detection: `je me suis`.
7. Skill matching depends on canonical taxonomy and aliases. `.NET Core`, `dotnet`, `.NET`, `ASP.NET Core`, and related forms must be handled intentionally.
8. Matching score and recommendation explanation must remain deterministic and explainable.
9. Admin monitoring must support a solo founder/operator, not a fake enterprise admin hierarchy.
10. ML/DL is deferred, but the system must collect correction labels and use taxonomy as the stable future ML label space.

## 4. Hard architecture rules still active

These rules remain non-negotiable:

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
CVUpload.objects must exclude soft-deleted CVs.
CVUpload.all_objects is only for admin/privacy/deletion/internal tasks.
LLM can extract, explain, and suggest, but cannot decide the final fit score.
No React, Next.js, Angular, FastAPI, MongoDB, SQLAlchemy, or SPA architecture.
```

## 5. Post-launch phase order

Use this order:

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

Do not implement all phases in one agent run. One phase at a time.

## 6. Solo-admin operating model

The current project has one admin/operator/developer/designer: Baha.

So admin scope must be practical:

```text
owner/superuser dashboard
staff-only admin ops
no multi-role hierarchy
no team permissions
no reviewer workflow
no organization admin model
sensitive file access logged
future RBAC deferred
```

## 7. ML/DL decision

Do not build ML/DL now.

Build this now:

```text
canonical skill taxonomy
skill aliases
skill relationships later
CV parser audit corpus
parser metrics
user/admin corrections
skill extraction feedback
job quality feedback
deterministic scoring
confidence thresholds
```

This is not double work. It is the ML foundation.

Future ML will plug into the same data model:

```text
Raw CV/job text
-> ML extractor predicts canonical Skill IDs + confidence
-> taxonomy validates result
-> ProfileSkill / NormalizedJobSkill rows are saved
-> MatchScoringService calculates deterministic score
```

The taxonomy is the label space for future ML. It must not be demolished later.
