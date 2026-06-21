import json
import logging
import hashlib
import time
import urllib.error
from decimal import Decimal
from typing import Any
from django.conf import settings
from django.utils import timezone
from apps.llm.services.client import OpenRouterClient
from apps.llm.models import JobEnrichment
from apps.jobs.models import JobStatus
from django.db.models import F, Q

logger = logging.getLogger(__name__)

__all__ = [
    "get_allowed_skill_signal_qualities",
    "job_qualifies_for_enrichment_with_reason",
    "job_qualifies_for_enrichment",
    "compute_job_enrichment_payload_hash",
    "count_daily_enrichment_budget_used",
    "get_openrouter_circuit_status",
    "enqueue_job_enrichment",
    "enrich_job",
    "sanitize_enrichment_error",
    "is_enrichment_retry_eligible",
    "force_retry_provider_blocked_enrichments",
    "queue_eligible_enrichment_retries",
    "queue_selected_eligible_enrichments",
    "validate_enrichment_schema",
]

class EnrichmentReason:
    SUCCESS = "success"
    INVALID_JSON = "invalid_json"
    INVALID_JSON_RETRY_SUCCESS = "invalid_json_retry_success"
    INVALID_JSON_RETRY_FAILED = "invalid_json_retry_failed"
    VALIDATION_ERROR = "validation_error"
    PROVIDER_CIRCUIT_OPEN = "provider_circuit_open"
    PROVIDER_ERROR = "provider_error"
    RATE_LIMITED = "rate_limited"
    INSUFFICIENT_CREDITS = "insufficient_credits"
    KEY_DAILY_LIMIT_EXCEEDED = "key_daily_limit_exceeded"
    FORBIDDEN_PROVIDER_BLOCKED = "forbidden/provider_blocked"
    PROVIDER_BLOCKED = "provider_blocked"
    FORBIDDEN = "forbidden"
    MISSING_API_KEY = "missing_api_key"
    INVALID_MODEL = "invalid_model"

AUTO_RETRY_FAILURE_REASONS = {EnrichmentReason.RATE_LIMITED, EnrichmentReason.PROVIDER_ERROR}
PROVIDER_CIRCUIT_FAILURE_REASONS = {
    EnrichmentReason.PROVIDER_BLOCKED,
    EnrichmentReason.FORBIDDEN_PROVIDER_BLOCKED,
    EnrichmentReason.KEY_DAILY_LIMIT_EXCEEDED,
    EnrichmentReason.RATE_LIMITED,
    EnrichmentReason.PROVIDER_ERROR,
    EnrichmentReason.INSUFFICIENT_CREDITS,
}
PERMANENT_FAILURE_REASONS = {
    EnrichmentReason.MISSING_API_KEY,
    EnrichmentReason.FORBIDDEN,
    EnrichmentReason.FORBIDDEN_PROVIDER_BLOCKED,
    EnrichmentReason.PROVIDER_BLOCKED,
    EnrichmentReason.KEY_DAILY_LIMIT_EXCEEDED,
    EnrichmentReason.INSUFFICIENT_CREDITS,
    EnrichmentReason.VALIDATION_ERROR,
    EnrichmentReason.INVALID_MODEL,
    EnrichmentReason.INVALID_JSON_RETRY_FAILED,
}
LOW_RELEVANCE_REASON_MARKERS = (
    "does not meet minimum relevance",
    "classification confidence is not high",
    "not ACTIVE",
    "not FR",
    "does not qualify",
)
SKIPPED_BUDGET_REASON_MARKERS = (
    "daily enrichment limit reached",
    "run enrichment limit reached",
    "budget",
    "cap",
)


def get_allowed_skill_signal_qualities() -> list[str]:
    relevance_threshold = settings.JOB_ENRICHMENT_MIN_RELEVANCE
    if relevance_threshold == "strong":
        return ["strong"]
    if relevance_threshold == "partial":
        return ["strong", "partial"]
    if relevance_threshold == "generic_only":
        return ["strong", "partial", "generic_only"]
    return ["strong", "partial", "generic_only", "missing", "unknown"]


