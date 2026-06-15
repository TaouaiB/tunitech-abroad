import logging
from apps.profiles.models import CandidateProfile
from apps.notifications.models import EmailPreference

logger = logging.getLogger(__name__)

class AccountProvisioningService:
    @staticmethod
    def provision_new_user(user, provider=None):
        """
        Idempotent service to provision user accounts after signup/login.
        """
        logger.info(f"AccountProvisioningService: provisioning {user.email}")
        
        profile, profile_created = CandidateProfile.objects.get_or_create(user=user)
        if profile_created:
            logger.info(f"Created CandidateProfile for {user.email}")
            
        prefs, prefs_created = EmailPreference.objects.get_or_create(user=user)
        if prefs_created:
            logger.info(f"Created EmailPreference for {user.email}")
            
        return profile
