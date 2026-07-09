# Phase 15J Deployment Runbook Outline

Phase 15J is the actual deployment phase. Do not execute this during Phase 15I.

## Target architecture

- Hetzner VPS
- Caddy reverse proxy with HTTPS
- Gunicorn for Django
- PostgreSQL
- Redis
- Celery worker
- Celery Beat
- Whitenoise for static assets
- private media protected by Django

## High-level steps

1. Provision VPS.
2. Create deploy user.
3. Install system packages.
4. Install PostgreSQL and Redis or configure managed services.
5. Clone repository.
6. Create production `.env` manually.
7. Install Python dependencies.
8. Run migrations.
9. Build CSS.
10. Collect static.
11. Configure Gunicorn systemd.
12. Configure Celery worker systemd.
13. Configure Celery Beat systemd.
14. Configure Caddy.
15. Configure backups.
16. Configure monitoring.
17. Run production smoke tests.
18. Confirm private media is not public.
19. Confirm LLM automatic enrichment disabled.
20. Go/no-go decision.
