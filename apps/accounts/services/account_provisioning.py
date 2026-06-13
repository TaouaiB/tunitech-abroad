import logging

logger = logging.getLogger(__name__)

class AccountProvisioningService:
    @staticmethod
    def provision_new_user(user, provider=None):
        """
        Idempotent service to provision user accounts after signup/login.
        
        Note (Phase 1):
        Currently only acts as a shell.
        
        Phase 2 TODO:
        - Create CandidateProfile if it does not exist.
        - Create EmailPreference if it does not exist.
        """
        logger.info(f"AccountProvisioningService shell: provisioning {user.email}")
        # Safe to call multiple times because we will use get_or_create in Phase 2
        pass
