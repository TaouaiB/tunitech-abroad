from django.db import models
from django.conf import settings

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
