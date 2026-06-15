import logging
from typing import Optional
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.conf import settings
from django.utils import timezone
from apps.notifications.models import EmailEvent, EmailBatch
from apps.accounts.models import User

logger = logging.getLogger(__name__)

class EmailSenderService:
    @classmethod
    def send(
        cls,
        to: str,
        subject: str,
        template_name: str,
        context: dict,
        idempotency_key: str,
        user: Optional[User] = None,
        batch: Optional[EmailBatch] = None,
        email_type: str = "system",
    ) -> EmailEvent:
        """
        Sends an email using Django's email utilities and logs it as an EmailEvent.
        Provides idempotency via idempotency_key.
        """
        # Check idempotency
        existing_event = EmailEvent.objects.filter(idempotency_key=idempotency_key).first()
        if existing_event:
            logger.info(f"Idempotent email skip: EmailEvent already exists for key {idempotency_key}")
            return existing_event

        # Create queued event
        event = EmailEvent.objects.create(
            user=user,
            batch=batch,
            email_type=email_type,
            to_email=to,
            subject=subject,
            template_name=template_name,
            status="queued",
            idempotency_key=idempotency_key,
        )

        try:
            # Render text template (required)
            text_template = f"notifications/email/{template_name}.txt"
            text_content = render_to_string(text_template, context)

            # Render html template (optional)
            html_template = f"notifications/email/{template_name}.html"
            html_content = None
            try:
                html_content = render_to_string(html_template, context)
            except TemplateDoesNotExist:
                pass

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to]
            )
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            
            msg.send()

            event.status = "sent"
            event.sent_at = timezone.now()
            event.save(update_fields=["status", "sent_at"])
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            event.status = "failed"
            event.error_message = str(e)
            event.failed_at = timezone.now()
            event.save(update_fields=["status", "error_message", "failed_at"])

        return event
