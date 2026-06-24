# Static & Private Media Deployment Policy

This document clarifies the deployment architecture for serving static assets and private user uploads (like CVs).

## 1. Static Files

**Definition**: CSS, JS, images, fonts included in the repository and collected via `manage.py collectstatic`.

**Deployment Strategy**:
- Served efficiently by **Whitenoise** within the Django WSGI/ASGI application.
- Caddy/Nginx acts as a reverse proxy, forwarding requests to Gunicorn, which uses Whitenoise for `STATIC_URL` routes.
- This keeps deployment simple without needing a separate web server block for static assets in the initial MVP.

## 2. Private Media (CV Uploads)

**Definition**: User-uploaded files, primarily PDF resumes. Stored in `PRIVATE_MEDIA_ROOT`.

**Deployment Strategy**:
- **Must NEVER be served directly** by Whitenoise, Caddy, or Nginx.
- Caddy/Nginx must explicitly deny direct access to the private media directory if it is ever accidentally exposed in the web root.
- Access to these files is strictly routed through Django views (e.g., `/profile/cv/download/`).

## 3. Security and Privacy Rules

- **Authentication Enforcement**: CV downloads and status routes must check `request.user.is_authenticated`.
- **Ownership Enforcement**: A user can only access their own CVs.
- **Deletion Handling**:
  - `CVUpload.objects` automatically excludes soft-deleted CVs.
  - `CVUpload.all_objects` is reserved for admin, privacy deletion tasks, and internal maintenance only.
