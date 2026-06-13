"""
config/__init__.py

Load the Celery app so it is always imported when Django starts,
ensuring that shared_task uses this app.
"""
from .celery import app as celery_app  # noqa: F401

__all__ = ("celery_app",)
