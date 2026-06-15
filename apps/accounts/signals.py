from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .services.account_provisioning import AccountProvisioningService

@receiver(user_signed_up)
def trigger_account_provisioning(request, user, **kwargs):
    AccountProvisioningService.provision_new_user(user)