def job_qualifies_for_enrichment_with_reason(
    job,
    daily_limit: int | None = None,
    ignore_pending_reservation: bool = False,
    exclude_enrichment_id: int | None = None,
    ignore_inflight_reservation: bool = False,
) -> tuple[bool, str]:
    """
    Check if a NormalizedJob qualifies for LLM enrichment, returning (qualifies, reason).
    """
    if not settings.JOB_ENRICHMENT_ENABLED:
        return False, "JOB_ENRICHMENT_ENABLED is False"

    if job.status != JobStatus.ACTIVE:
        return False, f"Job status is {job.status}, not ACTIVE"

    if job.country != "FR":
        return False, f"Job country is {job.country}, not FR"

    classification = job.classification_json or {}
    if classification.get("confidence") != "high":
        return False, "Job classification confidence is not high"

    allowed_qualities = get_allowed_skill_signal_qualities()
    if getattr(job, "skill_signal_quality", "unknown") not in allowed_qualities:
        return False, f"Job skill signal quality '{getattr(job, 'skill_signal_quality', 'unknown')}' does not meet minimum relevance threshold '{settings.JOB_ENRICHMENT_MIN_RELEVANCE}'"

    payload_hash = compute_job_enrichment_payload_hash(job)

    if hasattr(job, "enrichment"):
        unchanged_statuses = {
            JobEnrichment.Status.SUCCESS,
        }
        if not ignore_inflight_reservation:
            unchanged_statuses.add(JobEnrichment.Status.PROCESSING)
        if not ignore_pending_reservation:
            unchanged_statuses.add(JobEnrichment.Status.PENDING)

        if job.enrichment.payload_hash == payload_hash and job.enrichment.status in unchanged_statuses:
            return False, f"{job.enrichment.get_status_display()} enrichment already exists for this payload hash"

    limit_to_use = daily_limit if daily_limit is not None else settings.JOB_ENRICHMENT_DAILY_LIMIT

    if count_daily_enrichment_budget_used(exclude_enrichment_id=exclude_enrichment_id) >= limit_to_use:
        return False, "Daily enrichment limit reached"

    return True, ""

def job_qualifies_for_enrichment(
    job,
    daily_limit: int | None = None,
    ignore_pending_reservation: bool = False,
    exclude_enrichment_id: int | None = None,
) -> bool:
    """
    Check if a NormalizedJob qualifies for LLM enrichment.
    """
    qualifies, _ = job_qualifies_for_enrichment_with_reason(
        job,
        daily_limit,
        ignore_pending_reservation,
        exclude_enrichment_id,
    )
    return qualifies

def count_daily_enrichment_budget_used(exclude_enrichment_id: int | None = None):
    """
    Count today's reserved or attempted enrichment work.

    SKIPPED rows are intentionally excluded unless they show evidence of actual
    work through attempts or token usage.
    """
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)

    queryset = JobEnrichment.objects.filter(
        created_at__gte=today_start,
        created_at__lt=today_end
    ).filter(
        Q(
            status__in=[
                JobEnrichment.Status.PENDING,
                JobEnrichment.Status.PROCESSING,
                JobEnrichment.Status.SUCCESS,
                JobEnrichment.Status.FAILED,
                JobEnrichment.Status.VALIDATION_ERROR,
            ]
        )
        | Q(attempt_count__gt=0)
        | Q(total_tokens__gt=0)
    )
    if exclude_enrichment_id is not None:
        queryset = queryset.exclude(id=exclude_enrichment_id)
    return queryset.count()


def classify_enrichment_error(enrichment: JobEnrichment) -> str:
    reason = (enrichment.status_reason or "").strip()
    error = (enrichment.last_error or "").strip()
    combined = f"{reason} {error}".lower()
    if "key_daily_limit_exceeded" in combined:
        return "key_daily_limit_exceeded"
    if "key limit exceeded" in combined and "daily limit" in combined:
        return "key_daily_limit_exceeded"
    if "insufficient" in combined and "credit" in combined:
        return "insufficient_credits"
    if "403" in combined or "401" in combined or "forbidden" in combined:
        return "forbidden/provider_blocked"
    if "rate" in combined and "limit" in combined:
        return "rate_limited"
    if reason:
        return reason
    return ""


def sanitize_enrichment_error(enrichment: JobEnrichment) -> str:
    classification = classify_enrichment_error(enrichment)
    if classification == EnrichmentReason.KEY_DAILY_LIMIT_EXCEEDED:
        return EnrichmentReason.KEY_DAILY_LIMIT_EXCEEDED
    if classification == EnrichmentReason.FORBIDDEN_PROVIDER_BLOCKED:
        return EnrichmentReason.FORBIDDEN_PROVIDER_BLOCKED
    if classification == EnrichmentReason.INSUFFICIENT_CREDITS:
        return EnrichmentReason.INSUFFICIENT_CREDITS
    if classification == EnrichmentReason.RATE_LIMITED:
        return EnrichmentReason.RATE_LIMITED
    if classification == EnrichmentReason.VALIDATION_ERROR:
        return EnrichmentReason.VALIDATION_ERROR
    if classification == EnrichmentReason.INVALID_JSON_RETRY_FAILED:
        return EnrichmentReason.INVALID_JSON_RETRY_FAILED
    return (enrichment.last_error or enrichment.status_reason or "")[:200]


