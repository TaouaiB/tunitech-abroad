import os
from django.test import TestCase
from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService

class CVDeterministicExtractorServiceTests(TestCase):
    def test_extract_synthetic_cv(self):
        text = """
Aymen Ben Salah
Tunis, Tunisia | +216 55 123 456 | aymen.bensalah.test@example.test | LinkedIn: linkedin.com/in/aymen-bensalah-test | GitHub: github.com/aymen-bensalah-test | Portfolio: aymen-dev.example.test

Target roles: Junior Full Stack Developer, Frontend Developer, Backend Developer, Web Developer Intern, Software Developer Intern, React Developer, Node.js Developer
Salary range: 3000-4000 TND

Skills
JavaScript, Docker, Node.js, Express.js
and role, PROJECTS, March 2025
Added filters by location
French: Professional working proficiency
English: Fluent
        """
        result = CVDeterministicExtractorService.extract(text)
        
        self.assertEqual(result['extracted_name'], "Aymen Ben Salah")
        self.assertEqual(result['extracted_location'], "Tunis, Tunisia")
        self.assertEqual(result['extracted_phone'], "+216 55 123 456")
        self.assertEqual(result['extracted_email'], "aymen.bensalah.test@example.test")
        
        self.assertEqual(result['extracted_linkedin_url'], "https://linkedin.com/in/aymen-bensalah-test")
        self.assertEqual(result['extracted_github_url'], "https://github.com/aymen-bensalah-test")
        self.assertEqual(result['extracted_portfolio_url'], "https://aymen-dev.example.test")
        
        self.assertIn("Junior Full Stack Developer", result['target_roles'])
        self.assertIn("Frontend Developer", result['target_roles'])
        self.assertIn("Backend Developer", result['target_roles'])
        self.assertIn("Web Developer Intern", result['target_roles'])
        self.assertIn("Software Developer Intern", result['target_roles'])
        self.assertIn("React Developer", result['target_roles'])
        self.assertIn("Node.js Developer", result['target_roles'])
        
        self.assertEqual(result['french_level'], "fluent")
        self.assertEqual(result['english_level'], "fluent")
        self.assertEqual(result['current_level'], "junior")
        
        skills = set(s.lower() for s in result['raw_skills'])
        self.assertIn("javascript", skills)
        self.assertIn("docker", skills)
        self.assertIn("node.js", skills)
        self.assertIn("express.js", skills)
        
        # Noise should be filtered
        self.assertNotIn("and role", skills)
        self.assertNotIn("projects", skills)
        self.assertNotIn("march 2025", skills)

    def test_cv_001_clean_english(self):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures/cv_001_clean_english_full_stack.txt'), 'r') as f:
            text = f.read()
        result = CVDeterministicExtractorService.extract(text)
        self.assertEqual(result['extracted_name'], "Jane Doe")
        self.assertEqual(result['extracted_location'], "Tunis, Tunisia")
        self.assertEqual(result['extracted_email'], "jane.doe@example.test")
        self.assertEqual(result['extracted_linkedin_url'], "https://linkedin.com/in/jane-doe")
        self.assertEqual(result['extracted_github_url'], "https://github.com/janedoe")
        self.assertEqual(result['extracted_portfolio_url'], "https://janedoe.dev")
        self.assertEqual(result['website_url'], "https://janedoe.dev")
        self.assertEqual(result['english_level'], "native")
        self.assertEqual(result['french_level'], "fluent")
        self.assertIn("Backend Developer", result['target_roles'])
        
    def test_cv_002_french_junior(self):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures/cv_002_french_junior_stage.txt'), 'r') as f:
            text = f.read()
        result = CVDeterministicExtractorService.extract(text)
        self.assertEqual(result['extracted_name'], "Mohamed Ali")
        self.assertEqual(result['extracted_location'], "Tunis, Tunisie")
        self.assertEqual(result['extracted_email'], "mohamed.ali@example.test")
        self.assertEqual(result['extracted_linkedin_url'], "https://linkedin.com/in/mohamed-ali-fr")
        self.assertEqual(result['extracted_github_url'], "https://github.com/mohamedali")
        self.assertEqual(result['extracted_portfolio_url'], "https://mohamedali.fr")
        self.assertEqual(result['french_level'], "fluent")
        self.assertEqual(result['english_level'], "intermediate")
        self.assertIn("Développeur Junior", result['target_roles'])
        self.assertIn("Stage PFE", result['target_roles'])

    def test_cv_003_student_pfe(self):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures/cv_003_student_pfe_mixed_format.txt'), 'r') as f:
            text = f.read()
        result = CVDeterministicExtractorService.extract(text)
        self.assertEqual(result['extracted_name'], "Fatma Ben Youssef")
        self.assertEqual(result['extracted_location'], "Tunis, Tunisia")
        self.assertEqual(result['extracted_linkedin_url'], "https://linkedin.com/in/fatmaby")
        self.assertIn("Frontend Developer Intern", result['target_roles'])

    def test_cv_004_messy_links(self):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures/cv_004_messy_links_multiline.txt'), 'r') as f:
            text = f.read()
        result = CVDeterministicExtractorService.extract(text)
        self.assertEqual(result['extracted_linkedin_url'], "https://linkedin.com/in/omarz")
        self.assertEqual(result['extracted_github_url'], "https://github.com/omarzribi")
        self.assertEqual(result['extracted_portfolio_url'], "https://omar.dev")

    def test_cv_005_incomplete(self):
        with open(os.path.join(os.path.dirname(__file__), 'fixtures/cv_005_incomplete_cv_missing_links.txt'), 'r') as f:
            text = f.read()
        result = CVDeterministicExtractorService.extract(text)
        self.assertEqual(result['extracted_name'], "Amira Khelil")
        self.assertEqual(result['extracted_linkedin_url'], "")
        self.assertEqual(result['extracted_github_url'], "")
        self.assertEqual(result['extracted_portfolio_url'], "")
        skills = set(s.lower() for s in result['raw_skills'])
        self.assertNotIn("private university of tunis", skills)
        
    def test_no_bad_urls(self):
        text = "Name: Test\nSkills: Next.js, React.js, Express.js"
        result = CVDeterministicExtractorService.extract(text)
        self.assertEqual(result['website_url'], "")
        self.assertEqual(result['extracted_portfolio_url'], "")

    def test_parser_does_not_invent_uncertain_career_level(self):
        text = "Amina Ben Ali\nJunior club member\nSkills: Python, Django\n" + "Project text " * 10
        result = CVDeterministicExtractorService.extract(text)
        self.assertEqual(result["current_level"], "")

    def test_current_level_uses_stored_enum_values(self):
        samples = {
            "Amina Ben Ali\n1 year experience\nSkills: Python, Django\n": "junior",
            "Amina Ben Ali\n3 years experience\nSkills: Python, Django\n": "mid",
            "Amina Ben Ali\n6 years experience\nSkills: Python, Django\n": "senior",
            "Amina Ben Ali\nTarget roles: Frontend Developer Intern\nSkills: Python, Django\n": "intern",
            "Amina Ben Ali\nStudent Developer\nSkills: Python, Django\n": "student",
        }
        for text, expected_level in samples.items():
            with self.subTest(expected_level=expected_level):
                result = CVDeterministicExtractorService.extract(text)
                self.assertEqual(result["current_level"], expected_level)
                self.assertNotIn(result["current_level"], {"Junior", "Intermédiaire", "Senior"})
