from dataclasses import dataclass
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.notifications.models import EmailPreference, EmailUnsubscribeToken
from apps.accounts.models import User
from apps.privacy.services.consent import ConsentService

@dataclass
class ServiceResult:
    success: bool
    error: str = ""

class EmailPreferenceService:
    @staticmethod
    def update_preferences(user: User, cleaned_data: dict) -> EmailPreference:
        pref, _ = EmailPreference.objects.get_or_create(user=user)
        
        old_digest_enabled = pref.weekly_digest_enabled
        new_digest_enabled = cleaned_data.get("weekly_digest_enabled", pref.weekly_digest_enabled)
        
        pref.weekly_digest_enabled = new_digest_enabled
        
        if "product_updates_enabled" in cleaned_data:
            pref.product_updates_enabled = cleaned_data["product_updates_enabled"]
            
        if "cv_analysis_email_enabled" in cleaned_data:
            pref.cv_analysis_email_enabled = cleaned_data["cv_analysis_email_enabled"]
        
        pref.save()
        
        if new_digest_enabled and not old_digest_enabled:
            # record consent
            ConsentService.record(
                user=user,
                consent_type="email_digest",
                consent_text="Consentement aux emails hebdomadaires de recommandations.",
                consent_version="1.0",
                request_meta={"source_path": "email_preferences"},
                accepted=True,
            )
            
        return pref

    @staticmethod
    def unsubscribe(token: str) -> ServiceResult:
        try:
            token_obj = EmailUnsubscribeToken.objects.get(token=token)
            
            if token_obj.used_at:
                return ServiceResult(success=True) # Idempotent
                
            pref, _ = EmailPreference.objects.get_or_create(user=token_obj.user)
            
            if token_obj.email_type == "weekly_digest":
                pref.weekly_digest_enabled = False
            elif token_obj.email_type == "product_update":
                pref.product_updates_enabled = False
            elif token_obj.email_type == "all":
                pref.weekly_digest_enabled = False
                pref.product_updates_enabled = False
                
            pref.save()
            
            token_obj.used_at = timezone.now()
            token_obj.save(update_fields=["used_at"])
            
            return ServiceResult(success=True)
            
        except EmailUnsubscribeToken.DoesNotExist:
            return ServiceResult(success=False, error="Invalid token")
        except (ValidationError, ValueError):
            return ServiceResult(success=False, error="Invalid token format")
