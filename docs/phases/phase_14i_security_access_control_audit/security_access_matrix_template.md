# Security Access Matrix Template — Phase 14I

Create the final matrix at:

```text
docs/audits/security_access_matrix.md
```

Use this structure.

## Legend

```text
AUTH_PUBLIC = accessible anonymously
AUTH_USER = authenticated user required
OWNER_ONLY = authenticated owner required
STAFF = staff/admin required
SUPERUSER = superuser required
MUTATION = changes state
SAFE_READ = no state change
```

## Matrix

| Area | Route | View name | Methods | Auth rule | Owner rule | ID strategy | Mutation? | CSRF? | Service called | Tests | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Public | `/` | `core:home` | GET | AUTH_PUBLIC | none | none | no | n/a | optional analytics | yes/no | OK/FIXED/FOLLOW_UP | |
| Public | `/jobs/` | `jobs:list` | GET | AUTH_PUBLIC | none | local DB only | no | n/a | JobSearchService | yes/no | OK/FIXED/FOLLOW_UP | must not call France Travail |
| Public | `/jobs/<uuid:public_id>/` | `jobs:detail` | GET | AUTH_PUBLIC | none | UUID public_id | no | n/a | JobQueryService | yes/no | OK/FIXED/FOLLOW_UP | |
| Dashboard | `/dashboard/` | `dashboard:home` | GET | AUTH_USER | current user only | session user | no | n/a | dashboard services | yes/no | OK/FIXED/FOLLOW_UP | |
| CV | `/dashboard/cv/` | `dashboard:cv` | GET/POST | AUTH_USER | current user only | session user/public_id | POST upload/delete | yes | CVUploadService/CVDeletionService | yes/no | OK/FIXED/FOLLOW_UP | no file.url |
| CV | `/dashboard/cv/status/<uuid:public_id>/` | `dashboard:cv_status` | GET | AUTH_USER | OWNER_ONLY | UUID public_id | no | n/a | CV query/status service | yes/no | OK/FIXED/FOLLOW_UP | HTMX |
| Matching | `/dashboard/matches/<uuid:public_id>/` | `matching:detail` | GET | AUTH_USER | OWNER_ONLY | UUID public_id | no | n/a | MatchQueryService | yes/no | OK/FIXED/FOLLOW_UP | |
| Matching | `/dashboard/matches/<uuid:public_id>/explain/` | `matching:explain` | POST | AUTH_USER | OWNER_ONLY | UUID public_id | yes | yes | MatchExplanationService | yes/no | OK/FIXED/FOLLOW_UP | no direct LLM in view |
| Recommendations | `/dashboard/recommendations/` | `dashboard:recommendations` | GET/POST/HTMX | AUTH_USER | current user only | session user | possible refresh | yes if POST | Recommendation services | yes/no | OK/FIXED/FOLLOW_UP | |
| Saved jobs | `/dashboard/saved-jobs/` | `dashboard:saved_jobs` | GET/POST | AUTH_USER | current user only | UUID public_id for jobs | yes if remove | yes | SavedJobService | yes/no | OK/FIXED/FOLLOW_UP | |
| Email | `/dashboard/email-preferences/` | `dashboard:email_preferences` | GET/POST | AUTH_USER | current user only | session user/token for unsubscribe | yes | yes | EmailPreferenceService | yes/no | OK/FIXED/FOLLOW_UP | |
| Privacy | `/dashboard/account/` or deletion route | account/delete flow | GET/POST | AUTH_USER | current user only | session user/signed token | yes if request/delete | yes | AccountDeletionService | yes/no | OK/FIXED/FOLLOW_UP | |
| Admin | `/admin/` | Django Admin | GET/POST | STAFF/SUPERUSER | n/a | internal IDs allowed | yes | yes | admin/services | yes/no | OK/FIXED/FOLLOW_UP | no secrets/raw CV text |
| Health | `/health/` | `core:health` | GET | deployment-dependent | none | none | no | n/a | HealthCheckService | yes/no | OK/FIXED/FOLLOW_UP | no secrets |

Add all project-specific routes not listed here.
