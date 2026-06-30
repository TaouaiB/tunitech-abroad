from celery import shared_task

from apps.core.services.alerts import AdminAlertService
from apps.core.services.digest import AdminOpsDigestService


@shared_task
def run_admin_health_alerts():
    return AdminAlertService.run_health_alerts()


@shared_task
def send_admin_ops_digest():
    AdminOpsDigestService.send_digest_email()
    return "admin_ops_digest_checked"
