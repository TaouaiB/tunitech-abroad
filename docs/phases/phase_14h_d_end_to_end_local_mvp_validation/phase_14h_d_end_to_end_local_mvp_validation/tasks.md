# Tasks

## Task 1 — Repository and environment sanity

- Confirm current branch and uncommitted files.
- Confirm Phase 14H-C changes are committed before starting.
- Confirm Python/Django check passes.
- Confirm no missing migrations.
- Confirm Tailwind CSS build works.
- Confirm collectstatic dry-run works.

## Task 2 — Anonymous user flow

Validate in browser:

- `/` loads and is styled.
- `/jobs/` loads from local PostgreSQL.
- Job filters work enough to update results.
- Job detail loads using UUID public URL.
- No integer-ID public job detail URL is used.
- No France Travail live API call occurs from public job search.

## Task 3 — Authenticated dashboard flow

Use a disposable test account.

Validate:

- Signup/login works.
- Dashboard loads.
- Profile page loads.
- Profile can be edited.
- Account connections page loads.
- Email preferences page loads.

## Task 4 — CV upload and worker flow

With Redis and Celery worker running:

- Upload a test PDF CV.
- Confirm upload zone shows selected file name and size before submit.
- Confirm submit state changes to upload/progress state.
- Confirm CV status moves from queued/processing to parsed or parsed_with_warnings.
- Confirm `cv_worker_check` is useful and does not falsely report the newest CV as stuck.
- Confirm no public CV file URL appears.
- Confirm raw extracted text is not visible in templates.

## Task 5 — Job ingestion/enrichment smoke

Run a small safe ingestion smoke:

```bash
python manage.py sync_france_travail_it_jobs \
  --preset broad_it \
  --limit-per-keyword 2 \
  --max-total 10 \
  --normalize \
  --enqueue-enrichment \
  --settings=config.settings.local
```

Record:

- fetched count
- normalized count
- enrichment queued/skipped count
- errors

If OpenRouter is not configured or LLM is disabled, record that and do not force real LLM spend.

## Task 6 — Matching and recommendations flow

Validate:

- Job match can be generated for a logged-in user.
- Match detail loads with UUID public_id.
- Score is displayed and remains deterministic/rule-based.
- Missing skills display makes sense.
- Recommendations page loads.
- Saved jobs work: save and unsave a job.
- No user can access another user's match/recommendation objects.

## Task 7 — Privacy/account deletion flow

Use a disposable user only.

Validate:

- Email preferences page loads.
- Account deletion confirmation flow works safely.
- Deletion does not expose secrets or CV files.
- User-owned CVs are soft-deleted or removed according to existing privacy services.

If the flow is destructive, do it only on a new disposable local test user.

## Task 8 — Regression/security checks

Run all required automated checks and greps from `regression_security_checks.md`.

## Task 9 — Report

Create/update:

```text
docs/validation/local_mvp_e2e_report.md
```

Include:

- Date/time
- Commit/branch
- Services running
- Pages tested
- Commands run
- Results
- Bugs found
- Bugs fixed
- Remaining manual/visual risks
- Final verdict
