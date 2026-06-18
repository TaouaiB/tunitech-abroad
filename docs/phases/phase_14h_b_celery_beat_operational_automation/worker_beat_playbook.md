# Worker + Beat Local Playbook

## Redis

```bash
cd ~/Projects/tunitech-abroad
# If Redis already runs on 6380, do not start another container.
docker compose ps
# If not running:
docker compose up -d redis
```

If port 6380 is already in use but Celery connects successfully, do not fight it during this phase.

## Django

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
python manage.py runserver --settings=config.settings.local
```

## Celery worker

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
celery -A config worker --loglevel=info --concurrency=2
```

## Celery Beat

Run in foreground for local testing:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate
celery -A config beat --loglevel=info
```

Stop with `Ctrl+C`.

## What to look for

- Beat starts without import errors.
- Beat logs show scheduled tasks.
- Worker receives due tasks when schedule triggers.
- No runaway repeated task loop.
- Ingestion task respects config limits.

## Inspecting Logs

- For the worker, watch the terminal where `celery -A config worker ...` is running. Look for `Task <task_name>[<task_id>] received` and `Task <task_name>[<task_id>] succeeded`.
- For Beat, watch the terminal where `celery -A config beat ...` is running. Look for `Scheduler: Sending due task <task_name>`.
- Any exceptions or stack traces will appear in the worker's terminal output.

## How to stop tasks safely

- If a task is misbehaving, stop the Celery Worker process with `Ctrl+C`. The worker will finish the current task (warm shutdown) before exiting. Use `Ctrl+C` twice for a cold/immediate shutdown (not recommended).
- Stop the Celery Beat process with `Ctrl+C` to halt future task scheduling.
- If you need to purge the queue (remove all pending tasks), run:
  ```bash
  celery -A config purge
  ```
