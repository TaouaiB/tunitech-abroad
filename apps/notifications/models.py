from django.db import models
from django.conf import settings

class EmailPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_preferences")
    
    product_updates_enabled = models.BooleanField(default=False)
    weekly_digest_enabled = models.BooleanField(default=False)
    cv_analysis_email_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Email Preferences for {self.user.email}"
