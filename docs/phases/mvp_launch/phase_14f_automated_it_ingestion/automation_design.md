# Automation Design

## Local manual mode

Add a command:

```bash
python manage.py sync_france_travail_it_jobs \
  --preset broad_it \
  --limit-per-keyword 50 \
  --max-total 1000 \
  --normalize \
  --enqueue-enrichment \
  --settings=config.settings.local
```

Also support:

```bash
python manage.py sync_france_travail_it_jobs --config default --settings=config.settings.local
python manage.py sync_france_travail_it_jobs --dry-run --settings=config.settings.local
```

## Nightly mode

Support a nightly option:

```bash
python manage.py sync_france_travail_it_jobs \
  --preset broad_it \
  --limit-per-keyword 50 \
  --max-total 2000 \
  --normalize \
  --enqueue-enrichment \
  --settings=config.settings.production
```

Default nightly max total is 2000.

## Celery task

Add task like:

```python
@shared_task
def run_it_job_ingestion(config_id=None, trigger="celery"):
    return JobIngestionService.run_from_config(config_id=config_id, trigger=trigger)
```

Tasks call services only.

## Scheduler-ready

If project uses Celery Beat, add an optional schedule guarded by config/settings. If not, document Render Cron command.

Render Cron command can run:

```bash
python manage.py sync_france_travail_it_jobs --config default --settings=config.settings.production
```

## Enrichment automation

Default behavior:

- Every fetched + active + normalized + likely IT job queues enrichment.
- If a job has successful enrichment for same payload hash, skip.
- If enrichment is pending/processing, skip duplicate enqueue.
- If enrichment previously failed and payload changed, allow retry.
- Respect `enrichment_limit_per_run` and daily OpenRouter limits from Phase 14D.

## Expiry automation

Add command/service:

```bash
python manage.py expire_stale_jobs --days 21 --settings=config.settings.local
```

or integrate expiry into the ingestion command when `--expire-stale` is passed.

Rules:

- Do not hard-delete jobs by default.
- Mark inactive/stale/expired.
- Hide inactive jobs from public search and recommendations.
- Keep raw records for audit/debug.
