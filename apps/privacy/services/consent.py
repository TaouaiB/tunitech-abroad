from apps.privacy.models import ConsentRecord

class ConsentService:
    @staticmethod
    def record_consent(user, consent_type, consent_version, accepted=True, ip_address=None, user_agent=""):
        return ConsentRecord.objects.create(
            user=user,
            consent_type=consent_type,
            consent_version=consent_version,
            accepted=accepted,
            ip_address=ip_address,
            user_agent=user_agent
        )
