import logging
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from allauth.account.models import EmailAddress
from apps.notifications.models import EmailBatch, EmailEvent, EmailPreference, EmailUnsubscribeToken
from apps.recommendations.models import JobRecommendation
from apps.recommendations.services.active_users import ActiveUserRecommendationService
from apps.notifications.services.email_sender import EmailSenderService

logger = logging.getLogger(__name__)

class WeeklyDigestService:
    @classmethod
    def send_weekly_digest(cls, period_start=None, period_end=None) -> EmailBatch:
        now = timezone.now()
        if not period_end:
            period_end = now
        if not period_start:
            from datetime import timedelta
            period_start = period_end - timedelta(days=7)
            
        # Create Batch
        batch = EmailBatch.objects.create(
            batch_type="weekly_digest",
            status="running",
            period_start=period_start,
            period_end=period_end,
            started_at=now,
        )
        
        try:
            # Get active users with usable profile
            active_users = ActiveUserRecommendationService.get_active_users(days=14)
            
            sent_count = 0
            skipped_count = 0
            failed_count = 0
            
            year, week, _ = period_end.isocalendar()
            site_url = getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/")
            
            for user in active_users:
                # 1. verified email
                email_address = EmailAddress.objects.filter(user=user, verified=True).first()
                if not email_address:
                    skipped_count += 1
                    continue
                    
                # 2. EmailPreference.weekly_digest_enabled=True
                pref = EmailPreference.objects.filter(user=user, weekly_digest_enabled=True).first()
                if not pref:
                    skipped_count += 1
                    continue
                    
                # 3. has new or relevant recommendations
                recs = JobRecommendation.objects.filter(
                    user=user,
                    status="active"
                ).select_related("job").order_by("-ranking_score")[:5]
                
                if not recs:
                    skipped_count += 1
                    continue
                    
                # Eligible!
                idempotency_key = f"weekly_digest:{user.id}:{year}-W{week}"

                if EmailEvent.objects.filter(idempotency_key=idempotency_key).exists():
                    skipped_count += 1
                    continue
                
                token = EmailUnsubscribeToken.objects.filter(
                    user=user,
                    email_type="weekly_digest",
                    used_at__isnull=True,
                ).first()
                if token is None:
                    token = EmailUnsubscribeToken.objects.create(
                        user=user,
                        email_type="weekly_digest",
                    )
                
                context = {
                    "user": user,
                    "recommendations": recs,
                    "period_start": period_start,
                    "period_end": period_end,
                    "site_url": site_url,
                    "recommendations_url": f"{site_url}{reverse('dashboard:recommendations')}",
                    "unsubscribe_url": f"{site_url}{reverse('notifications:unsubscribe', kwargs={'token': token.token})}",
                }
                
                try:
                    event = EmailSenderService.send(
                        to=email_address.email,
                        subject="Your Weekly Job Recommendations",
                        template_name="weekly_digest",
                        context=context,
                        idempotency_key=idempotency_key,
                        user=user,
                        batch=batch,
                        email_type="weekly_digest"
                    )
                    if event.status == "sent":
                        sent_count += 1
                    elif event.status == "failed":
                        failed_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    logger.error(f"Error sending digest to {user.id}: {e}")
                    failed_count += 1
            
            batch.total_recipients = sent_count + skipped_count + failed_count
            batch.sent_count = sent_count
            batch.skipped_count = skipped_count
            batch.failed_count = failed_count
            batch.status = "completed" if failed_count == 0 else "partial_success"
            
        except Exception as e:
            logger.error(f"Error running weekly digest batch: {e}")
            batch.status = "failed"
            batch.error_message = str(e)
            
        batch.finished_at = timezone.now()
        batch.save()
        
        return batch
