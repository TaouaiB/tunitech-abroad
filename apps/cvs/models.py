from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateMediaStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT)

    def url(self, name):
        raise ValueError("Private CV files do not have public URLs.")


private_storage = PrivateMediaStorage()

def cv_upload_path(instance, filename):
    return f"cvs/{instance.user.id}/{uuid.uuid4()}_{filename}"

class ActiveCVManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class CVUpload(models.Model):
    PARSE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('parsed', 'Parsed'),
        ('parsed_with_warnings', 'Parsed with Warnings'),
        ('failed', 'Failed'),
        ('deleted', 'Deleted'),
    ]

    TEXT_EXTRACTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('too_little_text', 'Too Little Text'),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cv_uploads")
    
    file = models.FileField(upload_to=cv_upload_path, storage=private_storage)
    original_filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, db_index=True)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100, default="application/pdf")
    
    is_active = models.BooleanField(default=True, db_index=True)
    parse_status = models.CharField(max_length=50, choices=PARSE_STATUS_CHOICES, default='pending', db_index=True)
    parse_error = models.TextField(blank=True)
    
    text_extraction_status = models.CharField(max_length=50, choices=TEXT_EXTRACTION_STATUS_CHOICES, blank=True, default='pending')
    extracted_text_length = models.PositiveIntegerField(null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = ActiveCVManager()
    all_objects = models.Manager()

    # Reverse accessor declared by CVParsedData.cv_upload (related_name="parsed_data").
    # This annotation exists only for static analysis; Django creates the descriptor at runtime.
    if TYPE_CHECKING:
        parsed_data: CVParsedData

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_active=True, deleted_at__isnull=True),
                name='unique_active_cv_per_user'
            )
        ]

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.parse_status = 'deleted'
        self.save(update_fields=['is_active', 'deleted_at', 'parse_status'])

    def __str__(self):
        return f"{self.user.email} - {self.original_filename}"

class CVParsedData(models.Model):
    EXTRACTION_METHOD_CHOICES = [
        ('regex_only', 'Regex Only'),
        ('regex_llm', 'Regex + LLM'),
        ('manual', 'Manual'),
        ('failed', 'Failed'),
    ]

    cv_upload = models.OneToOneField(CVUpload, on_delete=models.CASCADE, related_name="parsed_data")
    raw_text = models.TextField(blank=True)
    
    deterministic_json = models.JSONField(default=dict)
    llm_json = models.JSONField(default=dict)
    merged_json = models.JSONField(default=dict)
    
    extraction_method = models.CharField(max_length=50, choices=EXTRACTION_METHOD_CHOICES, blank=True)
    llm_schema_version = models.CharField(max_length=50, blank=True)
    
    extracted_name = models.CharField(max_length=255, blank=True)
    extracted_email = models.EmailField(blank=True)
    extracted_phone = models.CharField(max_length=50, blank=True)
    extracted_location = models.CharField(max_length=255, blank=True)
    
    extracted_linkedin_url = models.URLField(blank=True)
    extracted_github_url = models.URLField(blank=True)
    extracted_portfolio_url = models.URLField(blank=True)
    
    estimated_years_experience = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    confidence_json = models.JSONField(default=dict)
    warnings_json = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parsed Data for {self.cv_upload.public_id}"
