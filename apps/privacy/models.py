from django.conf import settings
from django.db import models
import uuid

class ConsentRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consent_records")

    consent_type = models.CharField(max_length=100)
    consent_text = models.CharField(max_length=255, blank=True)
    consent_version = models.CharField(max_length=50)
    accepted = models.BooleanField(default=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.consent_type} v{self.consent_version} - {self.user.email}"

class DeletionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="deletion_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    completed_summary_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"DeletionRequest {self.public_id} - {self.status}"
