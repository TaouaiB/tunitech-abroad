# Phase 15J Deployment Runbook (Outline)

This runbook outlines the steps to deploy TuniTech Abroad to a Linux VPS (e.g., Hetzner).

## Target Architecture

- **Server**: Hetzner VPS (Linux/bash-oriented, e.g., Fedora or Ubuntu).
- **Reverse Proxy / TLS**: Caddy (handles HTTPS automatically, proxies to Gunicorn).
- **Web Server**: Gunicorn running the Django application.
- **Static Assets**: Whitenoise serving static files via Django.
- **Private Media**: Stored on disk, protected by Django views.
- **Database**: PostgreSQL.
- **Message Broker / Cache**: Redis.
- **Background Workers**: Celery worker and Celery beat managed by `systemd`.

## Step-by-Step Outline

1. **System Preparation**
   - Provision server, configure firewall (UFW/Firewalld), allow ports 80/443/22.
   - Create non-root `tunitech` user.
   - Install dependencies: Python 3.12+, PostgreSQL, Redis, Caddy.

2. **Database Setup**
   - Create PostgreSQL user and database.
   - Secure Redis (bind to localhost, requirepass if necessary).

3. **Application Deployment**
   - Clone the repository as the `tunitech` user.
   - Create virtual environment, install dependencies (`pip install -r requirements.txt`).
   - Create the `.env` file with real secrets.

4. **Django Setup**
   - Run migrations (`python manage.py migrate`).
   - Collect static files (`python manage.py collectstatic`).
   - Create superuser.

5. **Service Configuration (`systemd`)**
   - Create and enable `tunitech-web.service` (Gunicorn).
   - Create and enable `tunitech-celery.service` (Celery worker).
   - Create and enable `tunitech-beat.service` (Celery beat).

6. **Web Server Configuration**
   - Create `Caddyfile` to reverse proxy `domain.com` to Gunicorn's local socket/port.
   - Start Caddy, verify HTTPS provisioning.

7. **Verification**
   - Execute the `production_smoke_checklist.md`.
