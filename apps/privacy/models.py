from django.db import models
from django.conf import settings

class ConsentRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consent_records")
    
    consent_type = models.CharField(max_length=100)
    consent_version = models.CharField(max_length=50)
    accepted = models.BooleanField(default=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.consent_type} v{self.consent_version} - {self.user.email}"
