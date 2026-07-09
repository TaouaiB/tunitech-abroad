from django.test import TestCase
from apps.cvs.services.name_extractor import CVNameExtractionService
from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService

class CVNameExtractionServiceTest(TestCase):
    def test_extract_explicit_label(self):
        text = "Nom : Dupont Jean\nExperience:\n- Dev"
        result = CVNameExtractionService.extract(text)
        self.assertEqual(result["value"], "Dupont Jean")
        self.assertEqual(result["confidence"], 95)
        
    def test_extract_top_lines(self):
        text = "JEAN DUPONT\nSoftware Engineer\nParis, France"
        result = CVNameExtractionService.extract(text)
        self.assertEqual(result["value"], "JEAN DUPONT")
        self.assertTrue(result["confidence"] >= 80)
        
    def test_reject_first_person(self):
        text = "Je suis un développeur passionné.\nJe m'appelle Jean Dupont."
        result = CVNameExtractionService.extract(text)
        self.assertIsNone(result["value"])
        self.assertIn("low_confidence_name", result["warnings"])

    def test_reject_je_me_suis_without_confident_garbage(self):
        text = "je me suis occupé du développement web\nCompétences\nPython, Django"
        result = CVNameExtractionService.extract(text)
        self.assertIsNone(result["value"])
        self.assertLess(result["confidence"], 70)
        
    def test_reject_all_lowercase_prose(self):
        text = "this is a very long sentence that should not be a name"
        result = CVNameExtractionService.extract(text)
        self.assertIsNone(result["value"])
        
    def test_reject_section_headers(self):
        text = "Experience\nEducation\nSkills"
        result = CVNameExtractionService.extract(text)
        self.assertIsNone(result["value"])
        
    def test_email_hint(self):
        text = "Software Engineer\nJean Dupont\nSomething else"
        result = CVNameExtractionService.extract(text, email="jean.dupont@example.com")
        self.assertEqual(result["value"], "Jean Dupont")
        self.assertEqual(result["confidence"], 86)

    def test_auth_user_hint(self):
        text = "Software Engineer\nJean Dupont\nSomething else"
        result = CVNameExtractionService.extract(text, auth_user_name="Jean Dupont")
        self.assertEqual(result["value"], "Jean Dupont")
        self.assertTrue(result["confidence"] >= 75)

    def test_candidates_include_reject_reasons(self):
        text = "Experience\nJean Dupont"
        result = CVNameExtractionService.extract(text)
        rejected = [candidate for candidate in result["candidates"] if candidate["reject_reason"]]
        self.assertTrue(any(candidate["reject_reason"] == "section_header" for candidate in rejected))

    def test_deterministic_extractor_exposes_confidence_and_warning_codes(self):
        text = "je me suis occupé du développement web\nContact: bad@example.test\n" + "Skills: Python, Django\n"
        result = CVDeterministicExtractorService.extract(text)
        self.assertEqual(result["extracted_name"], "")
        self.assertEqual(result["name_confidence"], 0)
        self.assertEqual(result["email_confidence"], 100)
        self.assertIn("low_confidence_name", result["warnings"])
