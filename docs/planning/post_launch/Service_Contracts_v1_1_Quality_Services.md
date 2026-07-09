# Service Contracts v1.1 — Quality, Diagnostics, Admin, and ML-Ready Services

Status: Post-launch service contracts addendum  
Product: TuniAtlas Jobs  
Purpose: Define new/updated services for v1.1 hardening

## 1. Service-layer rules

All v1 service rules remain active:

```text
Views call services.
Celery tasks call services.
Models store data.
Services own business logic.
Services should not accept raw request objects unless explicitly a thin adapter/service.
Services should not return rendered HTML.
Services should use transactions for multi-record updates.
Services called from Celery must be idempotent.
Services must not log secrets, full CV text, OAuth tokens, or API credentials.
```

## 2. JobIngestionConfigService

Location:

```text
apps/jobs/services/ingestion_config.py
```

Purpose:

```text
Read/update owner-admin ingestion configuration safely.
```

Contract:

```python
JobIngestionConfigService.get_active_config(source_slug: str) -> JobIngestionConfig
JobIngestionConfigService.update_from_admin(config_id: int, cleaned_data: dict, admin_user: User) -> JobIngestionConfig
JobIngestionConfigService.snapshot_effective_config(config: JobIngestionConfig) -> dict
```

Rules:

```text
Validate numeric limits.
Prevent negative/zero page sizes.
Prevent unrealistic max_pages_per_query unless explicitly allowed.
Store last effective config snapshot.
Do not print secrets.
```

Errors:

```text
ValidationServiceError
PermissionServiceError
NotFoundServiceError
```

## 3. JobIngestionDiagnosticsService

Location:

```text
apps/jobs/services/ingestion_diagnostics.py
```

Purpose:

```text
Explain why production visible/matchable jobs are lower than expected.
```

Contract:

```python
JobIngestionDiagnosticsService.run(source_slug: str = "france_travail") -> dict
```

Output shape:

```python
{
    "source": "france_travail",
    "active_config": {...},
    "latest_runs": [...],
    "query_runs": [...],
    "counts": {
        "raw_total": 0,
        "normalized_total": 0,
        "active": 0,
        "stale": 0,
        "expired": 0,
        "removed": 0,
        "public_visible": 0,
        "public_matchable": 0,
        "zero_skill_jobs": 0,
    },
    "normalization_statuses": {...},
    "skill_extraction_statuses": {...},
    "eligibility_reasons": {...},
    "freshness_reasons": {...},
    "celery": {...},
    "warnings": [...],
}
```

Management command:

```bash
python manage.py diagnose_job_ingestion --settings=config.settings.production
```

Acceptance:

```text
No guessing about 200 versus 1000 jobs.
Admin can see where jobs are filtered/lost.
```

## 4. JobFreshnessAuditService

Location:

```text
apps/jobs/services/freshness_audit.py
```

Purpose:

```text
Audit and validate stale/expired/removed job logic.
```

Contract:

```python
JobFreshnessAuditService.audit(now=None) -> dict
```

Output:

```text
status counts
jobs expiring soon
jobs expired by source date
jobs stale by last_seen_at
jobs removed by last_seen_at
jobs protected because latest ingestion failed
suspicious mass-status-change warnings
```

Rules:

```text
Removed threshold wins over stale threshold.
Date-only expires_at uses end of day plus grace.
Failed ingestion must not mass-stale/remove jobs.
```

## 5. JobSearchFilterService

Location:

```text
apps/jobs/services/search_filters.py
```

Purpose:

```text
Normalize and validate public search filters before JobSearchService.
```

Contract:

```python
@dataclass
class JobSearchFilters:
    q: str = ""
    company: str = ""
    published_exact: date | None = None
    published_from: date | None = None
    published_to: date | None = None
    location: str = ""
    contract_type: str = ""
    job_type: str = ""
    remote_type: str = ""
    experience_level: str = ""
    skill: str = ""
    sort: str = "newest"
    page: int = 1
    page_size: int = 20
    invalid_filters: dict = field(default_factory=dict)
    was_whitespace_only: bool = False

JobSearchFilterService.clean(raw_filters: dict, user=None) -> JobSearchFilters
```

Rules:

