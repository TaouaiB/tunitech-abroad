from celery import shared_task
from apps.notifications.services.weekly_digest import WeeklyDigestService

@shared_task
def send_weekly_digest(period_start=None, period_end=None):
    batch = WeeklyDigestService.send_weekly_digest(period_start, period_end)
    return str(batch.public_id)
