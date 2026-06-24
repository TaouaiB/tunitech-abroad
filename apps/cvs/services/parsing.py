from decimal import Decimal
import re

from django.utils import timezone
from django.db import transaction
from apps.cvs.models import CVUpload, CVParsedData
from apps.cvs.services.text_extraction import CVTextExtractionService
from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService
from apps.cvs.services.llm_extraction import CVLLMExtractionService
from apps.skills.services.normalizer import SkillNormalizerService, normalize_skill_text
from apps.profiles.models import ProfileSkill
from apps.profiles.services.completeness import ProfileCompletenessService
from apps.profiles.services.validation import CURRENT_LEVEL_CHOICES

class CVParsingService:
    CURRENT_LEVEL_VALUES = {value for value, _label in CURRENT_LEVEL_CHOICES if value}
    CURRENT_LEVEL_ALIASES = {
        "junior": "junior",
        "Junior": "junior",
        "débutant": "junior",
        "debutant": "junior",
        "intern": "intern",
        "stagiaire": "intern",
        "stage": "intern",
        "student": "student",
        "étudiant": "student",
        "etudiant": "student",
        "mid": "mid",
        "mid-level": "mid",
        "middle": "mid",
        "confirmé": "mid",
        "confirme": "mid",
        "intermédiaire": "mid",
        "intermediaire": "mid",
        "Intermédiaire": "mid",
        "senior": "senior",
        "Senior": "senior",
        "lead": "senior",
    }
    MONTH_ALIASES = {
        "january": 1,
        "janvier": 1,
        "february": 2,
        "fevrier": 2,
        "février": 2,
        "march": 3,
        "mars": 3,
        "april": 4,
        "avril": 4,
        "may": 5,
        "mai": 5,
        "june": 6,
        "juin": 6,
        "july": 7,
        "juillet": 7,
        "august": 8,
        "aout": 8,
        "août": 8,
        "september": 9,
        "septembre": 9,
        "october": 10,
        "octobre": 10,
        "november": 11,
        "novembre": 11,
        "december": 12,
        "decembre": 12,
        "décembre": 12,
    }

    @classmethod
    def _normalize_current_level(cls, value: object) -> str:
        if not isinstance(value, str):
            return ""
        cleaned = value.strip()
        if not cleaned:
            return ""
        normalized = cls.CURRENT_LEVEL_ALIASES.get(cleaned, cls.CURRENT_LEVEL_ALIASES.get(cleaned.lower(), cleaned))
        if normalized in cls.CURRENT_LEVEL_VALUES:
            return normalized
        lowered = cleaned.lower()
        for alias, level in cls.CURRENT_LEVEL_ALIASES.items():
            if re.search(rf"\b{re.escape(alias.lower())}\b", lowered):
                return level
        return ""

    @classmethod
    def _infer_target_type(cls, parsed: dict) -> str:
        roles = parsed.get("target_roles") or []
        haystack = " ".join(str(role) for role in roles)
        haystack = f"{haystack} {parsed.get('current_level', '')}".lower()

        if any(token in haystack for token in ("apprenticeship", "alternance")):
            return "apprenticeship"
        if any(token in haystack for token in ("intern", "internship", "stage", "stagiaire", "pfe")):
            return "internship"
        if "junior" in haystack or any(token in haystack for token in ("developer", "engineer", "développeur")):
            return "job"
        return ""

    @classmethod
    def _infer_target_job_types(cls, target_type: str) -> list[str]:
        if target_type == "internship":
            return ["internship"]
        if target_type == "apprenticeship":
            return ["apprenticeship"]
        if target_type == "job":
            return ["full_time_job"]
        return []

    @classmethod
    def _estimate_years_from_text(cls, raw_text: str) -> float | None:
        spans: list[tuple[int, int, int, int]] = []
        month_pattern = "|".join(re.escape(month) for month in cls.MONTH_ALIASES)
        pattern = re.compile(
            rf"\b({month_pattern})\s+(20\d{{2}})\s*(?:-|–|—|to|au|à)\s*({month_pattern}|present|current|aujourd'hui|actuel)\s*(20\d{{2}})?",
            re.IGNORECASE,
        )

        for match in pattern.finditer(raw_text):
            start_month = cls.MONTH_ALIASES.get(match.group(1).lower())
            start_year = int(match.group(2))
            end_token = match.group(3).lower()
            if end_token in {"present", "current", "aujourd'hui", "actuel"}:
                today = timezone.now().date()
                end_month = today.month
                end_year = today.year
            else:
                end_month = cls.MONTH_ALIASES.get(end_token)
                end_year = int(match.group(4) or start_year)

            if not start_month or not end_month:
                continue
            if (end_year, end_month) < (start_year, start_month):
                continue
            spans.append((start_year, start_month, end_year, end_month))

        if not spans:
            return None

        total_months = sum((end_year - start_year) * 12 + (end_month - start_month) + 1 for start_year, start_month, end_year, end_month in spans)
        years = max(Decimal("0.1"), (Decimal(total_months) / Decimal(12)).quantize(Decimal("0.1")))
        return float(min(years, Decimal("40.0")))

    @classmethod
    def parse_by_id(cls, cv_upload_id: int) -> CVParsedData | None:
        try:
            cv_upload = CVUpload.all_objects.get(id=cv_upload_id)
        except CVUpload.DoesNotExist:
            return None
            
        return cls.parse(cv_upload)

    @classmethod
    def parse(cls, cv_upload: CVUpload) -> CVParsedData | None:
        if not cv_upload.is_active or cv_upload.deleted_at is not None:
            return None
            
        cv_upload.parse_status = 'processing'
        cv_upload.save(update_fields=['parse_status'])
        
        text_result = CVTextExtractionService.extract_text(cv_upload)
        if not text_result['success']:
            cv_upload.parse_status = 'failed'
            cv_upload.text_extraction_status = text_result.get('status', 'failed')
            cv_upload.extracted_text_length = len(text_result.get('raw_text', ''))
            cv_upload.parse_error = text_result.get('error', '')
            CVParsedData.objects.update_or_create(
                cv_upload=cv_upload,
                defaults={
                    'raw_text': text_result.get('raw_text', ''),
                    'extraction_method': 'failed',
                    'warnings_json': [text_result.get('error', 'Text extraction failed')],
                }
            )
            cv_upload.save(update_fields=['parse_status', 'text_extraction_status', 'extracted_text_length', 'parse_error'])
            return None
            
        raw_text = text_result['raw_text']
        cv_upload.text_extraction_status = 'success'
        cv_upload.extracted_text_length = len(raw_text)
        
        det_result = CVDeterministicExtractorService.extract(raw_text)
        if det_result.get('estimated_years_experience') is None:
            estimated_from_dates = cls._estimate_years_from_text(raw_text)
            if estimated_from_dates is not None:
                det_result['estimated_years_experience'] = estimated_from_dates
                if not det_result.get('current_level'):
                    det_result['current_level'] = 'junior' if estimated_from_dates < Decimal("2.0") else 'mid'
        if not det_result.get('current_level') and det_result.get('target_roles'):
            det_result['current_level'] = cls._normalize_current_level(" ".join(det_result['target_roles']))
        inferred_target_type = cls._infer_target_type(det_result)
        if inferred_target_type:
            det_result['target_type'] = inferred_target_type
        llm_result = CVLLMExtractionService.extract_structured(cv_upload, raw_text)
        
        with transaction.atomic():
            parsed_data, _ = CVParsedData.objects.update_or_create(
                cv_upload=cv_upload,
                defaults={
                    'raw_text': raw_text,
                    'deterministic_json': det_result,
                    'llm_json': llm_result,
                    'extraction_method': 'regex_only',
                    'merged_json': det_result,
                    'extracted_name': det_result.get('extracted_name', ''),
                    'extracted_email': det_result.get('extracted_email', ''),
                    'extracted_phone': det_result.get('extracted_phone', ''),
                    'extracted_location': det_result.get('extracted_location', ''),
                    'extracted_linkedin_url': det_result.get('extracted_linkedin_url', ''),
                    'extracted_github_url': det_result.get('extracted_github_url', ''),
                    'extracted_portfolio_url': det_result.get('extracted_portfolio_url', ''),
                    'estimated_years_experience': det_result.get('estimated_years_experience', None),
                    'warnings_json': det_result.get('warnings', []) + llm_result.get('warnings', [])
                }
            )
            
            raw_skills = det_result.get('raw_skills', [])
            normalization_result = SkillNormalizerService.normalize_many(
                raw_skills=raw_skills,
                source_type='cv',
                source_id=cv_upload.id
            )
            
            canonical_skills = normalization_result.canonical_skills
            
            user = cv_upload.user
            if hasattr(user, 'candidate_profile'):
                profile = user.candidate_profile
                
                update_fields = []
                extracted_name = det_result.get('extracted_name')
                if extracted_name:
                    if not profile.full_name:
                        profile.full_name = extracted_name
                        update_fields.append('full_name')
                    elif profile.full_name != extracted_name:
                        warning_msg = f"Profile name '{profile.full_name}' differs from CV name '{extracted_name}'."
                        if not isinstance(parsed_data.warnings_json, list):
                            parsed_data.warnings_json = []
                        if warning_msg not in parsed_data.warnings_json:
                            parsed_data.warnings_json.append(warning_msg)
                            parsed_data.save(update_fields=['warnings_json'])

                if not profile.phone and det_result.get('extracted_phone'):
                    profile.phone = det_result.get('extracted_phone')
                    update_fields.append('phone')
                if not profile.location and det_result.get('extracted_location'):
                    profile.location = det_result.get('extracted_location')
                    update_fields.append('location')
                if not profile.linkedin_url and det_result.get('extracted_linkedin_url'):
                    profile.linkedin_url = det_result.get('extracted_linkedin_url')
                    update_fields.append('linkedin_url')
                if not profile.github_url and det_result.get('extracted_github_url'):
                    profile.github_url = det_result.get('extracted_github_url')
                    update_fields.append('github_url')
                if det_result.get('portfolio_url') or det_result.get('extracted_portfolio_url'):
                    new_portfolio = det_result.get('portfolio_url') or det_result.get('extracted_portfolio_url')
                    if not profile.portfolio_url or profile.portfolio_url.lower() in ['https://next.js', 'https://react.js', 'https://node.js']:
                        profile.portfolio_url = new_portfolio
                        update_fields.append('portfolio_url')
                if det_result.get('website_url'):
                    if not profile.website_url or profile.website_url.lower() in ['https://next.js', 'https://react.js', 'https://node.js']:
                        profile.website_url = det_result.get('website_url')
                        update_fields.append('website_url')
                if not profile.french_level and det_result.get('french_level'):
                    profile.french_level = det_result.get('french_level')
                    update_fields.append('french_level')
                if not profile.english_level and det_result.get('english_level'):
                    profile.english_level = det_result.get('english_level')
                    update_fields.append('english_level')
                if not profile.target_roles and det_result.get('target_roles'):
                    profile.target_roles = det_result.get('target_roles')
                    update_fields.append('target_roles')
                inferred_target_type = det_result.get('target_type') or cls._infer_target_type(det_result)
                if not profile.target_type and inferred_target_type:
                    profile.target_type = inferred_target_type
                    update_fields.append('target_type')
                inferred_job_types = cls._infer_target_job_types(inferred_target_type)
                if not profile.target_job_types and inferred_job_types:
                    profile.target_job_types = inferred_job_types
                    update_fields.append('target_job_types')
                extracted_level = cls._normalize_current_level(det_result.get('current_level'))
                if not profile.current_level and extracted_level:
                    profile.current_level = extracted_level
                    update_fields.append('current_level')
                if profile.years_experience is None and det_result.get('estimated_years_experience') is not None:
                    profile.years_experience = det_result.get('estimated_years_experience')
                    update_fields.append('years_experience')
                    
                if update_fields:
                    profile.save(update_fields=update_fields)
                    
                existing_normalized = set(
                    ProfileSkill.objects.filter(profile=profile).values_list('normalized_name', flat=True)
                )
                
                new_profile_skills = []
                for skill in canonical_skills:
                    normalized_name = normalize_skill_text(skill.canonical_name)
                    if normalized_name not in existing_normalized:
                        new_profile_skills.append(
                            ProfileSkill(
                                profile=profile,
                                raw_name=skill.canonical_name,
                                normalized_name=normalized_name,
                                source='cv_upload',
                                confidence=80,
                                is_confirmed=False
                            )
                        )
                        existing_normalized.add(normalized_name)
                        
                if new_profile_skills:
                    ProfileSkill.objects.bulk_create(new_profile_skills, ignore_conflicts=True)
                    
                ProfileCompletenessService.calculate(profile)

            status = 'parsed_with_warnings' if parsed_data.warnings_json else 'parsed'
            cv_upload.parse_status = status
            cv_upload.parsed_at = timezone.now()
            cv_upload.save(update_fields=['parse_status', 'parsed_at', 'text_extraction_status', 'extracted_text_length'])
            
            try:
                from apps.recommendations.services.staleness import RecommendationStalenessService
                RecommendationStalenessService.mark_user_recommendations_stale(cv_upload.user, reason="cv_parsed")
            except ImportError:
                pass
                
            return parsed_data
