# Phase 14H-B — Celery Beat Schedule + Operational Automation

## Purpose

Make TuniTech Abroad self-maintaining in local and production-like environments by registering safe periodic Celery Beat tasks for ingestion, stale job cleanup, recommendation refresh, and privacy cleanup.

This phase follows Phase 14H-A audit safety fixes. It must not introduce Tailwind production build changes, deployment changes, or new product features.

## Core outcome

After this phase:

- `CELERY_BEAT_SCHEDULE` is no longer empty.
- Operational tasks are scheduled with safe defaults.
- The schedule can be inspected in tests and locally.
- Public job search still reads only PostgreSQL.
- Celery tasks still delegate to services only.
- No LLM or France Travail calls are made from Django views.

## Phase boundary

This is an operational automation phase, not a UI redesign, not deployment, and not Tailwind build setup.
