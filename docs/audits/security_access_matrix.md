# Security Access Matrix - Phase 14I

Audit date: 2026-06-18

Scope: current Phase 14I implementation only. Manual Chrome/admin signoff is still required before deployment acceptance.

## Matrix

| Area | Route | View name | Methods | Auth required | Owner-only | Staff/superuser | ID strategy | Mutation | CSRF | Service called | Automated coverage | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Public | `/` | `core:home` | GET | no | no | no | none | no | n/a | none | `test_public_pages_remain_public` | OK | Public landing page. |
| Public jobs | `/jobs/` | `jobs:list` | GET | no | no | no | local DB filters | no | n/a | `JobSearchService` | public route + external isolation tests | OK | Reads PostgreSQL only during user search. |
| Public jobs | `/jobs/<uuid:public_id>/` | `jobs:detail` | GET | no | no | no | UUID `public_id` | no | n/a | `JobQueryService`, `JobRevalidationService`, `SavedJobService` read | public UUID tests | OK | `/jobs/1/` returns 404. |
| Quick match | `/jobs/<uuid:public_id>/quick-match/` | `matching:quick_match` | POST | no | session scoped | no | job UUID `public_id` | yes | yes | `QuickMatchService` | dangerous GET test | OK | GET returns 405 and does not create a quick match. |
| Dashboard | `/dashboard/` | `dashboard:home` | GET | yes | current user | no | session user | no | n/a | none | private route tests | OK | Anonymous, logout, inactive-user paths covered. |
| Profile | `/dashboard/profile/` | `dashboard:profile` | GET/POST | yes | current user | no | session user | POST | yes | `ProfileUpdateService` | private route tests | OK | CV-derived suggestions use current user's active CV only. |
| CV manage | `/dashboard/cv/` | `dashboard:cv` | GET/POST | yes | current user | no | session user + CV UUID in POST | upload/delete on POST | yes | `CVUploadService`, `CVDeletionService` | CV privacy + dangerous GET tests | OK | Direct `file.url` not rendered; raw CV text not rendered. Original filename is displayed, not linked. |
| CV status HTMX | `/dashboard/cv/status/<uuid:public_id>/` | `dashboard:cv_status` | GET | yes | yes | no | CV UUID `public_id` | no | n/a | `CVUpload.objects` owner filter | two-user IDOR + HTMX tests | OK | User A gets 404 for user B's CV, including `HX-Request`. |
| Recommendations | `/dashboard/recommendations/` | `dashboard:recommendations` | GET | yes | current user | no | session user | refresh may be service-triggered | n/a | `RecommendationQueryService` | private route tests + external isolation tests | OK | No route accepts another user's ID. |
| Saved jobs page | `/dashboard/saved-jobs/` | `dashboard:saved_jobs` | GET | yes | current user | no | session user | no | n/a | `SavedJobService` | private route + two-user saved-job tests | OK | User A cannot see user B-only saved job. |
| Saved job mutation | `/jobs/<uuid:public_id>/save/` | `jobs:save` | POST | yes | current user | no | job UUID `public_id` | yes | yes | `SavedJobService` | anonymous + GET mutation tests | OK | GET returns 405. |
| Saved job mutation | `/jobs/<uuid:public_id>/unsave/` | `jobs:unsave` | POST | yes | current user | no | job UUID `public_id` | yes | yes | `SavedJobService` | two-user saved-job + GET mutation tests | OK | User A unsave does not delete user B's saved job. |
| Matching create | `/jobs/<uuid:public_id>/match/` | `matching:create` | POST | yes | current user | no | job UUID `public_id` | yes | yes | `MatchResultService` | dangerous GET + UUID tests | OK | GET returns 405. |
| Match history | `/dashboard/matches/` | `matching:history` | GET | yes | current user | no | session user | no | n/a | `MatchResultService` | private route tests | OK | Queryset filters by current user. |
| Match detail | `/dashboard/matches/<uuid:public_id>/` | `matching:detail` | GET | yes | yes | no | match UUID `public_id` | no | n/a | `MatchResultService` | two-user IDOR + UUID tests | OK | User A gets 404 for user B's match; `/dashboard/matches/1/` returns 404. |
| Email preferences | `/dashboard/email-preferences/` | `notifications:email_preferences` | GET/POST | yes | current user | no | session user | POST | yes | `EmailPreferenceService` | private route + ownership tests | OK | No user ID accepted in route or form. |
| Unsubscribe | `/email/unsubscribe/<uuid:token>/` | `notifications:unsubscribe` | GET/POST | no | token scoped | no | UUID token | POST only | yes | `EmailPreferenceService` | GET non-mutation + POST mutation tests | FIXED | Phase 14I fixed previous GET mutation. GET now renders confirmation only. |
| Account | `/dashboard/account/` | `dashboard:account` | GET | yes | current user | no | session user | no | n/a | none | private route tests | OK | Shows current user's deletion state only. |
| Social connections | `/dashboard/account/connections/` | `dashboard:connections` | GET/POST | yes | current user | no | signed token for social account | POST | yes | `SocialAccount` owner-filtered delete | existing social disconnect tests | OK | Raw social account ID is signed and owner-checked. |
| Account deletion | `/dashboard/settings/delete-account/` | `dashboard:delete_account` | GET/POST | yes | current user | no | session user | POST | yes | `AccountDeletionService` | dangerous GET tests | OK | GET does not deactivate user. |
| Deletion done | `/dashboard/settings/delete-account/done/` | `dashboard:delete_account_done` | GET | no | no | no | none | no | n/a | none | route matrix review | NEEDS_FOLLOW_UP | Public post-deletion confirmation; manual browser review required. |
| Legal | `/privacy/` | `privacy:privacy_policy` | GET | no | no | no | none | no | n/a | none | public route tests | OK | Public legal page. |
| Legal | `/terms/` | `privacy:terms` | GET | no | no | no | none | no | n/a | none | public route tests | OK | Public legal page. |
| Health | `/health/` | `health` | GET | no | no | no | none | no | n/a | `HealthCheckService` | public route + health tests | OK | Returns no secrets. |
| Admin | `/admin/` | Django admin | GET/POST | yes | n/a | staff/superuser | internal IDs allowed | yes | yes | admin actions/tasks/services | admin boundary tests | OK | Normal user denied; manual admin list review still required. |
| Allauth | `/accounts/*` | `allauth.urls` | GET/POST | route-dependent | session user | no | allauth internals | route-dependent | yes | django-allauth | existing account tests | OK | Manual OAuth browser signoff still required. |

## Integer ID Review

`grep -R "<int:" apps templates config -n` returned no matches. Internal integer IDs remain in Django model/admin/service code only, not in user-facing URL patterns for jobs, CVs, or matches.

## Manual Signoff Still Required

Human browser verification remains required for:

- `/admin/` model list/detail pages for sensitive field display.
- OAuth/account pages under `/accounts/`.
- End-to-end Chrome checks from `docs/phases/phase_14i_security_access_control_audit/manual_browser_security_signoff.md`.

Current allowed pre-signoff verdict: `FINAL_VERDICT: BLOCKED_HUMAN_SECURITY_SIGNOFF`.
