import uuid
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.jobs.models import NormalizedJob, JobSource, RawJobRecord
from apps.recommendations.models import JobRecommendation, SavedJob
from apps.profiles.models import CandidateProfile
from apps.cvs.models import CVParsedData, CVUpload
from apps.matching.models import MatchResult
from apps.cvs.services.upload import CVUploadService
from apps.cvs.services.deletion import CVDeletionService
from apps.cvs.services.parsing import CVParsingService
from apps.profiles.services.profile_update import ProfileUpdateService

User = get_user_model()

def make_user(email="test@example.test"):
    username = email.split('@')[0] + str(uuid.uuid4())[:8]
    return User.objects.create(username=username, email=email, is_active=True)

def create_job(status="active"):
    source, _ = JobSource.objects.get_or_create(name="test", source_type="api")
    raw = RawJobRecord.objects.create(
        source=source,
        source_job_id=str(uuid.uuid4()),
        raw_payload_json="{}",
        payload_hash=str(uuid.uuid4()),
        first_seen_at=timezone.now(),
        last_seen_at=timezone.now(),
        last_fetched_at=timezone.now()
    )
    return NormalizedJob.objects.create(
        source=source,
        source_job_id=raw.source_job_id,
        raw_record=raw,
        title="Test Job",
        company_name="Test Co",
        description="Test Desc",
        status=status,
        first_seen_at=timezone.now(),
        last_seen_at=timezone.now(),
        last_fetched_at=timezone.now()
    )

class DashboardIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.other_user = make_user(email="other@example.test")
        self.job = create_job(status="active")

    def test_dashboard_recommendations_requires_login(self):
        url = reverse("dashboard:recommendations")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('account_login')}?next={url}")

    def test_dashboard_recommendations_authenticated(self):
        self.client.force_login(self.user)
        url = reverse("dashboard:recommendations")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_saved_jobs_requires_login(self):
        url = reverse("dashboard:saved_jobs")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('account_login')}?next={url}")

    def test_dashboard_saved_jobs_authenticated(self):
        self.client.force_login(self.user)
        SavedJob.objects.create(user=self.user, job=self.job)
        url = reverse("dashboard:saved_jobs")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.job, [sj.job for sj in response.context["saved_jobs"]])

    def test_dashboard_saved_jobs_isolation(self):
        self.client.force_login(self.user)
        SavedJob.objects.create(user=self.other_user, job=self.job)
        url = reverse("dashboard:saved_jobs")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["saved_jobs"]), 0)

    def test_recommendation_card_hides_placeholder_badges_and_links_existing_match(self):
        self.client.force_login(self.user)
        profile = CandidateProfile.objects.create(
            user=self.user,
            full_name="Amina Ben Ali",
            phone="+216 20 000 000",
            location="Tunis",
            current_level="junior",
            years_experience=2,
            target_roles=["Backend Developer"],
            target_job_types=["full_time_job"],
            target_type="job",
            french_level="intermediate",
            english_level="fluent",
            relocation_preference="yes",
            remote_preference="hybrid",
        )
        cv = CVUpload.objects.create(
            user=self.user,
            file="cvs/test.pdf",
            original_filename="amina.pdf",
            file_hash=str(uuid.uuid4()),
            file_size=1234,
            is_active=True,
            parse_status="parsed",
        )
        CVParsedData.objects.create(cv_upload=cv, raw_text="")
        self.job.contract_type = "Unknown"
        self.job.remote_type = "unknown"
        self.job.job_type = "unknown"
        self.job.experience_level = "unknown"
        self.job.published_at = None
        self.job.source_url = "https://example.test/apply"
        self.job.save(update_fields=["contract_type", "remote_type", "job_type", "experience_level", "published_at", "source_url"])
        recommendation = JobRecommendation.objects.create(
            user=self.user,
            profile=profile,
            cv_upload=cv,
            job=self.job,
            fit_score=82,
            ranking_score=82,
            rank=1,
            strong_skills_json=["Python", {"name": "Django"}],
            missing_skills_json=["PostgreSQL"],
            computed_at=timezone.now(),
            status="active",
        )
        match = MatchResult.objects.create(
            user=self.user,
            profile=profile,
            cv_upload=cv,
            job=self.job,
            profile_snapshot_json={},
            job_snapshot_json={"title": self.job.title, "company_name": self.job.company_name},
            fit_score=recommendation.fit_score,
            technical_skills_score=80,
            experience_score=80,
            role_title_score=80,
            language_score=80,
            location_score=80,
            strong_skills_json=["Python"],
            missing_required_skills_json=["PostgreSQL"],
        )

        response = self.client.get(reverse("dashboard:recommendations"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Unknown")
        self.assertNotContains(response, "unknown")
        self.assertContains(response, "82%")
        self.assertContains(response, "tta-score-ring-prominent")
        self.assertContains(response, "tta-skill-chip-success")
        self.assertContains(response, reverse("matching:detail", kwargs={"public_id": match.public_id}))
        self.assertContains(response, reverse("jobs:detail", kwargs={"public_id": self.job.public_id}))
        self.assertContains(response, "Vu le")
        self.assertNotContains(response, "Postuler sur la source")
        self.assertNotContains(response, "https://example.test/apply")

    def test_recommendation_card_hides_match_cta_when_no_match_exists(self):
        self.client.force_login(self.user)
        profile = CandidateProfile.objects.create(
            user=self.user,
            full_name="Amina Ben Ali",
            phone="+216 20 000 000",
            location="Tunis",
            current_level="junior",
            years_experience=2,
            target_roles=["Backend Developer"],
            target_job_types=["full_time_job"],
            target_type="job",
            french_level="intermediate",
            english_level="fluent",
            relocation_preference="yes",
            remote_preference="hybrid",
        )
        cv = CVUpload.objects.create(
            user=self.user,
            file="cvs/test.pdf",
            original_filename="amina.pdf",
            file_hash=str(uuid.uuid4()),
            file_size=1234,
            is_active=True,
            parse_status="parsed",
        )
        CVParsedData.objects.create(cv_upload=cv, raw_text="")
        JobRecommendation.objects.create(
            user=self.user,
            profile=profile,
            cv_upload=cv,
            job=self.job,
            fit_score=70,
            ranking_score=70,
            rank=1,
            computed_at=timezone.now(),
            status="active",
        )

        response = self.client.get(reverse("dashboard:recommendations"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Voir la compatibilité")
        self.assertContains(response, "Voir l'offre")
        self.assertNotContains(response, "Postuler sur la source")

    def test_recommendations_page_defaults_to_highest_visible_score_first(self):
        self.client.force_login(self.user)
        profile = CandidateProfile.objects.create(
            user=self.user,
            full_name="Amina Ben Ali",
            phone="+216 20 000 000",
            location="Tunis",
            current_level="junior",
            years_experience=2,
            target_roles=["Backend Developer"],
            target_job_types=["full_time_job"],
            target_type="job",
            french_level="intermediate",
            english_level="fluent",
            relocation_preference="yes",
            remote_preference="hybrid",
        )
        cv = CVUpload.objects.create(
            user=self.user,
            file="cvs/test.pdf",
            original_filename="amina.pdf",
            file_hash=str(uuid.uuid4()),
            file_size=1234,
            is_active=True,
            parse_status="parsed",
        )
        CVParsedData.objects.create(cv_upload=cv, raw_text="")
        weaker_job = create_job(status="active")
        weaker_job.title = "Junior Backend Role"
        weaker_job.save(update_fields=["title"])
        stronger_job = create_job(status="active")
        stronger_job.title = "Senior Django Role"
        stronger_job.save(update_fields=["title"])
        JobRecommendation.objects.create(
            user=self.user,
            profile=profile,
            cv_upload=cv,
            job=weaker_job,
            fit_score=61,
            ranking_score=61,
            rank=1,
            computed_at=timezone.now(),
            status="active",
        )
        JobRecommendation.objects.create(
            user=self.user,
            profile=profile,
            cv_upload=cv,
            job=stronger_job,
            fit_score=93,
            ranking_score=93,
            rank=2,
            computed_at=timezone.now(),
            status="active",
        )

        response = self.client.get(reverse("dashboard:recommendations"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertLess(content.index("Senior Django Role"), content.index("Junior Backend Role"))
        self.assertLess(content.index("93%"), content.index("61%"))

    def test_recommendation_card_warning_copy_is_professional(self):
        self.client.force_login(self.user)
        profile = CandidateProfile.objects.create(
            user=self.user,
            full_name="Amina Ben Ali",
            phone="+216 20 000 000",
            location="Tunis",
            current_level="junior",
            years_experience=2,
            target_roles=["Backend Developer"],
            target_job_types=["full_time_job"],
            target_type="job",
            french_level="intermediate",
            english_level="fluent",
            relocation_preference="yes",
            remote_preference="hybrid",
        )
        cv = CVUpload.objects.create(
            user=self.user,
            file="cvs/test.pdf",
            original_filename="amina.pdf",
            file_hash=str(uuid.uuid4()),
            file_size=1234,
            is_active=True,
            parse_status="parsed",
        )
        CVParsedData.objects.create(cv_upload=cv, raw_text="")
        JobRecommendation.objects.create(
            user=self.user,
            profile=profile,
            cv_upload=cv,
            job=self.job,
            fit_score=72,
            ranking_score=72,
            rank=1,
            missing_skills_json=["PostgreSQL"],
            computed_at=timezone.now(),
            status="active",
        )

        response = self.client.get(reverse("dashboard:recommendations"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "À renforcer")
        self.assertContains(response, "Certaines compétences obligatoires ne sont pas encore dans votre profil.")
        self.assertContains(response, "tta-skill-chip-missing")
        self.assertNotContains(response, "Points de vigilance")
        self.assertNotContains(response, "Compétences obligatoires non détectées")

    def test_saved_jobs_card_hides_placeholder_and_garbage_metadata(self):
        self.client.force_login(self.user)
        self.job.contract_type = "Unknown"
        self.job.remote_type = "unknown"
        self.job.job_type = "t"
        self.job.experience_level = "unknown"
        self.job.company_name = "t"
        self.job.location = "Unknown"
        self.job.city = "t"
        self.job.description = "t"
        self.job.published_at = None
        self.job.save(
            update_fields=[
                "contract_type",
                "remote_type",
                "job_type",
                "experience_level",
                "company_name",
                "location",
                "city",
                "description",
                "published_at",
            ]
        )
        SavedJob.objects.create(user=self.user, job=self.job)

        response = self.client.get(reverse("dashboard:saved_jobs"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Unknown")
        self.assertNotContains(response, "unknown")
        self.assertNotContains(response, ">t<", html=False)
        self.assertContains(response, "Vu le")
        self.assertContains(response, reverse("jobs:detail", kwargs={"public_id": self.job.public_id}))


class JobDetailSaveIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.job = create_job(status="active")
        self.inactive_job = create_job(status="inactive")

    def test_job_detail_save_button_authenticated(self):
        self.client.force_login(self.user)
        url = reverse("jobs:detail", kwargs={"public_id": self.job.public_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "save-button-")

    def test_job_detail_save_button_anonymous(self):
        url = reverse("jobs:detail", kwargs={"public_id": self.job.public_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "save-button-")

    def test_save_job_requires_login(self):
        url = reverse("jobs:save", kwargs={"public_id": self.job.public_id})
        response = self.client.post(url)
        self.assertRedirects(response, f"{reverse('account_login')}?next={url}")

    def test_save_job_authenticated(self):
        self.client.force_login(self.user)
        url = reverse("jobs:save", kwargs={"public_id": self.job.public_id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("jobs:detail", kwargs={"public_id": self.job.public_id}))
        self.assertTrue(SavedJob.objects.filter(user=self.user, job=self.job).exists())

    def test_unsave_job_authenticated(self):
        self.client.force_login(self.user)
        SavedJob.objects.create(user=self.user, job=self.job)
        url = reverse("jobs:unsave", kwargs={"public_id": self.job.public_id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("jobs:detail", kwargs={"public_id": self.job.public_id}))
        self.assertFalse(SavedJob.objects.filter(user=self.user, job=self.job).exists())

    def test_save_job_htmx(self):
        self.client.force_login(self.user)
        url = reverse("jobs:save", kwargs={"public_id": self.job.public_id})
        response = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/partials/save_button.html")
        self.assertTrue(response.context["is_saved"])

    def test_unsave_job_htmx(self):
        self.client.force_login(self.user)
        SavedJob.objects.create(user=self.user, job=self.job)
        url = reverse("jobs:unsave", kwargs={"public_id": self.job.public_id})
        response = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/partials/save_button.html")
        self.assertFalse(response.context["is_saved"])

    def test_save_inactive_job(self):
        self.client.force_login(self.user)
        url = reverse("jobs:save", kwargs={"public_id": self.inactive_job.public_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(SavedJob.objects.filter(user=self.user, job=self.inactive_job).exists())

    def test_save_inactive_job_htmx(self):
        self.client.force_login(self.user)
        url = reverse("jobs:save", kwargs={"public_id": self.inactive_job.public_id})
        response = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 404)

    def test_unsave_inactive_job(self):
        self.client.force_login(self.user)
        url = reverse("jobs:unsave", kwargs={"public_id": self.inactive_job.public_id})
        response = self.client.post(url)
        # remove_saved_job silently returns False for inactive job, then we redirect to jobs:detail
        self.assertEqual(response.status_code, 302)

    def test_unsave_inactive_job_htmx(self):
        self.client.force_login(self.user)
        url = reverse("jobs:unsave", kwargs={"public_id": self.inactive_job.public_id})
        response = self.client.post(url, HTTP_HX_REQUEST="true")
        # HTMX branch calls get_public_job which raises Http404
        self.assertEqual(response.status_code, 404)


class StalenessHooksTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.job = create_job(status="active")
        self.recommendation = JobRecommendation.objects.create(
            user=self.user,
            profile=CandidateProfile.objects.create(user=self.user),
            job=self.job,
            fit_score=80,
            ranking_score=80,
            rank=1,
            computed_at=timezone.now(),
            status="active"
        )

    def test_profile_update_marks_stale(self):
        ProfileUpdateService.update_profile(self.user, {"full_name": "Test Name"})
        self.recommendation.refresh_from_db()
        self.assertEqual(self.recommendation.status, "stale")

    @patch("apps.cvs.services.upload.parse_cv")
    def test_cv_upload_marks_stale(self, mock_parse_cv):
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        with self.captureOnCommitCallbacks(execute=True):
            cv = CVUploadService.upload_cv(self.user, pdf_file, consent_accepted=True)
        self.recommendation.refresh_from_db()
        self.assertEqual(self.recommendation.status, "stale")

    @patch("apps.cvs.services.upload.parse_cv")
    def test_cv_deletion_marks_stale(self, mock_parse_cv):
        pdf_content = b"%PDF-1.4\n"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        with self.captureOnCommitCallbacks(execute=True):
            cv = CVUploadService.upload_cv(self.user, pdf_file, consent_accepted=True)
        
        # Reset recommendation status because upload already marked it stale
        self.recommendation.status = "active"
        self.recommendation.save()
        
        with self.captureOnCommitCallbacks(execute=True):
            CVDeletionService.delete_cv(self.user, cv.public_id)
        self.recommendation.refresh_from_db()
        self.assertEqual(self.recommendation.status, "stale")

    @patch("apps.cvs.services.text_extraction.CVTextExtractionService.extract_text")
    @patch("apps.cvs.services.deterministic_extractor.CVDeterministicExtractorService.extract")
    @patch("apps.cvs.services.llm_extraction.CVLLMExtractionService.extract_structured")
    def test_cv_parsing_marks_stale(self, mock_llm, mock_det, mock_extract_text):
        mock_extract_text.return_value = {"success": True, "raw_text": "Sample text"}
        mock_det.return_value = {}
        mock_llm.return_value = {}
        
        cv = CVUpload.objects.create(
            user=self.user,
            file="dummy.pdf",
            file_size=1024,
            mime_type="application/pdf",
            is_active=True
        )
        
        # Reset recommendation status
        self.recommendation.status = "active"
        self.recommendation.save()
        
        CVParsingService.parse(cv)
        
        self.recommendation.refresh_from_db()
        self.assertEqual(self.recommendation.status, "stale")