def _provider_failure_queryset(now=None):
    now = now or timezone.now()
    window_start = now - timezone.timedelta(minutes=settings.OPENROUTER_CIRCUIT_BREAKER_WINDOW_MINUTES)
    return JobEnrichment.objects.filter(
        status__in=[JobEnrichment.Status.FAILED, JobEnrichment.Status.VALIDATION_ERROR],
    ).filter(
        Q(status_reason__in=PROVIDER_CIRCUIT_FAILURE_REASONS)
        | Q(last_error__icontains="HTTP Error 403")
        | Q(last_error__icontains="HTTP Error 429")
        | Q(last_error__icontains="forbidden")
        | Q(last_error__icontains="rate limited")
        | Q(last_error__icontains="key_daily_limit_exceeded")
        | Q(last_error__icontains="insufficient_credits")
    ).filter(
        Q(completed_at__gte=window_start)
        | Q(completed_at__isnull=True, updated_at__gte=window_start)
    )


def get_openrouter_circuit_status(now=None) -> dict[str, Any]:
    now = now or timezone.now()
    enabled = settings.OPENROUTER_CIRCUIT_BREAKER_ENABLED
    failures = _provider_failure_queryset(now)
    recent_failure_count = failures.count()
    latest_failure = failures.order_by(
        F("completed_at").desc(nulls_last=True),
        F("updated_at").desc(nulls_last=True),
    ).first()
    cooldown_until = None
    cooldown_remaining_seconds = 0
    if latest_failure:
        reference_time = latest_failure.completed_at or latest_failure.updated_at
        cooldown_until = reference_time + timezone.timedelta(
            minutes=settings.OPENROUTER_CIRCUIT_BREAKER_COOLDOWN_MINUTES
        )
        cooldown_remaining_seconds = max(int((cooldown_until - now).total_seconds()), 0)

    threshold_met = recent_failure_count >= settings.OPENROUTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD
    is_open = bool(enabled and threshold_met and cooldown_remaining_seconds > 0)
    return {
        "enabled": enabled,
        "is_open": is_open,
        "status": "open" if is_open else "closed",
        "latest_failure_reason": sanitize_enrichment_error(latest_failure) if latest_failure else "",
        "recent_failure_count": recent_failure_count,
        "failure_threshold": settings.OPENROUTER_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        "window_minutes": settings.OPENROUTER_CIRCUIT_BREAKER_WINDOW_MINUTES,
        "cooldown_minutes": settings.OPENROUTER_CIRCUIT_BREAKER_COOLDOWN_MINUTES,
        "cooldown_until": cooldown_until,
        "cooldown_remaining_seconds": cooldown_remaining_seconds if is_open else 0,
        "cooldown_remaining_minutes": round(cooldown_remaining_seconds / 60, 1) if is_open else 0,
    }


def _mark_provider_circuit_open(job, payload_hash: str) -> JobEnrichment:
    enrichment, _ = JobEnrichment.objects.get_or_create(
        job=job,
        defaults={"payload_hash": payload_hash},
    )
    enrichment.payload_hash = payload_hash
    enrichment.status = JobEnrichment.Status.SKIPPED
    enrichment.status_reason = EnrichmentReason.PROVIDER_CIRCUIT_OPEN
    enrichment.last_error = ""
    enrichment.prompt_tokens = 0
    enrichment.completion_tokens = 0
    enrichment.total_tokens = 0
    enrichment.estimated_cost_usd = Decimal("0")
    enrichment.raw_response_text = ""
    enrichment.raw_response_json = {}
    enrichment.save(
        update_fields=[
            "payload_hash",
            "status",
            "status_reason",
            "last_error",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "estimated_cost_usd",
            "raw_response_text",
            "raw_response_json",
            "updated_at",
        ]
    )
    return enrichment


def _queue_enrichment_task(job_id: int, *, force: bool = False) -> None:
    from apps.llm.tasks import enrich_job_task

    if force:
        enrich_job_task.delay(job_id, force=True)
    else:
        enrich_job_task.delay(job_id)


