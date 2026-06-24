# Phase 15L Deployment Decisions

## Infrastructure Plan
- **Provider/Server**: Cloud provider (e.g. Hetzner Cloud) using a suitable Linux instance. Prices vary based on current offerings; the exact sizing (e.g., CPX21 or CPX31) will be finalized before provisioning.
- **Web Server**: Caddy as reverse proxy and HTTPS termination.
- **Application Server**: Gunicorn running Django, managed via systemd.
- **Task Queue**: Celery and Celery Beat for async tasks and scheduling, managed via systemd.
- **Database**: PostgreSQL (local on the same instance or managed).
- **Cache**: Redis.

## Domain Plan
- **Primary Domain**: `tuniatlas.com`
- **Canonical Redirect**: `www.tuniatlas.com` will redirect to the root `tuniatlas.com`.
- **Secondary/Later Domain**: `tuniatlas.tn` (defensive registration/later use).

## External Services
- **Email Provider Plan**: An SMTP service such as SendGrid, Mailgun, or Postmark for transactional emails.
- **Backup Destination Plan**: Automated backups (database dumps and media) sent to a secure object storage bucket (e.g. AWS S3, Backblaze B2, Hetzner Storage Box).

## Security & LLM Cost Controls
- **LLM Automatic Spending Disabled**: LLM integrations will be explicitly disabled or strictly rate-limited on launch to prevent runaway costs.
- **Private Media/CV Protection**: CVs and other private media will remain strictly protected and not accessible via public static URLs.

## Next Phases Order
1. **15M**: Deployment
2. **15N**: Smoke test
3. **15O**: Opus security audit
4. **15P**: Public launch fixes
