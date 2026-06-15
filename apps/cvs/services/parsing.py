from django.utils import timezone
from django.db import transaction
from apps.cvs.models import CVUpload, CVParsedData
from apps.cvs.services.text_extraction import CVTextExtractionService
from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService
from apps.cvs.services.llm_extraction import CVLLMExtractionService
from apps.skills.services.normalizer import SkillNormalizerService, normalize_skill_text
from apps.profiles.models import ProfileSkill
from apps.profiles.services.completeness import ProfileCompletenessService

class CVParsingService:
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
                if not profile.full_name and det_result.get('extracted_name'):
                    profile.full_name = det_result.get('extracted_name')
                    update_fields.append('full_name')
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
                if not profile.portfolio_url and det_result.get('extracted_portfolio_url'):
                    profile.portfolio_url = det_result.get('extracted_portfolio_url')
                    update_fields.append('portfolio_url')
                if not profile.website_url and det_result.get('website_url'):
                    profile.website_url = det_result.get('website_url')
                    update_fields.append('website_url')
                    
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
