import json
import logging
import hashlib
from decimal import Decimal
from typing import Any
from django.conf import settings
from django.utils import timezone
from apps.llm.services.client import OpenRouterClient
from apps.llm.models import JobEnrichment
from apps.jobs.models import JobStatus

logger = logging.getLogger(__name__)

__all__ = [
    "job_qualifies_for_enrichment_with_reason",
    "job_qualifies_for_enrichment",
    "enrich_job",
    "validate_enrichment_schema",
]


def job_qualifies_for_enrichment_with_reason(job) -> tuple[bool, str]:
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

    # Payload hash check to avoid duplicate enrichment
    payload_hash = _compute_payload_hash(job)
    
    # Check if a successful enrichment already exists for this hash
    if hasattr(job, "enrichment") and job.enrichment.status == JobEnrichment.Status.SUCCESS:
        if job.enrichment.payload_hash == payload_hash:
            return False, "Successful enrichment already exists for this payload hash"

    # Check daily limit
    today = timezone.now().date()
    daily_count = JobEnrichment.objects.filter(
        created_at__date=today,
    ).exclude(status=JobEnrichment.Status.PENDING).count()
    
    if daily_count >= settings.JOB_ENRICHMENT_DAILY_LIMIT:
        return False, "Daily enrichment limit reached"

    return True, ""

def job_qualifies_for_enrichment(job) -> bool:
    """
    Check if a NormalizedJob qualifies for LLM enrichment.
    """
    qualifies, _ = job_qualifies_for_enrichment_with_reason(job)
    return qualifies

def _compute_payload_hash(job) -> str:
    text = f"{job.title}\n{job.description}"
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def enrich_job(job, force: bool = False):
    """
    Enriches a job using the LLM and validates the output.
    Updates or creates the JobEnrichment record.
    """
    payload_hash = _compute_payload_hash(job)
    
    enrichment, _ = JobEnrichment.objects.get_or_create(
        job=job,
        defaults={"payload_hash": payload_hash}
    )

    if not force and enrichment.status == JobEnrichment.Status.SUCCESS and enrichment.payload_hash == payload_hash:
        return enrichment
        
    if not force and not job_qualifies_for_enrichment(job):
        enrichment.status = JobEnrichment.Status.SKIPPED
        enrichment.status_reason = "Job does not qualify or daily limit reached."
        enrichment.save()
        return enrichment

    enrichment.status = JobEnrichment.Status.PROCESSING
    enrichment.payload_hash = payload_hash
    enrichment.started_at = timezone.now()
    enrichment.attempt_count += 1
    enrichment.save(update_fields=["status", "payload_hash", "started_at", "attempt_count"])

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

    enrichment.raw_request_json = {"messages": messages}
    enrichment.model_name = settings.JOB_ENRICHMENT_MODEL

    client = OpenRouterClient(default_model=settings.JOB_ENRICHMENT_MODEL)
    
    max_retries = settings.JOB_ENRICHMENT_MAX_RETRIES
    retries = 0
    success = False
    
    while retries <= max_retries and not success:
        try:
            content, usage = client.chat(messages, response_format={"type": "json_object"})
            
            enrichment.raw_response_text = content
            if not isinstance(usage, dict):
                usage = {}

            enrichment.prompt_tokens = usage.get("prompt_tokens", 0)
            enrichment.completion_tokens = usage.get("completion_tokens", 0)
            enrichment.total_tokens = usage.get("total_tokens", 0)
            if enrichment.total_tokens:
                enrichment.estimated_cost_usd = (Decimal(enrichment.total_tokens) / Decimal(1_000_000)) * Decimal("0.10")
            else:
                enrichment.estimated_cost_usd = Decimal("0")
                enrichment.status_reason = "OpenRouter usage metadata unavailable; cost stored as zero."
            
            try:
                parsed_json = json.loads(content)
                enrichment.raw_response_json = parsed_json
            except json.JSONDecodeError as e:
                raise ValueError("LLM response is not valid JSON")

            # Validate schema
            validated_data, errors = validate_enrichment_schema(parsed_json, job_text)
            
            if errors:
                enrichment.status = JobEnrichment.Status.VALIDATION_ERROR
                enrichment.validation_errors_json = errors
                enrichment.validated_output_json = {}
                enrichment.last_error = f"Validation failed with {len(errors)} errors"
            else:
                enrichment.status = JobEnrichment.Status.SUCCESS
                enrichment.validated_output_json = validated_data
                enrichment.validation_errors_json = []
                enrichment.last_error = ""
            
            success = True
            
        except Exception as e:
            retries += 1
            enrichment.last_error = str(e)
            if retries > max_retries:
                enrichment.status = JobEnrichment.Status.FAILED

    enrichment.completed_at = timezone.now()
    enrichment.save()
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