```text
strip q
space-only q becomes empty
strip company
space-only company becomes empty
parse dates safely
valid published_exact overrides from/to
invalid dates stored in invalid_filters, not 500
anonymous best-match sort falls back to newest/relevance
page below 1 becomes 1
page too high handled by pagination layer
```

## 6. JobSearchQualityService

Location:

```text
apps/jobs/services/search_quality.py
```

Purpose:

```text
Track and audit search quality.
```

Contracts:

```python
JobSearchQualityService.record_search(filters: JobSearchFilters, result_count: int, user=None, session_key=None) -> None
JobSearchQualityService.audit(days: int = 7) -> dict
```

Audit output:

```text
total searches
zero-result searches
whitespace-only searches
invalid filter searches
top queries
top zero-result queries
top company filters
top skill queries
```

Failure rule:

```text
Search logging failure must not break user search.
```

## 7. PublicCopyAuditService

Location:

```text
apps/core/services/public_copy_audit.py
```

Purpose:

```text
Detect public UI copy that still markets the product as France-only.
```

Contract:

```python
PublicCopyAuditService.find_forbidden_terms(paths: list[str] | None = None) -> dict
```

Management command:

```bash
python manage.py audit_public_copy --settings=config.settings.local
```

Forbidden public-copy examples:

```text
France-first
France IT jobs
France opportunities
France recruiters
French market only
```

Allowed:

```text
France Travail
France inside job location/address
France inside admin/source/internal config
```

## 8. CVNameExtractionService

Location:

```text
apps/cvs/services/name_extraction.py
```

Purpose:

```text
Extract full name from CV text with confidence and strong rejection rules.
```

Contract:

```python
CVNameExtractionService.extract(raw_text: str, user=None) -> dict
```

Output:

```python
{
    "value": "Baha Edine Taouai" | None,
    "confidence": 0.0,
    "candidates": [
        {"value": "...", "source": "top_line", "score": 0.0, "reject_reason": None}
    ],
    "warnings": ["low_confidence_name"],
}
```

Candidate sources:

```text
explicit labels: Nom, Nom et prénom, Prénom Nom, Name, Full name
top first-page text lines
email local-part hint
auth user first_name/last_name or profile full_name
optional LLM result only as supporting signal
```

Reject if candidate:

```text
contains je/me/moi/suis/j'ai/i am/my
looks like a sentence
contains profile summary phrases
contains section headers
contains email/URL/phone/date
has too many words
is job title only
is all-lowercase prose
contains verbs/common CV prose
```

Rule:

```text
Return None when confidence is low.
Never return "je me suis".
```

## 9. CVParserAuditService

Location:

```text
apps/cvs/services/parser_audit.py
```

Purpose:

```text
Run automated CV parser regression tests against private local corpus.
```

Contract:

```python
CVParserAuditService.run(cv_dir: str, expected_dir: str, output_path: str, thresholds: dict | None = None) -> dict
```

Output:

```python
{
    "cv_count": 100,
    "passed_count": 90,
    "failed_count": 10,
    "metrics": {
        "name_exact_accuracy": 0.0,
        "name_acceptable_accuracy": 0.0,
        "email_accuracy": 0.0,
        "phone_accuracy": 0.0,
        "skill_precision": 0.0,
        "skill_recall": 0.0,
        "false_skill_rate": 0.0,
    },
    "report_csv": "...",
    "report_json": "...",
    "failures": [...],
}
```

Management command:

```bash
python manage.py audit_cv_parser \
  --cv-dir private_test_corpus/cvs \
  --expected-dir private_test_corpus/expected \
  --output private_test_corpus/reports/latest.csv \
  --settings=config.settings.local
```

Rules:

```text
Do not commit real CV files.
Do not log full CV text.
Fail command if thresholds are not met.
```

## 10. CVFieldCorrectionService

Location:

```text
apps/cvs/services/corrections.py
```

Purpose:

```text
Record user/admin corrections to extracted CV fields.
```

Contract:

```python
CVFieldCorrectionService.record_correction(
    cv_upload: CVUpload,
    field_name: str,
    extracted_value: str,
    corrected_value: str,
    confidence: float | None,
    corrected_by: User | None,
    source: str,
) -> CVFieldCorrection
```

Rules:

