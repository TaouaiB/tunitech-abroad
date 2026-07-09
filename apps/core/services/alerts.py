import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from apps.core.models import AdminAlertEvent
from datetime import timedelta
from apps.core.services.health import HealthCheckService

logger = logging.getLogger(__name__)

# Fragments considered sensitive in dict keys.
_BLOCKED_FRAGMENTS = (
    "secret", "token", "password", "raw_text",
    "file_path", "private_path", "api_key",
)


class AdminAlertService:
    @classmethod
    def trigger_alert(cls, alert_type: str, severity: str, summary: str, details: dict = None) -> AdminAlertEvent:
        if details is None:
            details = {}

        # Deduplication: suppress if exact same alert triggered in last 1 hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_alert = AdminAlertEvent.objects.filter(
            alert_type=alert_type,
            summary=summary,
            created_at__gte=one_hour_ago
        ).first()

        if recent_alert:
            logger.info("Suppressed duplicate admin alert type=%s", alert_type)
            return recent_alert

        safe_details = cls._sanitize_details(details)
        event = AdminAlertEvent.objects.create(
            alert_type=alert_type,
            severity=severity,
            summary=summary,
            details_json=safe_details,
        )

        cls._send_alert_email(event)
        return event

    @classmethod
    def _send_alert_email(cls, event: AdminAlertEvent):
        admin_email = getattr(settings, 'ADMIN_ALERT_EMAIL', None)
        if not admin_email:
            logger.error("ADMIN_ALERT_EMAIL is not set. Cannot send alert email.")
            return

        subject = f"[{event.severity.upper()}] TuniAtlas Alert: {event.alert_type}"

        # Render sanitized details as flat key: value lines.
        # details_json is already sanitized by trigger_alert().
        details_text = "\n".join([f"{k}: {v}" for k, v in event.details_json.items()])

        body = (
            f"Alert Type: {event.alert_type}\n"
            f"Severity: {event.severity}\n"
            f"Summary: {event.summary}\n\n"
            f"Details:\n{details_text}\n\n"
            f"Time: {event.created_at}"
        )

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
                fail_silently=False,
            )
            event.status = "sent"
            event.sent_at = timezone.now()
            event.sent_to = admin_email
            event.save(update_fields=['status', 'sent_at', 'sent_to'])
        except Exception:
            logger.error("Admin alert email delivery failed. Check mail configuration.")
            event.details_json["send_error"] = "email_send_failed"
            event.save(update_fields=['details_json'])

    @classmethod
    def run_health_alerts(cls) -> dict:
        health = HealthCheckService.run()
        created = []
        for error in health.get("errors", []):
            event = cls.trigger_alert(
                alert_type=error,
                severity="critical",
                summary=f"Health check reported {error}",
                details={"counts": health.get("counts", {}), "statuses": health.get("statuses", {})},
            )
            created.append(event.id)
        for warning in health.get("warnings", []):
            event = cls.trigger_alert(
                alert_type=warning,
                severity="warning",
                summary=f"Health check reported {warning}",
                details={"counts": health.get("counts", {}), "statuses": health.get("statuses", {})},
            )
            created.append(event.id)
        return {"health": health, "alert_event_ids": created}

    @classmethod
    def _sanitize_details(cls, details) -> dict:
        """Recursively redact sensitive keys from dicts.

        Only string-valued keys are inspected against the blocked fragment list.
        Non-string values under safe-looking keys are passed through unchanged.
        Lists are recursively sanitized element by element.
        """
        if isinstance(details, dict):
            safe = {}
            for key, value in details.items():
                key_text = str(key)
                if any(frag in key_text.lower() for frag in _BLOCKED_FRAGMENTS):
                    safe[key_text] = "[redacted]"
                else:
                    safe[key_text] = cls._sanitize_details(value)
            return safe
        if isinstance(details, list):
            return [cls._sanitize_details(item) for item in details]
        # Scalar value under a safe key — return as-is.
        return details
