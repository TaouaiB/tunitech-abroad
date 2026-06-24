"""
config/settings/base.py

Base settings shared across all environments.
All secrets and environment-specific values are read from environment variables.
This file must NOT contain any hardcoded secrets.
"""
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# Path helpers
# ─────────────────────────────────────────────────────────────────────────────

# BASE_DIR = /path/to/project (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env if present (only for local; production uses injected env vars)
load_dotenv(BASE_DIR / ".env")

# ─────────────────────────────────────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]  # Fail loudly if not set

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

raw_trusted_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in raw_trusted_origins.split(",") if origin.strip()]

SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000")

# ─────────────────────────────────────────────────────────────────────────────
# Application definition
#
# Phase 0 minimal apps — no django.contrib.auth, no django.contrib.admin.
# Phase 1 will add the custom User model before enabling auth/admin.
# ─────────────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    # Django core (auth, admin added in Phase 1)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",

    # Third-party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",

    # Local apps
    "apps.accounts.apps.AccountsConfig",
    "apps.core.apps.CoreConfig",
    "apps.dashboard.apps.DashboardConfig",
    "apps.profiles.apps.ProfilesConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.privacy.apps.PrivacyConfig",
    "apps.analytics.apps.AnalyticsConfig",
    "apps.skills.apps.SkillsConfig",
    "apps.jobs.apps.JobsConfig",
    "apps.cvs.apps.CVsConfig",
    "apps.matching.apps.MatchingConfig",
    "apps.recommendations.apps.RecommendationsConfig",
    "apps.llm.apps.LlmConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ─────────────────────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────────────────────

