# Manual Deployment Checklist

Follow this checklist when actually deploying to production:

- [ ] Connect to VPS via SSH as root.
- [ ] Create `tunitech` user and add to sudoers.
- [ ] Install system packages (PostgreSQL, Redis, Caddy, Python).
- [ ] Clone repository as `tunitech` user.
- [ ] Create Python virtual environment and install dependencies.
- [ ] Setup production `.env` securely without committing it.
- [ ] Apply database migrations.
- [ ] Run `collectstatic`.
- [ ] Setup Gunicorn, Celery worker, and Celery beat systemd services.
- [ ] Configure Caddy and enable HTTPS.
- [ ] Verify application health.
