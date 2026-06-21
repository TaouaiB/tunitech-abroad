# Monitoring & Health Checks Plan

This document outlines the observability and health monitoring strategy for the initial production deployment. Do not integrate paid monitoring tools initially. Use simple, effective MVP steps.

## Required Checks

### 1. Web / App Tier
- **Web health endpoint**: A dedicated route (e.g., `/health/`) returning a 200 OK. It should verify basic DB connectivity.
- **Gunicorn status**: Monitored via systemd (`systemctl status tunitech-web`).

### 2. Background Processing
- **Celery worker status**: Checked via systemd and Celery ping.
- **Celery beat status**: Checked via systemd.
- **Celery heartbeat freshness**: Ensure a periodic task updates a cache key, verifying the worker pool is alive and processing tasks.

### 3. Data Infrastructure
- **Redis availability**: Verified by the web health endpoint and Django cache checks.
- **PostgreSQL connectivity**: Verified by the web health endpoint.
- **Disk usage**: Monitored at the OS level (e.g., standard Hetzner metrics or simple cron scripts checking `df -h`).

### 4. Application Metrics (Logs & Admin Dashboard)
- **Ingestion success/failure**: Monitored via the admin `JobIngestionRun` models.
- **Queue / Pending / Stale processing counts**: Viewed in the admin operations dashboard.
- **Backup success/failure**: Check cron logs or basic email alerts.
- **Error logs**: Django logging configured to output warnings/errors, captured by `journalctl`.

## Future Options
- Sentry for error tracking.
- Prometheus/Grafana for detailed metric dashboards.
- Uptime Kuma for external pinging.
