from django.test import TestCase
from django.utils import timezone
from apps.jobs.services.it_classification import JobITClassificationService
from apps.jobs.services.skill_signals import compute_deterministic_skill_signal_quality
from apps.jobs.models import JobSource, RawJobRecord, NormalizedJob, JobStatus

class ClassificationHardeningTests(TestCase):
    def test_data_engineer_gcp_with_commercial_terms(self):
        # Even with terms like 'client', it should remain IT.
        payload = {"appellationlibelle": "Data Engineer GCP"}
        desc = "Travailler pour des clients dans le secteur bancaire. Business development avec l'équipe."
        title = "Data Engineer GCP"
        
        res = JobITClassificationService.classify(payload, desc, title)
        
        # 'business development' triggers a negative reason, but it's an IT title, so should not be excluded
        self.assertTrue(res.is_it)
        self.assertEqual(res.confidence, "high")
        self.assertEqual(res.family, "data_ai_bi")

    def test_data_engineer_expert_data_integration(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "Data Engineer / Expert Data Intégration"},
            "Pipeline ETL, SQL, GCP et intégration de données.",
            "Data Engineer / Expert Data Intégration",
        )

        self.assertTrue(res.is_it)
        self.assertEqual(res.confidence, "high")
        self.assertEqual(res.family, "data_ai_bi")

    def test_tech_lead_devops(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "Tech Lead DevOps"},
            "CI/CD, Docker, Kubernetes, Terraform et cloud.",
            "Tech Lead / DevOps",
        )

        self.assertTrue(res.is_it)
        self.assertEqual(res.confidence, "high")
        self.assertEqual(res.family, "devops_cloud_sre")

    def test_fullstack_java_angular(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "Développeur fullstack Java Angular"},
            "Développement backend Java, API REST et frontend Angular.",
            "Développeur fullstack Java/Angular",
        )

        self.assertTrue(res.is_it)
        self.assertEqual(res.confidence, "high")
        self.assertIn(res.family, {"software_development", "web_mobile"})

    def test_dotnet_csharp_fullstack(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "Développeur .NET C# Fullstack"},
            "Applications métier, API, C#, .NET et frontend.",
            "Développeur .NET / C# Fullstack",
        )

        self.assertTrue(res.is_it)
        self.assertEqual(res.confidence, "high")
        self.assertEqual(res.family, "software_development")

    def test_cybersecurity_consultant_audit_delivery(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "Consultant Cybersécurité Sénior"},
            "Réaliser des audits sécurité, ISO 27001, analyse de risques et durcissement.",
            "Consultant Cybersécurité Sénior",
        )

        self.assertTrue(res.is_it)
        self.assertEqual(res.confidence, "high")
        self.assertEqual(res.family, "cybersecurity")

    def test_ingenieur_optimisation_rd_with_algorithm_evidence(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "Ingénieur en Optimisation R&D"},
            "Développer des algorithmes et de l'outillage R&D en Python.",
            "Ingénieur en Optimisation R&D",
        )

        self.assertTrue(res.is_it)
        self.assertEqual(res.confidence, "high")
        self.assertEqual(res.family, "software_development")

    def test_sdr_cyber(self):
        # SDR titles should be excluded even if they mention cybersecurity
        payload = {"appellationlibelle": "SDR Cybersécurité"}
        desc = "Vendre des solutions de cybersécurité (ISO 27001)."
        title = "SDR Cybersécurité"
        
        res = JobITClassificationService.classify(payload, desc, title)
        
        self.assertFalse(res.is_it)
        self.assertEqual(res.confidence, "excluded")
        self.assertEqual(res.family, "non_it")

    def test_bdr_cyber(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "BDR Business Developer Cybersécurité"},
            "Prospection et développement commercial d'offres cyber.",
            "BDR Business Developer Cybersécurité",
        )

        self.assertFalse(res.is_it)
        self.assertEqual(res.confidence, "excluded")
        self.assertEqual(res.family, "non_it")

    def test_charge_affaires_commercial_agencement_bois(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "Chargé d'affaires agencement bois"},
            "Commercial agencement bois, devis et relation client.",
            "Chargé d'affaires / commercial agencement bois",
        )

        self.assertFalse(res.is_it)
        self.assertEqual(res.confidence, "excluded")
        self.assertEqual(res.family, "non_it")

    def test_franchise_reseau(self):
        payload = {"appellationlibelle": "Animateur de réseau de franchise"}
        desc = "Développer les points de vente."
        title = "Animateur réseau"
        
        res = JobITClassificationService.classify(payload, desc, title)
        
        self.assertFalse(res.is_it)
        self.assertEqual(res.confidence, "excluded")
        self.assertEqual(res.family, "non_it")

    def test_franchise_network_decisive_negatives_override_developpeur_reseau(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "Animateur/trice réseau / développeur/euse réseau de franchise"},
            "Animer le réseau de franchise, accompagner les franchisés, points de vente et politique commerciale.",
            "Animateur/trice réseau / développeur/euse réseau de franchise",
        )

        self.assertFalse(res.is_it)
        self.assertEqual(res.confidence, "excluded")
        self.assertEqual(res.family, "non_it")
        
    def test_sysadmin_reseau(self):
        payload = {"appellationlibelle": "Administrateur système et réseau"}
        desc = "Gérer l'infrastructure LAN/WAN et serveurs."
        title = "Administrateur réseau"
        
        res = JobITClassificationService.classify(payload, desc, title)
        
        self.assertTrue(res.is_it)
        self.assertEqual(res.family, "systems_network")

    def test_reseau_informatique_remains_it_but_franchise_reseau_does_not(self):
        it_res = JobITClassificationService.classify(
            {"appellationlibelle": "Administrateur réseau informatique"},
            "Infrastructure réseau informatique, serveurs et supervision.",
            "Administrateur réseau informatique",
        )
        non_it_res = JobITClassificationService.classify(
            {"appellationlibelle": "Développeur réseau de franchise"},
            "Animation des franchisés et points de vente.",
            "Développeur réseau de franchise",
        )

        self.assertTrue(it_res.is_it)
        self.assertEqual(it_res.family, "systems_network")
        self.assertFalse(non_it_res.is_it)
        self.assertEqual(non_it_res.confidence, "excluded")

    def test_mediateur_cyber(self):
        payload = {"appellationlibelle": "Médiateur scientifique"}
        desc = "Sensibiliser le grand public à la cybersécurité."
        title = "Médiateur scientifique cybersécurité"
        
        res = JobITClassificationService.classify(payload, desc, title)
        
        self.assertFalse(res.is_it)
        self.assertEqual(res.confidence, "excluded")

    def test_cyber_outreach_education_decisive_negatives_override_cybersecurity(self):
        res = JobITClassificationService.classify(
            {"appellationlibelle": "Médiateur/Médiatrice scientifique - spécialité cybersécurité"},
            "Ateliers de découverte, orientation, promouvoir la filière et pédagogie pour le grand public.",
            "Médiateur/Médiatrice scientifique - spécialité cybersécurité",
        )

        self.assertFalse(res.is_it)
        self.assertEqual(res.confidence, "excluded")
        self.assertEqual(res.family, "non_it")
        
    def test_generic_consulting_transformation(self):
        payload = {"appellationlibelle": "Consultant"}
        desc = "Transformation digitale et conduite du changement. Performance commerciale."
        title = "Consultant Transformation Digitale"
        
        res = JobITClassificationService.classify(payload, desc, title)
        
        self.assertFalse(res.is_it)
        self.assertEqual(res.confidence, "excluded")

    def test_skill_signal_keeps_strong_it_positive_when_negative_terms_exist(self):
        source = JobSource.objects.create(name="Test Source", slug="test-source", is_active=True)
        raw = RawJobRecord.objects.create(
            source=source,
            source_job_id="signal-1",
            raw_payload_json={"competences": [{"libelle": "GCP", "exigence": "E"}]},
            payload_hash="signal-1",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
        )
        job = NormalizedJob.objects.create(
            source=source,
            raw_record=raw,
            source_job_id="signal-1",
            title="Data Engineer GCP",
            description="Client, reporting et business development interne.",
            status=JobStatus.ACTIVE,
            classification_json={"family": "data_ai_bi", "is_it": True, "confidence": "high"},
            required_skills_json=["GCP"],
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
        )

        signal = compute_deterministic_skill_signal_quality(job)

        self.assertEqual(signal.quality, "strong")
