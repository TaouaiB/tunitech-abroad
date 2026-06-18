from django.test import TestCase
from apps.jobs.services.it_classification import JobITClassificationService, JobITClassificationResult
from apps.jobs.models import NormalizedJob, RawJobRecord, JobSource
from apps.jobs.services.normalization import JobNormalizationService
from apps.jobs.services.skill_extraction import JobSkillExtractionService
from apps.matching.services.scoring import MatchScoringService
from apps.profiles.models import CandidateProfile

class Phase14CClassificationTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="Test Source", slug="test-source", source_type="fixture")

    def test_software_app_csharp(self):
        payload = {
            "intitule": "Développeur C# / .NET",
            "description": "Nous cherchons un développeur logiciel avec maîtrise de C#, WinDev et .NET.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "software_development")
        self.assertTrue(res.is_it)
        self.assertEqual(res.confidence, "high")

    def test_mobile_automation_flutter(self):
        payload = {
            "intitule": "Ingénieur Mobile Automation",
            "description": "Stack technique: Flutter, React, Node, TypeScript, REST APIs.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "web_mobile")
        self.assertTrue(res.is_it)

    def test_as400_ibm_i(self):
        payload = {
            "intitule": "Ingénieur d'études",
            "description": "Environnement AS400, IBM i, RPG, CL, DB2.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "software_development")
        self.assertTrue(res.is_it)

    def test_salesforce_developer(self):
        payload = {
            "intitule": "Développeur Salesforce",
            "description": "Maîtrise de Salesforce et Apex requise.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "erp_crm")
        self.assertTrue(res.is_it)

    def test_data_analyst(self):
        payload = {
            "intitule": "Data Analyst (H/F)",
            "description": "Analyse de données, SQL, BI, Power BI, reporting.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "data_ai_bi")
        self.assertTrue(res.is_it)

    def test_webmaster_prestashop(self):
        payload = {
            "intitule": "Webmaster Ecommerce",
            "description": "Gestion site ecommerce Prestashop, bases en intégration.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "web_mobile")
        self.assertTrue(res.is_it)

    def test_devops_docker(self):
        payload = {
            "intitule": "Ingénieur DevOps",
            "description": "Docker, Kubernetes, Linux, Bash",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "devops_cloud_sre")
        self.assertTrue(res.is_it)

    def test_cybersecurity(self):
        payload = {
            "intitule": "Analyste Cybersécurité SOC",
            "description": "SOC, audit sécurité, ISO 27001",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "cybersecurity")
        self.assertTrue(res.is_it)

    def test_qa_test_automation(self):
        payload = {
            "intitule": "Testeur QA Automation",
            "description": "Cypress, Selenium, Playwright, tests unitaires.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "qa_testing")
        self.assertTrue(res.is_it)

    def test_photography_seller(self):
        payload = {
            "intitule": "Développeur-vendeur en photographie",
            "description": "Vente d'appareils photo, développement tirage, accueil client.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "non_it")
        self.assertFalse(res.is_it)

    def test_commercial_negative(self):
        payload = {
            "intitule": "Ingénieur commercial IT",
            "description": "Développement commercial, vente de prestations.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "non_it")
        self.assertFalse(res.is_it)

    def test_generic_web_developer(self):
        payload = {
            "intitule": "Developer",
            "description": "Participer au développement informatique de nos solutions.",
            "competences": [{"libelle": "Concevoir une application web", "exigence": "E"}]
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        # Should be fallback it
        self.assertEqual(res.family, "low_confidence_it")
        self.assertEqual(res.confidence, "low")

    def test_it_apprenticeship(self):
        payload = {
            "intitule": "alternance développeur",
            "description": "Apprentissage dev.",
            "natureContrat": "APP",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "it_training_apprenticeship")
        self.assertTrue(res.is_it)

    def test_support_negative(self):
        payload = {
            "intitule": "support client commercial",
            "description": "Assistance clientèle, gestion des commandes.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "non_it")
        self.assertFalse(res.is_it)

    def test_project_analysis_negative(self):
        payload = {
            "intitule": "chef de projet commercial",
            "description": "Organisation commerciale, suivi client, logistique.",
            "competences": []
        }
        res = JobITClassificationService.classify(payload, payload["description"], payload["intitule"])
        self.assertEqual(res.family, "non_it")
        self.assertFalse(res.is_it)

    def test_data_scientist_skill_extraction_and_scoring(self):
        from apps.skills.models import Skill, SkillAlias
        skill = Skill.objects.create(canonical_name="Python", slug="python", category="programming_language")
        SkillAlias.objects.create(skill=skill, alias="Python", normalized_alias="python")
        ml = Skill.objects.create(canonical_name="Machine Learning", slug="machine-learning", category="data_ai")
        SkillAlias.objects.create(skill=ml, alias="Machine Learning", normalized_alias="machine learning")
        pandas = Skill.objects.create(canonical_name="Pandas", slug="pandas", category="data_ai")
        SkillAlias.objects.create(skill=pandas, alias="Pandas", normalized_alias="pandas")
        
        payload = {
            "intitule": "Data Scientist",
            "description": "Mission: analyser les données. Compétences appréciées: Python, Machine Learning, Pandas.",
            "competences": [],
            "dateCreation": "2025-01-01T00:00:00Z"
        }
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id="ds123",
            raw_payload_json=payload,
            first_seen_at="2025-01-01T00:00:00Z",
            last_seen_at="2025-01-01T00:00:00Z",
            last_fetched_at="2025-01-01T00:00:00Z",
            payload_hash="hash1"
        )
        job = JobNormalizationService.normalize(raw)
        JobSkillExtractionService.extract_for_job(job)
        job.refresh_from_db()
        self.assertEqual(job.skill_signal_quality, "partial")
        self.assertEqual(job.classification_json["family"], "data_ai_bi")
        
        # Test scoring logic
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username="test", password="123", email="test@test.com")
        profile = CandidateProfile.objects.create(user=user)
        res = MatchScoringService.calculate(profile, job)
        self.assertEqual(res.match_confidence, "low_confidence")
