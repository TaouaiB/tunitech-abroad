from django.test import TestCase
from apps.cvs.services.llm_extraction import CVLLMExtractionService
from apps.cvs.models import CVUpload
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

User = get_user_model()

class CVWarningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@example.com")
        self.dummy_cv = CVUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("dummy.pdf", b"dummy content"),
            file_size=1024,
            parse_status='parsed'
        )

    def test_cv_warning_removed(self):
        result = CVLLMExtractionService.extract_structured(self.dummy_cv, "raw text")
        
        self.assertIn('warnings', result)
        self.assertNotIn("LLM extraction is disabled in this phase.", result['warnings'])
        self.assertEqual(len(result['warnings']), 0)
