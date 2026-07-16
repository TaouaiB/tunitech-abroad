import uuid

from django.db import models
from django.conf import settings

SKILL_UID_REGISTRY_HELP = (
    "Cross-environment UUIDv4 identity for this canonical skill. "
    "Assigned once from the committed skill UID registry and is immutable."
)


class SkillCategory(models.TextChoices):
    PROGRAMMING_LANGUAGE = 'programming_language', 'Programming Language'
    FRONTEND = 'frontend', 'Frontend'
    BACKEND = 'backend', 'Backend'
    DATABASE = 'database', 'Database'
    DEVOPS = 'devops', 'DevOps'
    CLOUD = 'cloud', 'Cloud'
    TESTING = 'testing', 'Testing'
    DATA_AI = 'data_ai', 'Data/AI'
    MOBILE = 'mobile', 'Mobile'
    TOOLS = 'tools', 'Tools'
    METHODOLOGY = 'methodology', 'Methodology'
    SOFT_SKILL = 'soft_skill', 'Soft Skill'
    SECURITY = 'security', 'Security'
    OTHER = 'other', 'Other'

class Skill(models.Model):
    canonical_name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.CharField(max_length=50, choices=SkillCategory.choices, default=SkillCategory.OTHER)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=50, default='manual')
    esco_uri = models.URLField(max_length=500, blank=True, null=True)
    skill_uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text=SKILL_UID_REGISTRY_HELP,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['canonical_name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['source']),
        ]

    def save(self, *args, **kwargs):
        """Reject changes to ``skill_uid`` after the row is persisted.

        ``skill_uid`` is a stable cross-environment identity. Direct SQL
        and ``QuerySet.update()`` bypass ``save()`` and are prohibited for
        this field — use the committed registry and the data migration
        ``0003_populate_skill_uid`` to provision it on existing rows.

        There is no public or private model helper that bypasses this
        invariant. The seed and rename code paths must therefore fail
        loudly when an existing row's ``skill_uid`` does not already
        match the registry; they may never rewrite a persisted identity.
        """
        if self.pk is not None:
            current = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("skill_uid", flat=True)
                .first()
            )
            if current is not None and current != self.skill_uid:
                raise ValueError(
                    "Skill.skill_uid is immutable. "
                    f"Existing={current} attempted={self.skill_uid} "
                    f"canonical_name={self.canonical_name!r}"
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.canonical_name

class SkillAlias(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name='aliases')
    alias = models.CharField(max_length=255)
    normalized_alias = models.CharField(max_length=255, unique=True)
    language = models.CharField(max_length=10, default='unknown')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['skill']),
            models.Index(fields=['normalized_alias']),
            models.Index(fields=['language']),
        ]

    def __str__(self):
        return f"{self.alias} -> {self.skill.canonical_name}"

class UnmatchedSkillCandidate(models.Model):
    SOURCE_CHOICES = [
        ('cv', 'CV'),
        ('job', 'Job'),
        ('quick_match', 'Quick Match'),
        ('manual', 'Manual'),
        ('admin', 'Admin'),
        ('unknown', 'Unknown'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('mapped', 'Mapped'),
        ('ignored', 'Ignored'),
    ]
    
    raw_skill_text = models.CharField(max_length=255)
    normalized_text = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='unknown')
    source_model = models.CharField(max_length=100, blank=True, null=True)
    source_object_id = models.BigIntegerField(blank=True, null=True)
    occurrence_count = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    mapped_skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name='mapped_candidates')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_skills')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['normalized_text', 'source_type'], name='unique_unmatched_skill')
        ]
        indexes = [
            models.Index(fields=['normalized_text']),
            models.Index(fields=['source_type']),
            models.Index(fields=['status']),
            models.Index(fields=['mapped_skill']),
            models.Index(fields=['reviewed_by']),
            models.Index(fields=['occurrence_count']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.raw_skill_text
