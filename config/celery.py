"""
config/celery.py

Celery application configuration for TuniTech Abroad.

- Uses Django settings for all configuration (via django-celery integration).
- Broker and result backend are configured via environment variables.
- Autodiscovery will find tasks in all INSTALLED_APPS once apps are added.
"""
import os

from celery import Celery
from celery.utils.log import get_task_logger

# Set the default Django settings module for the Celery command-line programs.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("tunitech_abroad")

# Read Celery configuration from Django settings, using CELERY_ prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks in all INSTALLED_APPS.
app.autodiscover_tasks()

logger = get_task_logger(__name__)


@app.task(bind=True, name="config.tasks.debug_task")
def debug_task(self):
    """
    Phase 0 debug task.

    Purpose: prove Celery worker and broker are correctly wired.
    This task must NOT contain any business logic.
    """
    logger.info("Debug task running on worker: %s", self.request.hostname)
    return f"Phase 0 debug task OK — worker: {self.request.hostname}"
