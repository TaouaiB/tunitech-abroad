from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added, social_account_updated
from .services.account_provisioning import AccountProvisioningService

@receiver(user_signed_up)
def trigger_account_provisioning(request, user, **kwargs):
    AccountProvisioningService.provision_new_user(user)
    sociallogin = kwargs.get('sociallogin')
    if sociallogin:
        populate_profile_from_social_data(user, sociallogin)

@receiver(social_account_added)
def handle_social_account_added(request, sociallogin, **kwargs):
    populate_profile_from_social_data(sociallogin.user, sociallogin)

@receiver(social_account_updated)
def handle_social_account_updated(request, sociallogin, **kwargs):
    populate_profile_from_social_data(sociallogin.user, sociallogin)

def populate_profile_from_social_data(user, sociallogin):
    if hasattr(user, 'candidate_profile'):
        profile = user.candidate_profile
        data = sociallogin.account.extra_data
        provider = sociallogin.account.provider
        
        update_fields = []
        name = data.get('name') or data.get('full_name')
        if name and not profile.full_name:
            profile.full_name = name
            update_fields.append('full_name')
            
        avatar_url = data.get('picture') if provider == 'google' else data.get('avatar_url')
        if avatar_url and not profile.avatar_url:
            profile.avatar_url = avatar_url
            update_fields.append('avatar_url')
            
        if provider == 'github':
            login = data.get('login')
            if login and not profile.github_url:
                profile.github_url = f"https://github.com/{login}"
                update_fields.append('github_url')
            if data.get('html_url') and not profile.github_url:
                profile.github_url = data.get('html_url')
                update_fields.append('github_url')
            if data.get('location') and not profile.location:
                profile.location = data.get('location')
                update_fields.append('location')
        elif provider == 'google':
            profile_url = data.get('profile') or data.get('link')
            if profile_url and not profile.website_url:
                profile.website_url = profile_url
                update_fields.append('website_url')

        email = data.get('email')
        if email and not user.email:
            user.email = email
            user.save(update_fields=['email'])
        
        if update_fields:
            profile.save(update_fields=update_fields)