def enqueue_job_enrichment(job, *, force: bool = False) -> bool:
    payload_hash = compute_job_enrichment_payload_hash(job)
    if get_openrouter_circuit_status()["is_open"]:
        _mark_provider_circuit_open(job, payload_hash)
        return False
    _queue_enrichment_task(job.id, force=force)
    return True


def _is_stale(enrichment: JobEnrichment, now, cooldown_minutes: int) -> bool:
    reference_time = enrichment.completed_at or enrichment.started_at or enrichment.updated_at or enrichment.created_at
    return reference_time <= now - timezone.timedelta(minutes=cooldown_minutes)


def is_enrichment_retry_eligible(
    enrichment: JobEnrichment,
    *,
    now=None,
    cooldown_minutes: int | None = None,
) -> tuple[bool, str]:
    now = now or timezone.now()
    cooldown_minutes = cooldown_minutes or settings.JOB_ENRICHMENT_RETRY_COOLDOWN_MINUTES
    classification = classify_enrichment_error(enrichment)
    reason_text = f"{enrichment.status_reason or ''} {enrichment.last_error or ''}".lower()

    if enrichment.status == JobEnrichment.Status.SUCCESS:
        return False, "already success"
    if classification in PERMANENT_FAILURE_REASONS:
        return False, classification
    if any(marker.lower() in reason_text for marker in LOW_RELEVANCE_REASON_MARKERS):
        return False, "low relevance"

    if enrichment.status in [JobEnrichment.Status.PENDING, JobEnrichment.Status.PROCESSING]:
        if _is_stale(enrichment, now, cooldown_minutes):
            return True, "stale pending/processing"
        return False, "cooldown"

    if enrichment.status == JobEnrichment.Status.SKIPPED:
        if any(marker in reason_text for marker in SKIPPED_BUDGET_REASON_MARKERS):
            return True, "budget cap"
        return False, "skipped reason is not auto-retry eligible"

    if enrichment.status == JobEnrichment.Status.FAILED:
        if classification in AUTO_RETRY_FAILURE_REASONS and _is_stale(enrichment, now, cooldown_minutes):
            return True, classification
        return False, classification or "failed reason is not auto-retry eligible"

    if enrichment.status == JobEnrichment.Status.VALIDATION_ERROR:
        return False, "validation_error"

    return False, "status is not auto-retry eligible"


def _eligible_job_ids_for_enrichment(job_ids, *, limit: int, now=None) -> list[int]:
    eligible_ids: list[int] = []
    from apps.jobs.models import NormalizedJob

    if get_openrouter_circuit_status(now=now)["is_open"]:
        return eligible_ids

    for job in NormalizedJob.objects.filter(id__in=list(job_ids)).select_related("source"):
        if len(eligible_ids) >= limit:
            break
        existing = getattr(job, "enrichment", None)
        if existing:
            eligible, _ = is_enrichment_retry_eligible(existing, now=now)
            if not eligible:
                continue
        qualifies, _ = job_qualifies_for_enrichment_with_reason(
            job,
            ignore_pending_reservation=True,
            ignore_inflight_reservation=True,
            exclude_enrichment_id=existing.id if existing else None,
        )
        if qualifies:
            payload_hash = compute_job_enrichment_payload_hash(job)
            JobEnrichment.objects.update_or_create(
                job=job,
                defaults={
                    "payload_hash": payload_hash,
                    "status": JobEnrichment.Status.PENDING,
                    "status_reason": "Queued by admin/retry policy.",
                    "last_error": "",
                },
            )
            eligible_ids.append(job.id)
    return eligible_ids


def queue_selected_eligible_enrichments(
    *,
    enrichment_ids=None,
    job_ids=None,
    limit: int | None = None,
    require_retry_enabled: bool = False,
) -> int:
    if not settings.JOB_ENRICHMENT_ENABLED:
        return 0
    if require_retry_enabled and not settings.JOB_ENRICHMENT_RETRY_ENABLED:
        return 0

    limit_to_use = min(limit or settings.JOB_ENRICHMENT_RETRY_MAX_PER_RUN, settings.JOB_ENRICHMENT_RETRY_MAX_PER_RUN)
    queued_job_ids: list[int] = []
    now = timezone.now()

    if enrichment_ids is not None:
        enrichments = (
            JobEnrichment.objects.filter(id__in=list(enrichment_ids))
            .select_related("job")
            .order_by("updated_at", "created_at")
        )
        for enrichment in enrichments:
            if len(queued_job_ids) >= limit_to_use:
                break
            eligible, _ = is_enrichment_retry_eligible(enrichment, now=now)
            if not eligible:
                continue
            queued_job_ids.extend(
                _eligible_job_ids_for_enrichment([enrichment.job_id], limit=limit_to_use - len(queued_job_ids), now=now)
            )

    if job_ids is not None and len(queued_job_ids) < limit_to_use:
        queued_job_ids.extend(
            _eligible_job_ids_for_enrichment(
                job_ids,
                limit=limit_to_use - len(queued_job_ids),
                now=now,
            )
        )

    if not queued_job_ids:
        return 0

    for job_id in queued_job_ids:
        _queue_enrichment_task(job_id)
    return len(queued_job_ids)


