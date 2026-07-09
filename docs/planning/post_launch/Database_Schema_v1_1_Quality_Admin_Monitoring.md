# Database Schema v1.1 — Quality, Admin Monitoring, and ML-Ready Labels

Status: Post-launch schema addendum  
Product: TuniAtlas Jobs  
Purpose: Add schema needed for ingestion diagnostics, search quality, parser audits, corrections, admin alerts, and future ML readiness

## 1. Purpose

This document extends Database Schema v1.

It does not replace core v1 models.

Core v1 concepts remain:

```text
User
CandidateProfile
ProfileSkill
CVUpload
CVParsedData
Skill
SkillAlias
UnmatchedSkillCandidate
JobSource
IngestionRun
RawJobRecord
NormalizedJob
NormalizedJobSkill
MatchResult
JobRecommendation
SavedJob
EmailPreference
ConsentRecord
DeletionRequest
UserEvent
```

v1.1 adds operational quality and label data.

## 2. Schema design rules

```text
Do not duplicate existing concepts if already implemented.
Extend existing models when correct.
Use UUID public_id for public/admin-sensitive object references where appropriate.
Do not store secrets.
Do not store full CV text in logs.
Do not expose private file paths.
Do not create enterprise RBAC models now.
Prefer JSONField for audit snapshots and metrics where schema changes frequently.
```

## 3. JobIngestionConfig extension

If a `JobIngestionConfig` model exists, extend it. If not, create it.

Purpose:

```text
Owner/admin controls automatic ingestion volume and freshness thresholds without code edits.
```

Recommended fields:

```python
class JobIngestionConfig(models.Model):
    source = models.ForeignKey("jobs.JobSource", on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)

    target_daily_fetch_count = models.PositiveIntegerField(default=1000)
    max_jobs_per_run = models.PositiveIntegerField(default=1000)
    max_pages_per_query = models.PositiveIntegerField(default=10)
    page_size = models.PositiveIntegerField(default=100)

    queries_json = models.JSONField(default=list, blank=True)
    contract_filters_json = models.JSONField(default=dict, blank=True)
    location_filters_json = models.JSONField(default=dict, blank=True)
    remote_filters_json = models.JSONField(default=dict, blank=True)

    stale_after_hours = models.PositiveIntegerField(default=48)
    removed_after_hours = models.PositiveIntegerField(default=168)
    expire_grace_hours = models.PositiveIntegerField(default=24)

    last_effective_config_json = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

Constraints/indexes:

```text
index source
index is_active
optional unique active config per source if product wants one active config only
```

Notes:

```text
target_daily_fetch_count is not guaranteed. It is the target/limit.
queries_json must be admin-readable.
```

## 4. JobIngestionQueryRun

Purpose:

```text
Track ingestion per query so admin can explain why automatic fetch count is low.
```

Recommended model:

```python
class JobIngestionQueryRun(models.Model):
    ingestion_run = models.ForeignKey("jobs.IngestionRun", on_delete=models.CASCADE, related_name="query_runs")
    query_label = models.CharField(max_length=120, blank=True)
    params_json = models.JSONField(default=dict, blank=True)
    requested_range_json = models.JSONField(default=dict, blank=True)

    fetched_count = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    unchanged_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

Indexes:

```text
ingestion_run
query_label
started_at
error_count
```

## 5. SearchQueryLog

Purpose:

```text
Track search quality, zero-result searches, whitespace-only searches, invalid filters, and future product insights.
```

Recommended model:

```python
class SearchQueryLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    session_hash = models.CharField(max_length=128, blank=True)

    query_raw = models.CharField(max_length=255, blank=True)
    query_normalized = models.CharField(max_length=255, blank=True)
    company_raw = models.CharField(max_length=255, blank=True)
    company_normalized = models.CharField(max_length=255, blank=True)

    filters_json = models.JSONField(default=dict, blank=True)
    result_count = models.PositiveIntegerField(default=0)
    page = models.PositiveIntegerField(default=1)
    sort = models.CharField(max_length=50, blank=True)

    had_invalid_filters = models.BooleanField(default=False)
    was_whitespace_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

Indexes:

```text
created_at
user
result_count
was_whitespace_only
had_invalid_filters
query_normalized
company_normalized
```

Privacy:

```text
Do not store IP unless needed and disclosed.
Use session_hash for anonymous users.
```

## 6. CVParserAuditRun

Purpose:

```text
Record local parser audit runs against private test corpus.
```

Recommended model:

```python
class CVParserAuditRun(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)

    cv_count = models.PositiveIntegerField(default=0)
    passed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)

    metrics_json = models.JSONField(default=dict, blank=True)
    thresholds_json = models.JSONField(default=dict, blank=True)
    report_path = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

Notes:

```text
This model stores reports/metrics, not real CV files.
Real test PDFs stay local and gitignored.
```

## 7. CVParserAuditCase

Purpose:

```text
Store expected-vs-actual diff per audit case.
```

Recommended model:

```python
class CVParserAuditCase(models.Model):
    run = models.ForeignKey(CVParserAuditRun, on_delete=models.CASCADE, related_name="cases")
    case_id = models.CharField(max_length=120)

    expected_json = models.JSONField(default=dict, blank=True)
    actual_json = models.JSONField(default=dict, blank=True)
    diff_json = models.JSONField(default=dict, blank=True)

    passed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    metrics_json = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

Privacy:

```text
Expected/actual JSON must not include full CV text.
Use field-level expected outputs only.
```

## 8. CVFieldCorrection

Purpose:

```text
Capture user/admin corrections to parsed CV fields. This improves current quality and becomes future ML training data.
```

Recommended model:

```python
class CVFieldCorrection(models.Model):
    SOURCE_CHOICES = [
        ("user", "User"),
        ("admin", "Admin"),
        ("system", "System"),
    ]

    cv_upload = models.ForeignKey("cvs.CVUpload", on_delete=models.CASCADE, related_name="field_corrections")
    field_name = models.CharField(max_length=100)

    extracted_value = models.TextField(blank=True)
    corrected_value = models.TextField(blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)

    corrected_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
