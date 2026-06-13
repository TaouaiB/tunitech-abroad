# AGENTS.md — TuniTech Abroad Agent Rules

## 1. Project Identity

TuniTech Abroad is a France-first job intelligence platform for Tunisian IT candidates, students, bootcamp graduates, internship seekers, and junior/mid-level developers.

Product loop:

Tunisian IT profile -> France IT jobs/internships -> CV/profile parsing -> job matching -> missing skill detection -> recommendations.

This is not a generic job board. It is a job intelligence and matching product.

## 2. Source of Truth

Use the planning PDFs in `docs/planning/` as source of truth:

- BRD v1
- PRD v1
- Technical Architecture v1
- Database Schema v1
- Service Contracts v1
- Data Flow / Sequence Diagrams v1
- Page + URL + View Map v1
- Implementation Roadmap v1
- MVP Backlog v1
- Repository Setup Plan v1
- Working Agreement v1

When a phase file conflicts with a broader planning document, obey the current phase file and the rules in this `AGENTS.md`. Do not silently expand the scope.

## 3. Locked Stack

Use:

- Django
- Django ORM
- PostgreSQL
- Redis
- Celery
- Celery Beat
- django-allauth, starting Phase 1
- Django templates
- HTMX
- Tailwind CSS
- Alpine.js only where needed
- OpenRouter for controlled LLM usage, starting Phase 9
- PyMuPDF/pdfplumber for CV text extraction, starting Phase 6

Do not use:

- React
- Next.js
- Angular
- FastAPI
- Flask
- MongoDB
- SQLAlchemy
- Prisma
- SPA architecture
- Meilisearch
- Elasticsearch
- live France Travail API calls during normal user job search

## 4. Architecture Rules

- Build a modular Django monolith.
- Views stay thin.
- Business logic goes in services.
- Celery tasks call services only.
- Models store data and do not call external APIs.
- No OpenRouter or LLM calls from Django views.
- No France Travail live API calls during normal user job search.
- User job search reads local PostgreSQL only.
- Public URLs use UUID `public_id`, never internal integer IDs.
- CV files are private and must not be publicly exposed.
- `CVUpload.objects` must exclude soft-deleted CVs.
- `CVUpload.all_objects` is only for admin/privacy/deletion/internal tasks.
- LLM can extract, explain, and suggest, but cannot decide or modify the final fit score.

## 5. Phase Boundary Rule

Work only inside the current phase.

The agent may complete all tickets inside the current phase automatically. The agent must not start the next phase unless Baha explicitly asks.

Wrong:

- Implement auth during Phase 0.
- Implement job models during Phase 0.
- Implement CV upload during Phase 0.
- Add LLM integration before Phase 9.
- Add email delivery before Phase 10.
- Add production deployment before Phase 14.

## 6. Phase Order

- Phase 0: Repository and local environment
- Phase 1: Django foundation and authentication
- Phase 2: Core models and admin
- Phase 3: Skill taxonomy
- Phase 4: Job ingestion and normalization
- Phase 5: Public job search and pages
- Phase 6: CV/profile
- Phase 7: Matching and quick match
- Phase 8: Recommendations and saved jobs
- Phase 9: OpenRouter LLM support
- Phase 10: Email notifications
- Phase 11: Privacy deletion
- Phase 12: Admin and observability
- Phase 13: MVP polish
- Phase 14: Deployment

## 7. Secrets Rule

Create `.env.example` only.

Never create, commit, print, log, or document real secrets.

`.env` must be gitignored.

Use environment variables for secrets and runtime configuration. Baha will create `.env` manually.

Minimum `.gitignore` protection:

```gitignore
.env
.env.*
!.env.example
```

Do not print secret values in:

- terminal output
- README
- reports
- tests
- logs
- error messages
- screenshots

## 8. Docker Rule

Use Docker Compose only for PostgreSQL and Redis at the beginning.

Do not Dockerize the Django web app in early phases.

Run locally:

- Django server
- Celery worker
- Celery Beat
- Tailwind watcher

Allowed Docker Compose services in Phase 0:

- `postgres`
- `redis`

Do not create a Django web container unless Baha explicitly asks later.

## 9. Git Workflow

Keep branching simple:

- `main` = stable
- `dev` = active work

Do not code directly on `main`.

After a phase is stable and reviewed:

```bash
git checkout dev
git add .
git commit -m "Complete Phase 0 repository foundation"

git checkout main
git merge dev
git push origin main

git checkout dev
git push origin dev
```

## 10. Fedora/Linux Assumption

Use Fedora/Linux/bash commands by default.

Use `dnf` for system packages if needed.

Do not provide Windows PowerShell commands unless Baha explicitly asks.

## 11. Testing and Checks

After each logical block, run the relevant checks. If a check fails, fix it and rerun.

At the end of every phase, provide:

1. completed tickets
2. files created/changed
3. commands run
4. final check results
5. remaining risks/manual steps

## 12. Review Package Expected by ChatGPT

When the phase is complete, provide:

- Agent final report
- Git diff or changed file list
- Important files content, especially settings, services, tasks, views, tests
- Terminal output of checks/tests
- Errors encountered and fixes applied
- Remaining risks/manual steps
