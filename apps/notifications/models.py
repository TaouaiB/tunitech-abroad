import uuid
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

class EmailBatch(models.Model):
    BATCH_TYPE_CHOICES = (
        ("weekly_digest", "Weekly Digest"),
        ("transactional", "Transactional"),
        ("system", "System"),
    )
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("partial_success", "Partial Success"),
    )
    
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    batch_type = models.CharField(max_length=20, choices=BATCH_TYPE_CHOICES, default="system")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Batch {self.public_id} ({self.batch_type} - {self.status})"

class EmailEvent(models.Model):
    EMAIL_TYPE_CHOICES = (
        ("system", "System"),
        ("verification", "Verification"),
        ("password_reset", "Password Reset"),
        ("weekly_digest", "Weekly Digest"),
        ("cv_analysis_completed", "CV Analysis Completed"),
        ("product_update", "Product Update"),
    )
    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
        ("duplicate", "Duplicate"),
    )
    
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="email_events")
    batch = models.ForeignKey(EmailBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    
    email_type = models.CharField(max_length=30, choices=EMAIL_TYPE_CHOICES, default="system")
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    idempotency_key = models.CharField(max_length=255, unique=True)
    
    provider_message_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    
    queued_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Event {self.public_id} to {self.to_email} ({self.status})"

class EmailUnsubscribeToken(models.Model):
    EMAIL_TYPE_CHOICES = (
        ("weekly_digest", "Weekly Digest"),
        ("product_update", "Product Update"),
        ("all", "All"),
    )
    
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="unsubscribe_tokens")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    email_type = models.CharField(max_length=30, choices=EMAIL_TYPE_CHOICES, default="all")
    
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Token for {self.user.email} ({self.email_type})"