```text
Do not expose corrections publicly.
Corrections become future ML labels.
```

## 11. SkillAliasAuditService

Location:

```text
apps/skills/services/alias_audit.py
```

Purpose:

```text
Audit skill aliases and detect ambiguous/missing mappings.
```

Contract:

```python
SkillAliasAuditService.audit() -> dict
```

Output:

```text
duplicate normalized aliases
ambiguous aliases
aliases pointing inactive skills
top unmatched skill candidates
skills with no aliases
punctuation-sensitive skills needing tests
```

Management command:

```bash
python manage.py audit_skill_aliases --settings=config.settings.local
```

## 12. SkillExtractionFeedbackService

Location:

```text
apps/skills/services/extraction_feedback.py
```

Purpose:

```text
Record confirmations/rejections/mappings of extracted skills.
```

Contract:

```python
SkillExtractionFeedbackService.record_feedback(
    source_type: str,
    source_public_id: UUID,
    raw_text: str,
    extracted_skill: Skill | None,
    corrected_skill: Skill | None,
    action: str,
    created_by: User | None,
) -> SkillExtractionFeedback
```

Use:

```text
admin skill review
future ML labels
false-positive tracking
alias improvement
```

## 13. SkillRelationshipService, deferred unless needed

Location:

```text
apps/skills/services/relationships.py
```

Purpose:

```text
Support partial matching between related skills later.
```

Contract:

```python
SkillRelationshipService.get_related_skills(skill: Skill) -> list[dict]
SkillRelationshipService.calculate_partial_credit(candidate_skill_ids: set[int], required_skill: Skill) -> float
```

Rule:

```text
Exact skill match has priority.
Related skills provide limited partial credit only.
```

## 14. AdminFileAccessService

Location:

```text
apps/core/services/admin_file_access.py
```

Purpose:

```text
Safely serve sensitive files to owner/admin and log access.
```

Contract:

```python
AdminFileAccessService.get_cv_for_download(admin_user: User, cv_public_id: UUID, reason: str, request_meta: dict) -> FileResponseData
```

Rules:

```text
superuser or explicit permission required
use CVUpload.all_objects internally
no public file URL
no filesystem path in UI
create AdminFileAccessLog
```

## 15. AdminAlertService

Location:

```text
apps/core/services/admin_alerts.py
```

Purpose:

```text
Detect anomalies and send owner/admin alerts.
```

Contracts:

```python
AdminAlertService.check_alert_conditions() -> list[AdminAlertEvent]
AdminAlertService.send_pending_alerts() -> dict
AdminAlertService.create_alert(alert_type: str, severity: str, summary: str, details: dict) -> AdminAlertEvent
```

Email destination:

```text
settings.ADMIN_ALERT_EMAIL
```

Rules:

```text
Do not hardcode email.
Do not include secrets.
Do not include full CV text.
Deduplicate repeated alerts.
Use Celery for sending.
```

## 16. AdminOpsDigestService

Location:

```text
apps/core/services/admin_ops_digest.py
```

Purpose:

```text
Send owner/admin periodic digest with operational summary.
```

Contract:

```python
AdminOpsDigestService.build_digest(period: str = "daily") -> dict
AdminOpsDigestService.send_digest(to_email: str) -> ServiceResult
```

Digest sections:

```text
users
CV uploads/parses
job ingestion
job visibility
search quality
unknown skills
recommendations
email failures
LLM cost if enabled
alerts
```

## 17. JobQualityAuditService

Location:

```text
apps/jobs/services/quality_audit.py
```

Purpose:

```text
Find jobs with weak data quality.
```

Contract:

```python
JobQualityAuditService.audit() -> dict
```

Output:

```text
zero-skill jobs
generic-skill-only jobs
jobs hidden from public
jobs pending analysis
jobs with failed normalization
jobs with failed skill extraction
jobs with suspicious dates
jobs by eligibility bucket
```

## 18. Updated task rule

Any new Celery task for these services must only call services.

Examples:

```python
@shared_task
def send_admin_alerts():
    return AdminAlertService.send_pending_alerts()

@shared_task
def run_job_ingestion_diagnostics():
    return JobIngestionDiagnosticsService.run()
```

Do not put business logic inside task functions.