def queue_eligible_enrichment_retries(limit: int | None = None) -> int:
    if not settings.JOB_ENRICHMENT_RETRY_ENABLED:
        return 0

    limit_to_use = min(limit or settings.JOB_ENRICHMENT_RETRY_MAX_PER_RUN, settings.JOB_ENRICHMENT_RETRY_MAX_PER_RUN)
    candidates = JobEnrichment.objects.filter(
        status__in=[
            JobEnrichment.Status.PENDING,
            JobEnrichment.Status.PROCESSING,
            JobEnrichment.Status.FAILED,
            JobEnrichment.Status.SKIPPED,
        ]
    ).order_by("updated_at", "created_at")[: limit_to_use * 5]
    return queue_selected_eligible_enrichments(
        enrichment_ids=[candidate.id for candidate in candidates],
        limit=limit_to_use,
        require_retry_enabled=True,
    )


def force_retry_provider_blocked_enrichments(*, limit: int = 1, dry_run: bool = True) -> dict[str, Any]:
    if not settings.JOB_ENRICHMENT_FORCE_PROVIDER_BLOCKED_RETRY:
        return {
            "enabled": False,
            "requested_limit": limit,
            "effective_limit": 0,
            "candidate_count": 0,
            "queued": 0,
            "dry_run": dry_run,
        }

    effective_limit = min(max(limit, 1), 3)
    candidates = list(
        JobEnrichment.objects.filter(
            status=JobEnrichment.Status.FAILED,
        ).filter(
            Q(status_reason__in=["provider_blocked", "forbidden/provider_blocked"])
            | Q(last_error__icontains="HTTP Error 403")
            | Q(last_error__icontains="forbidden")
        ).exclude(
            Q(status_reason__in=["key_daily_limit_exceeded", "insufficient_credits"])
            | Q(last_error__icontains="key_daily_limit_exceeded")
            | Q(last_error__icontains="insufficient_credits")
            | (Q(last_error__icontains="key limit exceeded") & Q(last_error__icontains="daily limit"))
            | (Q(last_error__icontains="insufficient") & Q(last_error__icontains="credit"))
        ).order_by("updated_at", "created_at")[:effective_limit]
    )

    if dry_run:
        queued = 0
    else:
        queued = 0
        for enrichment in candidates:
            if enqueue_job_enrichment(enrichment.job, force=True):
                queued += 1

    return {
        "enabled": True,
        "requested_limit": limit,
        "effective_limit": effective_limit,
        "candidate_count": len(candidates),
        "queued": queued,
        "dry_run": dry_run,
    }


def compute_job_enrichment_payload_hash(job) -> str:
    text = f"{job.title}\n{job.description}"
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def _compute_payload_hash(job) -> str:
    return compute_job_enrichment_payload_hash(job)


def _sleep_before_provider_retry(retry_number: int) -> None:
    delay = min(0.25 * (2 ** max(retry_number - 1, 0)), 2)
    time.sleep(delay)


def _safe_read_http_error_body(error: urllib.error.HTTPError, max_bytes: int = 4096) -> str:
    try:
        body = error.read(max_bytes)
    except Exception:
        return ""
    if not isinstance(body, bytes):
        return ""
    try:
        return body.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _classify_http_error(error: urllib.error.HTTPError) -> str:
    body = _safe_read_http_error_body(error)
    lower_body = body.lower()
    if error.code == 403 and "key limit exceeded" in lower_body and "daily limit" in lower_body:
        return EnrichmentReason.KEY_DAILY_LIMIT_EXCEEDED
    if "insufficient" in lower_body and "credit" in lower_body:
        return EnrichmentReason.INSUFFICIENT_CREDITS
    if error.code in (401, 403):
        return EnrichmentReason.FORBIDDEN_PROVIDER_BLOCKED
    if error.code == 429:
        return EnrichmentReason.RATE_LIMITED
    if error.code in (400, 404):
        return EnrichmentReason.INVALID_MODEL
    return EnrichmentReason.PROVIDER_ERROR

