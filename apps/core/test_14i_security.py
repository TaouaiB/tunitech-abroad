from pathlib import Path

from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

from apps.cvs.models import CVParsedData, CVUpload
from apps.jobs.models import JobSource, NormalizedJob, RawJobRecord
from apps.matching.models import MatchResult
from apps.notifications.models import EmailPreference
from apps.profiles.models import CandidateProfile
from apps.recommendations.models import SavedJob

User = get_user_model()

class Phase14ISecurityTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username="usera", email="usera@example.test", password="password")
        self.user_b = User.objects.create_user(username="userb", email="userb@example.test", password="password")

        self.source = JobSource.objects.create(
            name="Security Fixture",
            slug=f"security-fixture-{uuid.uuid4()}",
            source_type="fixture",
        )
        self.job = self._create_job("security-job-a", "Phase 14I Python Developer")
        self.other_job = self._create_job("security-job-b", "Phase 14I Private Saved Job")

        self.profile_a = CandidateProfile.objects.create(
            user=self.user_a,
            public_id=uuid.uuid4(),
            current_level="junior",
            target_country="FR",
            target_roles=[],
            french_level="B2",
        )
        self.profile_b = CandidateProfile.objects.create(
            user=self.user_b,
            public_id=uuid.uuid4(),
            current_level="junior",
            target_country="FR",
            target_roles=[],
            french_level="B2",
        )

        self.cv_a = CVUpload.objects.create(
            user=self.user_a,
            public_id=uuid.uuid4(),
            original_filename="a_cv.pdf",
            file_hash="dummyhash-a",
            file_size=100,
            is_active=True,
            parse_status="parsed",
        )
        self.cv_b = CVUpload.objects.create(
            user=self.user_b,
            public_id=uuid.uuid4(),
            original_filename="b_cv.pdf",
            file_hash="dummyhash",
            file_size=100,
            is_active=True,
            parse_status="parsed",
        )
        CVParsedData.objects.create(cv_upload=self.cv_a, raw_text="SECRET_RAW_CV_TEXT_A")
        CVParsedData.objects.create(cv_upload=self.cv_b, raw_text="SECRET_RAW_CV_TEXT_B")

        self.match_b = MatchResult.objects.create(
            public_id=uuid.uuid4(),
            user=self.user_b,
            profile=self.profile_b,
            job=self.job,
            fit_score=80,
            technical_skills_score=80,
            experience_score=80,
            role_title_score=80,
            language_score=80,
            location_score=80,
            profile_snapshot_json={},
            job_snapshot_json={}
        )

        self.client_a = Client()
        self.client_a.force_login(self.user_a)

        self.client_b = Client()
        self.client_b.force_login(self.user_b)

        self.client_anon = Client()

    def _create_job(self, source_job_id, title):
        now = timezone.now()
        raw = RawJobRecord.objects.create(
            source=self.source,
            source_job_id=source_job_id,
            raw_payload_json={},
            payload_hash=f"hash-{source_job_id}",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        return NormalizedJob.objects.create(
            source=self.source,
            raw_record=raw,
            source_job_id=source_job_id,
            title=title,
            company_name="Security Co",
            location="Paris",
            remote_type="remote",
            job_type="full_time_job",
            experience_level="junior",
            description="Build secure software.",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )

    def test_anonymous_blocked_from_dashboard(self):
        response = self.client_anon.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_anonymous_blocked_from_private_routes(self):
        private_urls = [
            reverse("dashboard:home"),
            reverse("dashboard:profile"),
            reverse("dashboard:cv"),
            reverse("dashboard:cv_status", kwargs={"public_id": self.cv_a.public_id}),
            reverse("dashboard:recommendations"),
            reverse("dashboard:saved_jobs"),
            reverse("dashboard:email_preferences"),
            reverse("dashboard:account"),
            reverse("dashboard:connections"),
            reverse("dashboard:delete_account"),
            reverse("matching:history"),
            reverse("matching:detail", kwargs={"public_id": self.match_b.public_id}),
        ]

        for url in private_urls:
            with self.subTest(url=url):
                response = self.client_anon.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("login", response.url)

    def test_authenticated_user_allowed_on_own_private_routes(self):
        private_urls = [
            reverse("dashboard:home"),
            reverse("dashboard:profile"),
            reverse("dashboard:cv"),
            reverse("dashboard:cv_status", kwargs={"public_id": self.cv_a.public_id}),
            reverse("dashboard:recommendations"),
            reverse("dashboard:saved_jobs"),
            reverse("dashboard:email_preferences"),
            reverse("dashboard:account"),
            reverse("dashboard:connections"),
            reverse("dashboard:delete_account"),
            reverse("matching:history"),
        ]

        for url in private_urls:
            with self.subTest(url=url):
                response = self.client_a.get(url)
                self.assertEqual(response.status_code, 200)

    def test_inactive_user_and_logout_clear_private_access(self):
        response = self.client_a.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)

        self.user_a.is_active = False
        self.user_a.save(update_fields=["is_active"])
        response = self.client_a.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)

        self.user_b.is_active = True
        self.user_b.save(update_fields=["is_active"])
        self.client_b.logout()
        response = self.client_b.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)

    def test_public_pages_remain_public(self):
        public_urls = [
            reverse("core:home"),
            reverse("jobs:list"),
            reverse("jobs:detail", kwargs={"public_id": self.job.public_id}),
            reverse("privacy:privacy_policy"),
            reverse("privacy:terms"),
            reverse("health"),
        ]

        for url in public_urls:
            with self.subTest(url=url):
                response = self.client_anon.get(url)
                self.assertEqual(response.status_code, 200)

    def test_anonymous_blocked_from_save_job(self):
        response = self.client_anon.post(reverse("jobs:save", kwargs={"public_id": self.job.public_id}))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_user_a_blocked_from_user_b_cv_status(self):
        url = reverse("dashboard:cv_status", kwargs={"public_id": self.cv_b.public_id})
        response = self.client_a.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_a_blocked_from_user_b_cv_status_htmx(self):
        url = reverse("dashboard:cv_status", kwargs={"public_id": self.cv_b.public_id})
        response = self.client_a.get(url, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 404)

    def test_user_a_blocked_from_user_b_cv_delete(self):
        url = reverse("dashboard:cv")
        response = self.client_a.post(url, {"delete_cv_id": str(self.cv_b.public_id)})
        self.cv_b.refresh_from_db()
        # Ensure CV is not deleted by User A's action
        self.assertTrue(self.cv_b.is_active)
        self.assertIsNone(self.cv_b.deleted_at)

    def test_user_a_blocked_from_user_b_match_detail(self):
        url = reverse("matching:detail", kwargs={"public_id": self.match_b.public_id})
        response = self.client_a.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_a_cannot_view_or_mutate_user_b_saved_jobs(self):
        SavedJob.objects.create(user=self.user_b, job=self.other_job)

        response = self.client_a.get(reverse("dashboard:saved_jobs"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.other_job.title)

        response = self.client_a.post(reverse("jobs:unsave", kwargs={"public_id": self.other_job.public_id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SavedJob.objects.filter(user=self.user_b, job=self.other_job).exists())

    def test_user_a_email_preference_post_mutates_only_user_a(self):
        pref_a = EmailPreference.objects.create(user=self.user_a, weekly_digest_enabled=False)
        pref_b = EmailPreference.objects.create(user=self.user_b, weekly_digest_enabled=True)

        response = self.client_a.post(reverse("dashboard:email_preferences"), {"weekly_digest_enabled": "on"})

        self.assertEqual(response.status_code, 302)
        pref_a.refresh_from_db()
        pref_b.refresh_from_db()
        self.assertTrue(pref_a.weekly_digest_enabled)
        self.assertTrue(pref_b.weekly_digest_enabled)

    def test_save_job_requires_post(self):
        # Using GET should be blocked, as `@require_POST` is applied
        url = reverse("jobs:save", kwargs={"public_id": self.job.public_id})
        response = self.client_a.get(url)
        self.assertEqual(response.status_code, 405) # Method Not Allowed

    def test_unsave_job_requires_post(self):
        url = reverse("jobs:unsave", kwargs={"public_id": self.job.public_id})
        response = self.client_a.get(url)
        self.assertEqual(response.status_code, 405)

    def test_dangerous_get_requests_do_not_mutate(self):
        delete_url = reverse("dashboard:cv")
        create_match_url = reverse("matching:create", kwargs={"public_id": self.job.public_id})
        quick_match_url = reverse("matching:quick_match", kwargs={"public_id": self.job.public_id})
        delete_account_url = reverse("dashboard:delete_account")

        response = self.client_a.get(delete_url, {"delete_cv_id": str(self.cv_a.public_id)})
        self.assertEqual(response.status_code, 200)
        self.cv_a.refresh_from_db()
        self.assertTrue(self.cv_a.is_active)

        before_matches = MatchResult.objects.filter(user=self.user_a).count()
        response = self.client_a.get(create_match_url)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(MatchResult.objects.filter(user=self.user_a).count(), before_matches)

        response = self.client_anon.get(quick_match_url)
        self.assertEqual(response.status_code, 405)

        response = self.client_a.get(delete_account_url)
        self.assertEqual(response.status_code, 200)
        self.user_a.refresh_from_db()
        self.assertTrue(self.user_a.is_active)

    def test_normal_user_blocked_from_admin(self):
        response = self.client_a.get("/admin/")
        self.assertEqual(response.status_code, 302) # Redirects to login

    def test_cv_file_url_raises_value_error(self):
        with self.assertRaises(ValueError):
            _ = self.cv_b.file.url

    def test_cv_pages_do_not_expose_file_urls_or_raw_text(self):
        for url in [reverse("dashboard:cv"), reverse("dashboard:profile")]:
            with self.subTest(url=url):
                response = self.client_a.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "SECRET_RAW_CV_TEXT_A")
                self.assertNotContains(response, "/private_media/")

    def test_soft_deleted_cv_excluded_from_default_manager(self):
        self.cv_a.soft_delete()

        self.assertFalse(CVUpload.objects.filter(public_id=self.cv_a.public_id).exists())
        self.assertTrue(CVUpload.all_objects.filter(public_id=self.cv_a.public_id).exists())

    def test_public_routes_use_uuid(self):
        # We verify that integer routes 404 by testing a common public route
        response = self.client_anon.get("/jobs/1/")
        self.assertEqual(response.status_code, 404)

        response = self.client_a.get("/dashboard/matches/1/")
        self.assertEqual(response.status_code, 404)

        response = self.client_a.get("/dashboard/cv/status/1/")
        self.assertEqual(response.status_code, 404)

    def test_no_external_clients_called_from_views_or_templates(self):
        paths = [settings.BASE_DIR / "templates"]
        paths.extend((settings.BASE_DIR / "apps").glob("*/views.py"))

        forbidden = [
            "FranceTravailClient",
            "OpenRouterClient",
            "run_llm",
            "france_travail",
        ]
        for path in paths:
            files = path.rglob("*") if path.is_dir() else [path]
            for file_path in files:
                if not Path(file_path).is_file():
                    continue
                content = Path(file_path).read_text(encoding="utf-8")
                for symbol in forbidden:
                    with self.subTest(file=str(file_path), symbol=symbol):
                        self.assertNotIn(symbol, content)
