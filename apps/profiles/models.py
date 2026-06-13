import uuid
from django.db import models
from django.conf import settings

class CandidateProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="candidate_profile")
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)

    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    current_level = models.CharField(max_length=50, blank=True)
    years_experience = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    target_country = models.CharField(max_length=100, default="France")
    target_roles = models.JSONField(default=list, blank=True)
    target_job_types = models.JSONField(default=list, blank=True)
    target_type = models.CharField(max_length=50, blank=True)

    french_level = models.CharField(max_length=20, blank=True)
    english_level = models.CharField(max_length=20, blank=True)
    relocation_preference = models.CharField(max_length=50, blank=True)
    remote_preference = models.CharField(max_length=50, blank=True)

    profile_completion_score = models.PositiveSmallIntegerField(default=0)
    is_confirmed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Profile"

class ProfileSkill(models.Model):
    profile = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="profile_skills")
    raw_name = models.CharField(max_length=150)
    normalized_name = models.CharField(max_length=150, db_index=True)
    source = models.CharField(max_length=50, blank=True)
    confidence = models.PositiveSmallIntegerField(default=100)
    is_confirmed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['profile', 'normalized_name'], name='unique_profile_skill')
        ]

    def __str__(self):
        return f"{self.normalized_name} for {self.profile.user.email}"