def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    return text

def enrich_job(job, force: bool = False, force_provider_call: bool = False):
    """
    Enriches a job using the LLM and validates the output.
    Updates or creates the JobEnrichment record.
    """
    if force_provider_call and not settings.DEBUG:
        raise ValueError("force_provider_call is only allowed in DEBUG mode")

    payload_hash = _compute_payload_hash(job)

    enrichment, _ = JobEnrichment.objects.get_or_create(
        job=job,
        defaults={"payload_hash": payload_hash}
    )

    if not force and not force_provider_call:
        if enrichment.status == JobEnrichment.Status.SUCCESS and enrichment.payload_hash == payload_hash:
            return enrichment

        if enrichment.status == JobEnrichment.Status.PROCESSING and enrichment.payload_hash == payload_hash:
            enrichment.status_reason = "Enrichment already processing"
            return enrichment

    if not force and not force_provider_call and not job_qualifies_for_enrichment(
        job,
        ignore_pending_reservation=True,
        exclude_enrichment_id=enrichment.id,
    ):
        enrichment.status = JobEnrichment.Status.SKIPPED
        enrichment.status_reason = "Job does not qualify or daily limit reached."
        enrichment.save(update_fields=["status", "status_reason"])
        return enrichment

    if not force_provider_call and get_openrouter_circuit_status()["is_open"]:
        return _mark_provider_circuit_open(job, payload_hash)

    enrichment.status = JobEnrichment.Status.PROCESSING
    enrichment.payload_hash = payload_hash
    enrichment.started_at = timezone.now()
    enrichment.attempt_count += 1
    enrichment.status_reason = ""
    enrichment.last_error = ""
    enrichment.validation_errors_json = []
    enrichment.save(
        update_fields=[
            "status",
            "payload_hash",
            "started_at",
            "attempt_count",
            "status_reason",
            "last_error",
            "validation_errors_json",
        ]
    )

    system_prompt = """You are an expert IT job analyzer for a job matching platform in France.
Your goal is to extract structured intelligence from a job description.

Extract facts only. Do not score candidates. Do not include soft skills as technical skills (e.g., rigueur, autonomie, bon relationnel, etc).
Allowed role_family values: software_development, web_mobile, data_ai_bi, devops_cloud_sre, cybersecurity, qa_testing, systems_network, database, erp_crm, it_support, it_project_product_analysis, it_training_apprenticeship, other
Allowed seniority values: intern, junior, mid, senior, unknown
Allowed remote_policy values: remote, hybrid, onsite, unknown
Allowed confidence values: high, medium, low

Required vs optional distinction:
- Put in required_skills ONLY if the text says it's required/indispensable/expected/maîtrise de.
- Put in optional_skills ONLY if the text says un plus, apprécié, nice to have, bonus.

Evidence rules:
- Every skill must include 'evidence', which MUST be an exact or near-exact short quote from the text.

Respond with a JSON object strictly matching this shape:
{
  "is_it_role": true,
  "role_family": "software_development",
  "normalized_role_title": "...",
  "seniority": "mid",
  "required_skills": [{"name": "Java", "evidence": "..."}],
  "optional_skills": [{"name": "C", "evidence": "..."}],
  "years_experience_min": 3,
  "languages": [{"language": "French", "level": "required", "evidence": "..."}],
  "remote_policy": "hybrid",
  "confidence": "high"
}
"""

    job_text = f"Title: {job.title}\n\nDescription:\n{job.description}"
    # Truncate if needed
    if len(job_text) > settings.JOB_ENRICHMENT_MAX_CHARS:
        job_text = job_text[:settings.JOB_ENRICHMENT_MAX_CHARS]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": job_text}
    ]

    # We do not log request messages, prompt, or raw responses for privacy/security
    enrichment.raw_request_json = {}
    enrichment.model_name = settings.JOB_ENRICHMENT_MODEL

    client = OpenRouterClient(default_model=settings.JOB_ENRICHMENT_MODEL)

    max_retries = settings.JOB_ENRICHMENT_MAX_RETRIES
    retries = 0
    success = False
    invalid_json_retry_used = False

    while retries <= max_retries and not success:
        try:
            import urllib.error
            content, usage = client.chat(messages, response_format={"type": "json_object"})

            if not isinstance(usage, dict):
                usage = {}

            enrichment.raw_response_text = content

            enrichment.prompt_tokens += usage.get("prompt_tokens", 0)
            enrichment.completion_tokens += usage.get("completion_tokens", 0)
            enrichment.total_tokens += usage.get("total_tokens", 0)
            if enrichment.total_tokens:
                enrichment.estimated_cost_usd = (Decimal(enrichment.total_tokens) / Decimal(1_000_000)) * Decimal("0.10")
            else:
                enrichment.estimated_cost_usd = Decimal("0")
                if not enrichment.status_reason:
                    enrichment.status_reason = "OpenRouter usage metadata unavailable; cost stored as zero."

            try:
                extracted_content = _extract_json(content)
                if not extracted_content:
                    raise json.JSONDecodeError("Empty or non-object output", content, 0)
                parsed_json = json.loads(extracted_content)
                if invalid_json_retry_used:
                    enrichment.status_reason = EnrichmentReason.INVALID_JSON_RETRY_SUCCESS
            except json.JSONDecodeError as e:
                if not invalid_json_retry_used:
                    invalid_json_retry_used = True
                    enrichment.last_error = f"Invalid JSON on first try: {str(e)}"
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": "Your previous response was not valid JSON. Please provide ONLY a valid JSON object matching the exact schema requested, without any markdown formatting or explanation."})
                    continue
                else:
                    enrichment.status = JobEnrichment.Status.VALIDATION_ERROR
                    enrichment.status_reason = EnrichmentReason.INVALID_JSON_RETRY_FAILED
                    enrichment.last_error = f"Invalid JSON on retry: {str(e)}"
                    enrichment.validated_output_json = {}
                    enrichment.validation_errors_json = [str(e)]
                    success = True
                    continue

            # Validate schema
            validated_data, errors = validate_enrichment_schema(parsed_json, job_text)

            if errors:
                enrichment.status = JobEnrichment.Status.VALIDATION_ERROR
                enrichment.status_reason = EnrichmentReason.VALIDATION_ERROR
                enrichment.validation_errors_json = errors
                enrichment.validated_output_json = {}
                enrichment.last_error = f"Validation failed with {len(errors)} errors"
            else:
                enrichment.status = JobEnrichment.Status.SUCCESS
                if not invalid_json_retry_used:
                    enrichment.status_reason = EnrichmentReason.SUCCESS
                enrichment.validated_output_json = validated_data
                enrichment.validation_errors_json = []
                enrichment.last_error = ""

            success = True

        except ValueError as e:
            if "OPENROUTER_API_KEY is not set" in str(e):
                enrichment.status = JobEnrichment.Status.FAILED
                enrichment.status_reason = "missing_api_key"
                enrichment.last_error = "OPENROUTER_API_KEY is not set"
                break
            else:
                retries += 1
                enrichment.status_reason = "provider_error"
                enrichment.last_error = str(e)
                if retries > max_retries:
                    enrichment.status = JobEnrichment.Status.FAILED
        except urllib.error.HTTPError as e:
            classification = _classify_http_error(e)
            if classification in {"forbidden/provider_blocked", "key_daily_limit_exceeded", "insufficient_credits"}:
                enrichment.status = JobEnrichment.Status.FAILED
                enrichment.status_reason = classification
                enrichment.last_error = f"HTTP Error {e.code}: {classification}"
                break
            elif classification == "rate_limited":
                retries += 1
                enrichment.status_reason = "rate_limited"
                enrichment.last_error = "HTTP Error 429: Rate limited"
                if retries > max_retries:
                    enrichment.status = JobEnrichment.Status.FAILED
                else:
                    _sleep_before_provider_retry(retries)
            elif classification == "invalid_model":
                enrichment.status = JobEnrichment.Status.FAILED
                enrichment.status_reason = "invalid_model"
                enrichment.last_error = f"HTTP Error {e.code}: Invalid request"
                break
            else:
                retries += 1
                enrichment.status_reason = "provider_error"
                enrichment.last_error = f"HTTP Error {e.code}"
                if retries > max_retries:
                    enrichment.status = JobEnrichment.Status.FAILED
                else:
                    _sleep_before_provider_retry(retries)
        except Exception as e:
            retries += 1
            enrichment.status_reason = "provider_error"
            enrichment.last_error = str(e)
            if retries > max_retries:
                enrichment.status = JobEnrichment.Status.FAILED

    enrichment.completed_at = timezone.now()
    enrichment.save()

    if enrichment.status == JobEnrichment.Status.SUCCESS:
        try:
            from apps.jobs.services.skill_materialization import JobSkillMaterializationService
            JobSkillMaterializationService.materialize_for_job(job, source="llm", enrichment=enrichment)
        except Exception as e:
            logger.error(f"Error materializing skills from enrichment for job {job.id}: {e}")
            from apps.jobs.models import SkillExtractionStatus
            job.skill_extraction_status = SkillExtractionStatus.FAILED
            job.save(update_fields=["skill_extraction_status"])

    return enrichment

