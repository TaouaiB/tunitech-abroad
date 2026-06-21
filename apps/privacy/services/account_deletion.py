import logging
from django.db import transaction
from django.utils import timezone
from apps.privacy.models import DeletionRequest
from apps.cvs.models import CVUpload
from apps.cvs.services.deletion import CVDeletionService
from apps.analytics.services.user_event import UserEventService

logger = logging.getLogger(__name__)

class AccountDeletionService:
    @staticmethod
    def request_deletion(user) -> DeletionRequest:
        request_obj = DeletionRequest.objects.filter(
            user=user,
            status__in=["pending", "processing"],
        ).first()
        created = request_obj is None
        if request_obj is None:
            request_obj = DeletionRequest.objects.create(user=user, status="pending")

        try:
            UserEventService.record_event(
                event_type="account_deletion_requested",
                user=user,
                metadata={"request_public_id": str(request_obj.public_id)},
            )
        except Exception as e:
            logger.warning(f"Failed to record account deletion requested event: {e}", exc_info=True)

        if created:
            AccountDeletionService.process_request(request_obj)

        return request_obj

    @staticmethod
    def process_request(deletion_request: DeletionRequest) -> DeletionRequest:
        if deletion_request.status == 'completed':
            return deletion_request

        deletion_request.status = 'processing'
        deletion_request.save(update_fields=['status'])

        user = deletion_request.user
        if not user:
            deletion_request.status = 'failed'
            deletion_request.error_message = 'User not found'
            deletion_request.attempt_count += 1
            deletion_request.save(update_fields=['status', 'error_message', 'attempt_count'])
            return deletion_request

        try:
            user.is_active = False
            user.save(update_fields=['is_active'])

            with transaction.atomic():
                summary = {}

                # Delete CVs (this also deletes CVParsedData and unconfirmed ProfileSkills)
                cvs = list(CVUpload.all_objects.filter(user=user))
                summary["cv_uploads"] = len(cvs)
                for cv in cvs:
                    if cv.deleted_at is None:
                        CVDeletionService.delete_cv(user, cv.public_id)
                    else:
                        CVDeletionService.delete_cv_record(cv)

                # Delete saved jobs
                try:
                    from apps.recommendations.models import SavedJob
                    summary["saved_jobs"], _ = SavedJob.objects.filter(user=user).delete()
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to delete saved jobs: {e}", exc_info=True)

                # Delete match results
                try:
                    from apps.matching.models import MatchResult
                    summary["match_results"], _ = MatchResult.objects.filter(user=user).delete()
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to delete match results: {e}", exc_info=True)

                # Delete recommendations
                try:
                    from apps.recommendations.models import JobRecommendation, RecommendationRun
                    summary["recommendations"], _ = JobRecommendation.objects.filter(user=user).delete()
                    summary["recommendation_runs"] = RecommendationRun.objects.filter(user=user).update(
                        user=None,
                        error_message="",
                    )
                except ImportError:
                    pass

                # Delete candidate profile and remaining profile skills
                if hasattr(user, 'candidate_profile'):
                    user.candidate_profile.delete()

                # Delete email preferences
                try:
                    from apps.notifications.models import EmailPreference, EmailUnsubscribeToken, EmailEvent
                    summary["email_preferences"], _ = EmailPreference.objects.filter(user=user).delete()
                    summary["unsubscribe_tokens"], _ = EmailUnsubscribeToken.objects.filter(user=user).delete()
                    summary["email_events"] = EmailEvent.objects.filter(user=user).update(
                        user=None,
                        to_email="deleted-user@deleted.local",
                        subject="",
                        provider_message_id="",
                        error_message="",
                        metadata_json={},
                    )
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to delete email preferences: {e}", exc_info=True)

                # Anonymize LLM usage logs
                try:
                    from apps.llm.models import LLMRequestLog
                    summary["llm_request_logs"] = LLMRequestLog.objects.filter(user=user).update(
                        user=None,
                        error_message="",
                    )
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to anonymize LLM usage logs: {e}", exc_info=True)

                # Anonymize UserEvents
                try:
                    from apps.analytics.models import UserEvent
                    summary["user_events"] = UserEvent.objects.filter(user=user).update(
                        user=None,
                        metadata={},
                    )
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to anonymize user events: {e}", exc_info=True)

                # Remove social accounts
                try:
                    from allauth.account.models import EmailAddress
                    from allauth.socialaccount.models import SocialAccount
                    summary["email_addresses"], _ = EmailAddress.objects.filter(user=user).delete()
                    summary["social_accounts"], _ = SocialAccount.objects.filter(user=user).delete()
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to remove social accounts: {e}", exc_info=True)

                # Anonymize User
                user.email = f"deleted-user-{deletion_request.public_id}@deleted.local"
                user.username = f"deleted_{deletion_request.public_id.hex[:10]}"
                user.first_name = ""
                user.last_name = ""
                user.set_unusable_password()
                user.save()

                deletion_request.completed_summary_json = summary

            deletion_request.status = 'completed'
            deletion_request.processed_at = timezone.now()
            deletion_request.error_message = ""
            deletion_request.save(update_fields=['status', 'processed_at', 'error_message', 'completed_summary_json'])

        except Exception as e:
            deletion_request.status = 'failed'
            deletion_request.attempt_count += 1
            deletion_request.error_message = str(e)[:500]
            deletion_request.save(update_fields=['status', 'attempt_count', 'error_message'])

        return deletion_request
