from django.conf import settings

class CVLLMExtractionService:
    @classmethod
    def extract_structured(cls, cv_upload, raw_text: str) -> dict:
        return {
            'enabled': getattr(settings, 'CV_LLM_EXTRACTION_ENABLED', False),
            'extracted_data': {},
            'warnings': ['LLM extraction is disabled in this phase.']
        }
