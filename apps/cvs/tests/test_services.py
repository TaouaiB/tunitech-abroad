from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.cvs.models import CVUpload
from apps.cvs.services.upload import CVUploadService
from apps.cvs.services.text_extraction import CVTextExtractionService
from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService
from apps.cvs.services.deletion import CVDeletionService
from apps.cvs.services.parsing import CVParsingService
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.skills.models import Skill, SkillAlias
from apps.skills.services.normalizer import normalize_skill_text
import fitz

UserModel = get_user_model()


def create_test_user(
    *,
    username: str,
    email: str,
    password: str = "pw",
    is_staff: bool = False,
) -> AbstractBaseUser:
    user = UserModel.objects.create(
        username=username,
        email=email,
        is_staff=is_staff,
    )
    user.set_password(password)
    user.save(update_fields=["password"])
    return user


class CVServiceTests(TestCase):
    def setUp(self):
        self.user = create_test_user(username="testuser2", email="test2@test.com", password="password")

    @patch('apps.cvs.services.upload.parse_cv.delay')
    def test_upload_cv_success(self, mock_delay):
        file = SimpleUploadedFile("test.pdf", b"pdf_content", content_type="application/pdf")
        with self.captureOnCommitCallbacks(execute=True):
            cv = CVUploadService.upload_cv(self.user, file, consent_accepted=True)
        self.assertEqual(cv.user, self.user)
        self.assertTrue(cv.is_active)
        self.assertEqual(CVUpload.objects.count(), 1)
        mock_delay.assert_called_once_with(cv.id)
        
    def test_upload_cv_no_consent(self):
        file = SimpleUploadedFile("test.pdf", b"pdf_content", content_type="application/pdf")
        with self.assertRaises(ValueError):
            CVUploadService.upload_cv(self.user, file, consent_accepted=False)

    def test_upload_cv_rejects_non_pdf_in_service(self):
        file = SimpleUploadedFile("test.txt", b"text", content_type="text/plain")
        with self.assertRaises(ValueError):
            CVUploadService.upload_cv(self.user, file, consent_accepted=True)

    def test_upload_cv_rejects_oversized_file_in_service(self):
        file = SimpleUploadedFile("large.pdf", b"x" * (6 * 1024 * 1024), content_type="application/pdf")
        with self.assertRaises(ValueError):
            CVUploadService.upload_cv(self.user, file, consent_accepted=True)

    def test_deterministic_extractor(self):
        text = "Amina Ben Ali\nLocation: Tunis\nContact me at test@test.com or +33 6 12 34 56 78.\nLinkedIn: https://linkedin.com/in/test\nGitHub: https://github.com/test\nPortfolio: https://amina.dev\nSkills:\nPython, Django, React"
        result = CVDeterministicExtractorService.extract(text)
        self.assertEqual(result['extracted_name'], "Amina Ben Ali")
        self.assertEqual(result['extracted_location'], "Tunis")
        self.assertEqual(result['extracted_email'], "test@test.com")
        self.assertEqual(result['extracted_linkedin_url'], "https://linkedin.com/in/test")
        self.assertEqual(result['extracted_github_url'], "https://github.com/test")
        self.assertEqual(result['extracted_portfolio_url'], "https://amina.dev")
        self.assertIn("python", [s.lower() for s in result['raw_skills']])

    def test_text_extraction_success_and_too_little_text(self):
        readable_pdf = self._pdf_file("Amina Ben Ali\n" + "Python Django PostgreSQL " * 5)
        short_pdf = self._pdf_file("Tiny")
        readable_cv = CVUpload.objects.create(
            user=self.user, file=readable_pdf, original_filename="readable.pdf",
            file_hash="hash", file_size=readable_pdf.size, is_active=True
        )
        result = CVTextExtractionService.extract_text(readable_cv)
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'success')

        readable_cv.is_active = False
        readable_cv.save(update_fields=['is_active'])
        short_cv = CVUpload.objects.create(
            user=self.user, file=short_pdf, original_filename="short.pdf",
            file_hash="hash2", file_size=short_pdf.size, is_active=True
        )
        result = CVTextExtractionService.extract_text(short_cv)
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'too_little_text')

    @patch('apps.cvs.services.parsing.CVLLMExtractionService.extract_structured')
    def test_parsing_prefills_blanks_and_keeps_existing_values_idempotently(self, mock_llm):
        mock_llm.return_value = {'enabled': False, 'extracted_data': {}, 'warnings': []}
        skill = Skill.objects.create(canonical_name="Python", slug="python", category="backend")
        SkillAlias.objects.create(skill=skill, alias="Python", normalized_alias=normalize_skill_text("Python"))
        profile = CandidateProfile.objects.create(
            user=self.user,
            full_name="Existing Name",
            phone="+216 11 111 111",
        )
        pdf = self._pdf_file(
            "Amina Ben Ali\n"
            "Location: Tunis\n"
            "Email: amina@example.com\n"
            "Phone: +33 6 12 34 56 78\n"
            "LinkedIn: https://linkedin.com/in/amina\n"
            "GitHub: https://github.com/amina\n"
            "Portfolio: https://amina.dev\n"
            "Skills:\n"
            "Python\n"
        )
        cv = CVUpload.objects.create(
            user=self.user, file=pdf, original_filename="cv.pdf",
            file_hash="hash3", file_size=pdf.size, is_active=True
        )

        CVParsingService.parse(cv)
        CVParsingService.parse(cv)

        profile.refresh_from_db()
        self.assertEqual(profile.full_name, "Existing Name")
        self.assertEqual(profile.phone, "+216 11 111 111")
        self.assertEqual(profile.location, "Tunis")
        self.assertEqual(profile.linkedin_url, "https://linkedin.com/in/amina")
        self.assertEqual(ProfileSkill.objects.filter(profile=profile, normalized_name="python").count(), 1)
        
    def test_deletion_service(self):
        file = SimpleUploadedFile("test.pdf", b"pdf_content", content_type="application/pdf")
        cv = CVUpload.objects.create(
            user=self.user, file=file, original_filename="test.pdf",
            file_hash="hash", file_size=1, is_active=True
        )
        result = CVDeletionService.delete_cv(self.user, cv.public_id)
        self.assertTrue(result['success'])
        self.assertEqual(CVUpload.objects.count(), 0)
        self.assertEqual(CVUpload.all_objects.count(), 1)

    def _pdf_file(self, text: str) -> SimpleUploadedFile:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text)
        content = doc.tobytes()
        doc.close()
        return SimpleUploadedFile("sample.pdf", content, content_type="application/pdf")
