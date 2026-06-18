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
            
            try:
                from allauth.socialaccount.models import SocialAccount
                social_account = SocialAccount.objects.filter(user=user).first()
                if social_account:
                    extra = social_account.extra_data
                    if social_account.provider == 'google':
                        profile.full_name = extra.get('name', '')
                        profile.avatar_url = extra.get('picture', '')
                        profile.website_url = extra.get('profile') or extra.get('link') or ''
                    elif social_account.provider == 'github':
                        profile.full_name = extra.get('name', '')
                        profile.github_url = extra.get('html_url', '') or (
                            f"https://github.com/{extra.get('login')}" if extra.get('login') else ''
                        )
                        profile.avatar_url = extra.get('avatar_url', '')
                        profile.location = extra.get('location', '')
                    profile.save()
            except ImportError:
                pass
            
        prefs, prefs_created = EmailPreference.objects.get_or_create(user=user)
        if prefs_created:
            logger.info(f"Created EmailPreference for {user.email}")
            
        return profile