def validate_enrichment_schema(data: Any, original_text: str) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    validated: dict[str, Any] = {}

    original_text_lower = original_text.lower()

    if not isinstance(data, dict):
        return None, ["Root is not a JSON object"]

    validated["is_it_role"] = bool(data.get("is_it_role", False))

    role_family_allowed = [
        "software_development", "web_mobile", "data_ai_bi", "devops_cloud_sre",
        "cybersecurity", "qa_testing", "systems_network", "database", "erp_crm",
        "it_support", "it_project_product_analysis", "it_training_apprenticeship", "other"
    ]
    role_family = data.get("role_family", "other")
    if role_family not in role_family_allowed:
        errors.append(f"Invalid role_family: {role_family}")
    validated["role_family"] = role_family

    validated["normalized_role_title"] = data.get("normalized_role_title", "")

    seniority_allowed = ["intern", "junior", "mid", "senior", "unknown"]
    seniority = data.get("seniority", "unknown")
    if seniority not in seniority_allowed:
        errors.append(f"Invalid seniority: {seniority}")
    validated["seniority"] = seniority

    # Skills validation
    soft_skills = ["rigueur", "autonomie", "bon relationnel", "esprit d'équipe", "communication", "curiosité"]

    def validate_skills(skills_list: Any, list_name: str) -> list[dict[str, str]]:
        valid_skills: list[dict[str, str]] = []
        if not isinstance(skills_list, list):
            errors.append(f"{list_name} is not a list")
            return valid_skills

        for skill in skills_list:
            if not isinstance(skill, dict):
                errors.append(f"Item in {list_name} is not an object")
                continue

            name = str(skill.get("name", "")).strip()
            evidence = str(skill.get("evidence", "")).strip()

            if not name:
                errors.append(f"Missing skill name in {list_name}")
                continue

            if not evidence:
                errors.append(f"Missing evidence for skill {name}")
                continue

            if name.lower() in soft_skills:
                errors.append(f"Soft skill {name} rejected")
                continue

            # Naive evidence check: words in evidence must exist in original text (at least partially)
            evidence_lower = evidence.lower()
            if evidence_lower not in original_text_lower:
                # Fallback: check if 80% of words are in the text
                ev_words = [w for w in evidence_lower.split() if len(w) > 3]
                if ev_words:
                    found_words = sum(1 for w in ev_words if w in original_text_lower)
                    if found_words / len(ev_words) < 0.5:
                        errors.append(f"Fake evidence for {name}: {evidence}")
                        continue

            valid_skills.append({"name": name, "evidence": evidence})
        return valid_skills

    validated["required_skills"] = validate_skills(data.get("required_skills", []), "required_skills")
    validated["optional_skills"] = validate_skills(data.get("optional_skills", []), "optional_skills")

    try:
        years = data.get("years_experience_min")
        validated["years_experience_min"] = int(years) if years is not None else None
    except (ValueError, TypeError):
        validated["years_experience_min"] = None

    languages = data.get("languages", [])
    validated_languages: list[dict[str, str]] = []
    if not isinstance(languages, list):
        errors.append("languages is not a list")
    else:
        for language_item in languages:
            if not isinstance(language_item, dict):
                errors.append("Item in languages is not an object")
                continue
            language = str(language_item.get("language", "")).strip()
            level = str(language_item.get("level", "")).strip()
            evidence = str(language_item.get("evidence", "")).strip()
            if not language:
                errors.append("Missing language name")
                continue
            validated_languages.append({"language": language, "level": level, "evidence": evidence})
    validated["languages"] = validated_languages

    remote_policy_allowed = ["remote", "hybrid", "onsite", "unknown"]
    remote_policy = data.get("remote_policy", "unknown")
    if remote_policy not in remote_policy_allowed:
        errors.append(f"Invalid remote_policy: {remote_policy}")
    validated["remote_policy"] = remote_policy

    confidence_allowed = ["high", "medium", "low"]
    confidence = data.get("confidence", "low")
    if confidence not in confidence_allowed:
        errors.append(f"Invalid confidence: {confidence}")
    validated["confidence"] = confidence

    return validated, errors
