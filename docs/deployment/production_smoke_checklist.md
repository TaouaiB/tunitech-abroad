# Production Smoke Checklist

Run this checklist manually immediately after deploying to production.

## Public & Auth
- [ ] Homepage loads successfully without 500 errors.
- [ ] Standard Login / Logout flow works.
- [ ] Google OAuth login works.
- [ ] GitHub OAuth login works.
- [ ] Sign-up flow completes.

## Job Browsing
- [ ] Jobs list loads fast.
- [ ] Search and filtering functional.
- [ ] Job detail page loads.
- [ ] "Plus pertinentes" (if implemented/applicable) displays correctly.

## Candidate Features
- [ ] CV Upload succeeds (verifies `PRIVATE_MEDIA_ROOT` permissions).
- [ ] Quick Match triggers and returns a result without crashing.
- [ ] User Profile page loads and shows uploaded CVs.
- [ ] User can successfully delete a CV.
- [ ] Job Recommendations page loads.
- [ ] Saving and Unsaving a job updates the UI and database.

## Operations & Background Tasks
- [ ] Web health endpoint (`/health/` or similar) returns a 200 OK.
- [ ] Celery heartbeat is recent (check admin or logs).
- [ ] Run a manual job ingestion command (or dry-run via admin) and verify it succeeds.
- [ ] Admin operations dashboard loads for staff users.

## Privacy & Security
- [ ] Direct access to a CV file path returns 404 or 403, confirming private media is not exposed by the web server.
- [ ] Email unsubscribe links work.
- [ ] No LLM token burn occurs during standard flows unless explicitly enabled via environment variables.
