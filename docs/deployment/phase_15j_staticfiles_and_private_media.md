# Static Files & Private Media

## Static Files
- We use Whitenoise for static files serving in production.
- Gunicorn handles serving these files efficiently alongside application logic.
- Run `python manage.py collectstatic` on every deploy.

## Private Media (CVs)
- Caddy **MUST NOT** serve `/media/` directories directly.
- User-uploaded files like CVs are strictly private.
- They are served via Django proxy views that perform authentication and authorization checks.