```

Indexes:

```text
cv_upload
field_name
source
created_at
```

Privacy:

```text
This contains personal data. Admin-only access.
Do not export without anonymization.
```

## 9. SkillExtractionFeedback

Purpose:

```text
Capture corrections/confirmations for extracted skills from CVs and jobs.
```

Recommended model:

```python
class SkillExtractionFeedback(models.Model):
    SOURCE_TYPE_CHOICES = [
        ("cv", "CV"),
        ("job", "Job"),
    ]
    ACTION_CHOICES = [
        ("confirmed", "Confirmed"),
        ("rejected", "Rejected"),
        ("mapped", "Mapped"),
        ("ignored", "Ignored"),
    ]

    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    source_public_id = models.UUIDField(db_index=True)

    raw_text = models.CharField(max_length=255)
    normalized_text = models.CharField(max_length=255, blank=True)

    extracted_skill = models.ForeignKey("skills.Skill", null=True, blank=True, on_delete=models.SET_NULL, related_name="extraction_feedback_as_extracted")
    corrected_skill = models.ForeignKey("skills.Skill", null=True, blank=True, on_delete=models.SET_NULL, related_name="extraction_feedback_as_corrected")

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
```

Indexes:

```text
source_type, source_public_id
normalized_text
action
created_at
```

Use:

```text
future ML labels
skill alias improvements
admin review quality
false positive tracking
```

## 10. JobQualityFeedback

Purpose:

```text
Capture admin feedback on job data quality.
```

Recommended model:

```python
class JobQualityFeedback(models.Model):
    REASON_CHOICES = [
        ("not_it", "Not IT"),
        ("expired", "Expired"),
        ("wrong_skills", "Wrong Skills"),
        ("wrong_level", "Wrong Level"),
        ("wrong_contract", "Wrong Contract"),
        ("bad_description", "Bad Description"),
        ("duplicate", "Duplicate"),
        ("other", "Other"),
    ]

    job = models.ForeignKey("jobs.NormalizedJob", on_delete=models.CASCADE, related_name="quality_feedback")
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
```

Indexes:

```text
job
reason
created_at
reviewed_by
```

## 11. AdminFileAccessLog

Purpose:

```text
Audit sensitive admin file access, especially CV downloads.
```

Recommended model:

```python
class AdminFileAccessLog(models.Model):
    ACTION_CHOICES = [
        ("download", "Download"),
        ("view_metadata", "View Metadata"),
    ]

    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    object_type = models.CharField(max_length=50)
    object_public_id = models.UUIDField(db_index=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    reason = models.CharField(max_length=255, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

Rules:

```text
Every admin CV download must create this log.
Do not expose filesystem path.
Do not create public CV URL.
```

## 12. AdminAlertEvent

Purpose:

```text
Record operational alerts sent or waiting to be sent to owner/admin.
```

Recommended model:

```python
class AdminAlertEvent(models.Model):
    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("sent", "Sent"),
        ("acknowledged", "Acknowledged"),
        ("resolved", "Resolved"),
        ("suppressed", "Suppressed"),
    ]

    alert_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    summary = models.CharField(max_length=255)
    details_json = models.JSONField(default=dict, blank=True)

    sent_to = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
```

Indexes:

```text
alert_type
severity
status
created_at
sent_at
```

## 13. Optional SkillRelation, deferred

Do not build unless Phase 16F needs it.

Potential future model:

```python
class SkillRelation(models.Model):
    RELATION_CHOICES = [
        ("parent_child", "Parent/Child"),
        ("ecosystem", "Ecosystem"),
        ("related", "Related"),
    ]

    parent_skill = models.ForeignKey("skills.Skill", on_delete=models.CASCADE, related_name="child_relations")
    child_skill = models.ForeignKey("skills.Skill", on_delete=models.CASCADE, related_name="parent_relations")
    relation_type = models.CharField(max_length=50, choices=RELATION_CHOICES)
    weight = models.DecimalField(max_digits=4, decimal_places=3, default=0.500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

Use cases:

```text
.NET -> ASP.NET Core
.NET -> Entity Framework Core
JavaScript -> React
JavaScript -> Node.js
```

Do not over-credit related skills in matching.

## 14. Migration order recommendation

Use this order:

```text
1. Extend/create JobIngestionConfig.
2. Add JobIngestionQueryRun.
3. Add SearchQueryLog.
4. Add AdminAlertEvent.
5. Add AdminFileAccessLog.
6. Add CVParserAuditRun / CVParserAuditCase.
7. Add CVFieldCorrection.
8. Add SkillExtractionFeedback.
9. Add JobQualityFeedback.
10. Add SkillRelation later only if needed.
```

## 15. Security/privacy notes

```text
Do not commit private_test_corpus.
Do not store real CV files in parser audit tables.
Do not store full raw CV text in logs.
Do not expose CV file URLs.
Restrict CV corrections and parser data to owner/admin.
Admin file access must be logged.
Alert emails must not include secrets or full personal data.
```
