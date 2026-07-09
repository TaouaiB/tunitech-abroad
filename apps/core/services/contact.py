import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from apps.core.models import ContactMessage

logger = logging.getLogger(__name__)

class ContactService:
    @classmethod
    def submit_contact_message(cls, *, form, user=None, request=None) -> ContactMessage:
        from django.db import transaction
        from apps.core.tasks import send_contact_message_email

        message = form.save(commit=False)
        if user and user.is_authenticated:
            message.user = user
            if not message.email:
                message.email = user.email

        if request:
            message.source_path = request.path

        with transaction.atomic():
            message.save()
            transaction.on_commit(lambda: send_contact_message_email.delay(message.id))

        return message

    @classmethod
    def send_contact_message_email(cls, *, message_id: int) -> None:
        try:
            message = ContactMessage.objects.get(id=message_id)
        except ContactMessage.DoesNotExist:
            logger.error("ContactMessage %s does not exist", message_id)
            return

        recipients = getattr(settings, "CONTACT_EMAIL_RECIPIENTS", [])
        if not recipients:
            logger.warning("No CONTACT_EMAIL_RECIPIENTS configured.")
            message.status = ContactMessage.Status.FAILED
            message.last_error_code = "recipient_not_configured"
            message.save(update_fields=["status", "last_error_code", "updated_at"])
            return

        subject = f"[TuniAtlas Contact] {message.subject}"
        body = f"Name: {message.name}\nEmail: {message.email}\nSubject: {message.subject}\nPath: {message.source_path}\n\nMessage:\n{message.message}"

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
            message.status = ContactMessage.Status.SENT
            message.sent_at = timezone.now()
            message.last_error_code = ""
            message.save(update_fields=["status", "sent_at", "last_error_code", "updated_at"])
        except Exception:
            logger.error("Contact email send failed for message %s", message_id)
            message.status = ContactMessage.Status.FAILED
            message.last_error_code = "email_send_failed"
            message.save(update_fields=["status", "last_error_code", "updated_at"])
