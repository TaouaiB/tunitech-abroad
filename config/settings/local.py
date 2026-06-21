import os
"""
config/settings/local.py

Local development overrides.
Inherits everything from base and enables development-friendly settings.
"""
from .base import *  # noqa: F401, F403

# ─────────────────────────────────────────────────────────────────────────────
# Debug
# ─────────────────────────────────────────────────────────────────────────────

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]  # nosec B104

# ─────────────────────────────────────────────────────────────────────────────
# Dev-only installed apps
# ─────────────────────────────────────────────────────────────────────────────

INSTALLED_APPS = INSTALLED_APPS + [  # noqa: F405
    "django_extensions",
]

# ─────────────────────────────────────────────────────────────────────────────
# Email backend (console for local)
# ─────────────────────────────────────────────────────────────────────────────

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")

# ─────────────────────────────────────────────────────────────────────────────
# Static files (served locally by Django dev server)
# ─────────────────────────────────────────────────────────────────────────────

STATICFILES_DIRS = [BASE_DIR / "static"]  # noqa: F405
