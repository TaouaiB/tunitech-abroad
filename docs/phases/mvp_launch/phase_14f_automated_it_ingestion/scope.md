# Scope — Phase 14F

## In scope

Build automated broad IT job ingestion from France Travail into local PostgreSQL.

Phase 14F must add:

1. A dedicated broad IT sync command.
2. Admin-configurable ingestion settings.
3. Broad IT keyword preset.
4. Pagination and deduplication.
5. No hidden cap of 10 in the new command.
6. Safe visible limits:
   - default `limit_per_keyword = 50`
   - default `max_total_per_run = 1000`
   - default nightly max total `2000`
7. Normalize fetched jobs.
8. Queue enrichment for every fetched active IT job by default.
9. Expire stale/closed jobs automatically.
10. Store ingestion run logs.
11. Manual admin/management command trigger.
12. Celery task and scheduler-ready design.
13. Tests and verification.

## Out of scope

Do not implement a polished admin dashboard beyond Django admin unless trivial.
Do not redesign the public UI.
Do not change final match scoring logic except to ensure enriched data is used when already available.
Do not build Phase 14G.
Do not deploy.
Do not commit.

## Important distinction

Do not fetch every job from France Travail. Fetch broad IT jobs only, using a large keyword/role-family preset, ROME/category signals where available, deduplication, and eligibility filters.

User-facing job search must remain local PostgreSQL only.
