# Phase 14G — CV Processing Status UX + Worker Reliability

## Goal
Make CV upload/parsing feel reliable and understandable in local MVP usage.

The user must never be left staring at a vague `pending` state with no explanation. The app should clearly show upload progress, queued state, processing state, completion, and failure/retry guidance.

## Why this phase exists
During local testing, CV upload appeared stuck forever in `pending`. The root operational cause was that the Celery worker was not running, but the product problem remains: the UI does not explain what is happening or whether the worker is alive.

## Phase boundary
This phase is only about CV processing status UX and worker reliability.

Do not implement new matching logic, new LLM extraction behavior, new recommendation scoring, deployment automation, or broad UI redesign.

## Required stack boundaries
- Django views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- No OpenRouter calls from Django views.
- CV files remain private.
- Public URLs use UUID `public_id`, never internal integer IDs.
- `CVUpload.objects` must exclude soft-deleted CVs.
- `CVUpload.all_objects` is only for admin/privacy/deletion/internal tasks.
