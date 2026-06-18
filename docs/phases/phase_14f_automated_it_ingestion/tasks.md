# Tasks — Phase 14F

## TTA-14F-001 — Add ingestion config models

- Add `JobIngestionConfig`.
- Add `JobIngestionRun`.
- Add migrations.
- Register in Django admin.
- Defaults:
  - `limit_per_keyword=50`
  - `max_total_per_run=1000`
  - `nightly_max_total=2000`
  - `enqueue_enrichment=True`
  - `enrich_every_fetched_it_job=True`

## TTA-14F-002 — Add broad IT preset service

- Add `broad_it` keyword preset.
- Include development, data, DevOps, cloud, cyber, QA, support, systems, DBA, ERP/CRM, project/product, internship/apprenticeship terms.
- Make preset testable.

## TTA-14F-003 — Add broad IT sync service

Create service such as:

```python
JobIngestionService.run(config, trigger, overrides)
```

Must:

- Call France Travail client only from service/management command/task, not views.
- Paginate per keyword.
- Enforce visible limits.
- Deduplicate by source job ID.
- Save/update raw job records.
- Normalize fetched jobs.
- Record run counts.

## TTA-14F-004 — Add management command

Command:

```bash
python manage.py sync_france_travail_it_jobs --preset broad_it --limit-per-keyword 50 --max-total 1000 --normalize --enqueue-enrichment
```

Options:

- `--config default`
- `--preset broad_it`
- `--limit-per-keyword N`
- `--max-total N`
- `--max-pages-per-keyword N`
- `--normalize`
- `--enqueue-enrichment`
- `--no-enrichment`
- `--expire-stale`
- `--dry-run`

## TTA-14F-005 — Queue enrichment for every fetched IT job by default

For each fetched active normalized job:

- Check likely IT/enrichment eligibility.
- If eligible and unchanged enrichment does not already exist, enqueue enrichment.
- If sync command is run with `--sync-enrichment` for local testing, process small enrichment synchronously only if explicitly requested.
- Respect `enrichment_limit_per_run`.

## TTA-14F-006 — Add stale/expired job cleanup

Implement `JobExpiryService`.

Rules:

- Mark jobs inactive/stale if not seen for configured days.
- Do not hard delete by default.
- Public search/recommendations must exclude inactive/stale jobs.
- Add command or command option to run expiry.

## TTA-14F-007 — Add Celery task and scheduler-ready setup

- Add `run_it_job_ingestion` Celery task.
- Optionally add Celery Beat config if existing project already uses beat.
- Document Render Cron command if not using Beat.
- Do not require paid Render features.

## TTA-14F-008 — Admin controls

- Register config/run models.
- Add admin actions if safe.
- Admin can change limits/frequency/enrichment/expiry.
- Admin can start a manual run without blocking a huge web request.

## TTA-14F-009 — Tests

Add tests for:

- default config values.
- broad preset contains broad IT families.
- command respects `limit_per_keyword=50` and `max_total=1000`.
- no hidden cap of 10 in new command.
- pagination stops at max limits.
- deduplication by source job ID.
- normalization called.
- enrichment queued for every fetched eligible IT job by default.
- non-IT false positives do not get recommended.
- stale jobs expire.
- admin config can reduce frequency/limits.
- no live API calls from views.

## TTA-14F-010 — Agent report

Write `docs/phases/phase_14f_automated_it_ingestion/agent_report.md` with required evidence.