_database_url = os.environ.get("DATABASE_URL") or (
    "postgresql://{user}:{password}@{host}:{port}/{db}".format(
        user=os.environ.get("POSTGRES_USER", "tunitech"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        db=os.environ.get("POSTGRES_DB", "tunitech_abroad"),
    )
)

DATABASES = {
    "default": dj_database_url.parse(
        _database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ─────────────────────────────────────────────────────────────────────────────
# Cache (Redis)
# ─────────────────────────────────────────────────────────────────────────────

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6380/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

# ─────────────────────────────────────────────────────────────────────────────
# Celery
# ─────────────────────────────────────────────────────────────────────────────

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Paris"
CELERY_BEAT_SCHEDULER = "celery.beat:PersistentScheduler"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True  # Suppress Celery 5.x deprecation warning
CELERY_HEARTBEAT_STALE_MINUTES = int(os.environ.get("CELERY_HEARTBEAT_STALE_MINUTES", "15"))
CV_PARSE_STALE_MINUTES = int(os.environ.get("CV_PARSE_STALE_MINUTES", "15"))
INGESTION_STALE_RUNNING_MINUTES = int(os.environ.get("INGESTION_STALE_RUNNING_MINUTES", "60"))
JOB_ENRICHMENT_PROCESSING_STALE_MINUTES = int(os.environ.get("JOB_ENRICHMENT_PROCESSING_STALE_MINUTES", "60"))

JOB_ENRICHMENT_RETRY_ENABLED = os.environ.get("JOB_ENRICHMENT_RETRY_ENABLED", "False") == "True"
JOB_ENRICHMENT_RETRY_MAX_PER_RUN = int(os.environ.get("JOB_ENRICHMENT_RETRY_MAX_PER_RUN", "10"))
JOB_ENRICHMENT_RETRY_COOLDOWN_MINUTES = int(os.environ.get("JOB_ENRICHMENT_RETRY_COOLDOWN_MINUTES", "60"))
OPENROUTER_ENRICHMENT_RATE_LIMIT = os.environ.get("OPENROUTER_ENRICHMENT_RATE_LIMIT", "3/m")
OPENROUTER_ENRICHMENT_QUEUE = os.environ.get("OPENROUTER_ENRICHMENT_QUEUE", "llm")
OPENROUTER_CIRCUIT_BREAKER_ENABLED = os.environ.get("OPENROUTER_CIRCUIT_BREAKER_ENABLED", "True") == "True"
OPENROUTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.environ.get("OPENROUTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
OPENROUTER_CIRCUIT_BREAKER_WINDOW_MINUTES = int(os.environ.get("OPENROUTER_CIRCUIT_BREAKER_WINDOW_MINUTES", "30"))
OPENROUTER_CIRCUIT_BREAKER_COOLDOWN_MINUTES = int(os.environ.get("OPENROUTER_CIRCUIT_BREAKER_COOLDOWN_MINUTES", "60"))
JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY = os.environ.get("JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY", "False") == "True"

CELERY_TASK_ROUTES = {
    "apps.llm.tasks.enrich_job_task": {"queue": OPENROUTER_ENRICHMENT_QUEUE},
}

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "celery_heartbeat": {
        "task": "apps.jobs.tasks.celery_heartbeat",
        "schedule": crontab(minute="*/5"),
    },
    "run_it_job_ingestion": {
        "task": "apps.jobs.tasks.run_it_job_ingestion",
        "schedule": crontab(minute="0", hour="*/4"),
    },
    "mark_stale_and_expired_jobs": {
        "task": "apps.jobs.tasks.mark_stale_and_expired_jobs",
        "schedule": crontab(minute="30", hour="2"),
    },
    "refresh_active_users_recommendations": {
        "task": "apps.recommendations.tasks.refresh_active_users_recommendations",
        "schedule": crontab(minute="30", hour="3"),
    },
    "cleanup_expired_quick_matches": {
        "task": "apps.privacy.tasks.cleanup_expired_quick_matches",
        "schedule": crontab(minute="0", hour="4"),
    },
    "delete_orphaned_cv_files": {
        "task": "apps.privacy.tasks.delete_orphaned_cv_files",
        "schedule": crontab(minute="30", hour="4", day_of_week="sun"),
    },
}

if JOB_ENRICHMENT_RETRY_ENABLED:
    CELERY_BEAT_SCHEDULE["retry_eligible_job_enrichments"] = {
        "task": "apps.llm.tasks.retry_eligible_job_enrichments",
        "schedule": crontab(minute="15", hour="*/2"),
    }

# ─────────────────────────────────────────────────────────────────────────────
# Internationalisation
# ─────────────────────────────────────────────────────────────────────────────

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────────────────────────────────────
# Static files
# ─────────────────────────────────────────────────────────────────────────────

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# ─────────────────────────────────────────────────────────────────────────────
# Media files (CV uploads later — kept here as a placeholder)
# ─────────────────────────────────────────────────────────────────────────────

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"
MAX_CV_UPLOAD_SIZE_MB = int(os.environ.get("MAX_CV_UPLOAD_SIZE_MB", "5"))
CV_LLM_EXTRACTION_ENABLED = False

# ─────────────────────────────────────────────────────────────────────────────
# Default primary key type
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────────────────────────────────────
# Authentication & Allauth Configuration
# ─────────────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = "accounts.User"
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

SOCIALACCOUNT_ADAPTER = "apps.accounts.adapters.TuniTechSocialAccountAdapter"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# Social auth placeholders
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
            "secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            "key": ""
        }
    },
    "github": {
        "APP": {
            "client_id": os.environ.get("GITHUB_CLIENT_ID", ""),
            "secret": os.environ.get("GITHUB_CLIENT_SECRET", ""),
            "key": ""
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Logging (minimal base config)
# ─────────────────────────────────────────────────────────────────────────────

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# LLM Integration
# ─────────────────────────────────────────────────────────────────────────────

LLM_ENABLED = os.environ.get("LLM_ENABLED", "False") == "True"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_DEFAULT_MODEL = os.environ.get("OPENROUTER_DEFAULT_MODEL", "google/gemini-2.5-pro")

JOB_ENRICHMENT_ENABLED = os.environ.get("JOB_ENRICHMENT_ENABLED", "False") == "True"
JOB_RECOMMENDATIONS_USE_ENRICHED_DATA = os.environ.get("JOB_RECOMMENDATIONS_USE_ENRICHED_DATA", "False") == "True"
JOB_ENRICHMENT_MODEL = os.environ.get("JOB_ENRICHMENT_MODEL", OPENROUTER_DEFAULT_MODEL)
JOB_ENRICHMENT_DAILY_LIMIT = int(os.environ.get("JOB_ENRICHMENT_DAILY_LIMIT", "1000"))
JOB_ENRICHMENT_MAX_PER_INGESTION_RUN = int(os.environ.get("JOB_ENRICHMENT_MAX_PER_INGESTION_RUN", "20"))
JOB_ENRICHMENT_MIN_RELEVANCE = os.environ.get("JOB_ENRICHMENT_MIN_RELEVANCE", "partial") # strong, partial, generic_only, missing
JOB_ENRICHMENT_MAX_CHARS = int(os.environ.get("JOB_ENRICHMENT_MAX_CHARS", "6000"))
JOB_ENRICHMENT_MAX_RETRIES = int(os.environ.get("JOB_ENRICHMENT_MAX_RETRIES", "2"))

# France Travail API
FRANCE_TRAVAIL_CLIENT_ID = os.environ.get("FRANCE_TRAVAIL_CLIENT_ID", "")
FRANCE_TRAVAIL_CLIENT_SECRET = os.environ.get("FRANCE_TRAVAIL_CLIENT_SECRET", "")
FRANCE_TRAVAIL_REQUEST_DELAY_SECONDS = float(os.environ.get("FRANCE_TRAVAIL_REQUEST_DELAY_SECONDS", "0.5"))
FRANCE_TRAVAIL_MAX_REQUESTS_PER_RUN = int(os.environ.get("FRANCE_TRAVAIL_MAX_REQUESTS_PER_RUN", "100"))
FRANCE_TRAVAIL_BACKOFF_ON_429_SECONDS = int(os.environ.get("FRANCE_TRAVAIL_BACKOFF_ON_429_SECONDS", "60"))

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


# Email SMTP configuration
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "webmaster@localhost")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", DEFAULT_FROM_EMAIL)

# OAuth provider credentials
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
