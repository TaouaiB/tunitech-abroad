from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.jobs.models import JobSource, JobStatus, NormalizedJob, RawJobRecord, SourceType


class HomeCTATests(TestCase):
    def _job(self, title, status=JobStatus.ACTIVE, published_at=None):
        source, _ = JobSource.objects.get_or_create(name="FT", slug="home-ft", source_type=SourceType.API)
        raw = RawJobRecord.objects.create(
            source=source,
            source_job_id=title,
            raw_payload_json={},
            payload_hash=title,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
        )
        return NormalizedJob.objects.create(
            source=source,
            raw_record=raw,
            source_job_id=title,
            title=title,
            status=status,
            published_at=published_at,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
            last_fetched_at=timezone.now(),
        )

    def test_anonymous_homepage_shows_signup_cta(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Find Your Ideal Tech Role in France")
        self.assertContains(response, "Keyword, title, or company")
        self.assertNotContains(response, "Aller au tableau de bord")
        self.assertNotContains(response, "Voir mes recommandations")
        self.assertNotContains(response, "Gérer mon CV")

    def test_authenticated_homepage_shows_candidate_ctas(self):
        user = get_user_model().objects.create_user(
            username="candidate",
            email="candidate@example.test",
            password="pass",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Find Your Ideal Tech Role in France")
        self.assertNotContains(response, "Créer un compte")
        self.assertNotContains(response, "créez un compte")
        self.assertContains(response, "Remote, Paris, Lyon")

    def test_homepage_shows_real_latest_jobs_not_static_coming_soon(self):
        self._job("Old Active Job", published_at=timezone.now() - timezone.timedelta(days=2))
        self._job("Latest Active Job", published_at=timezone.now())
        self._job("Expired Job", status=JobStatus.EXPIRED, published_at=timezone.now() + timezone.timedelta(days=1))

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Latest Active Job")
        self.assertContains(response, "Old Active Job")
        self.assertNotContains(response, "Expired Job")
        self.assertNotContains(response, "Les offres seront bientôt disponibles.")

    def test_homepage_shows_honest_empty_state_without_jobs(self):
        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "No jobs found right now")


class PublicSEORouteTests(TestCase):
    def test_robots_txt_returns_200_with_canonical_sitemap(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "Sitemap: https://tuniatlas.com/sitemap.xml")

    def test_sitemap_xml_returns_200_without_private_urls(self):
        response = self.client.get("/sitemap.xml")
        body = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn("https://tuniatlas.com/", body)
        for private_path in ["/dashboard", "/admin", "/accounts", "/cv"]:
            self.assertNotIn(private_path, body)
