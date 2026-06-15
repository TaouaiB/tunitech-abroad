from django.db import models
from django.conf import settings

class LLMRequestLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    purpose = models.CharField(max_length=100)
    provider = models.CharField(max_length=50, default="openrouter")
    model_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50) # 'success', 'error'
    prompt_tokens = models.IntegerField(null=True, blank=True)
    completion_tokens = models.IntegerField(null=True, blank=True)
    total_tokens = models.IntegerField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.purpose} - {self.model_name} ({self.status})"
