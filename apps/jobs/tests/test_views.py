from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import uuid
from unittest.mock import patch

from apps.jobs.models import JobSource, RawJobRecord, NormalizedJob, JobStatus, SourceType


class JobViewTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="FT", slug="ft", source_type=SourceType.API)
        raw = RawJobRecord.objects.create(
            source=self.source, source_job_id="1", raw_payload_json={}, payload_hash="1",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.job = NormalizedJob.objects.create(
            source=self.source, raw_record=raw, source_job_id="1", title="Test View Job",
            company_name="Test Company",
            status=JobStatus.ACTIVE,
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )

    def test_job_list_view_anonymous(self):
        response = self.client.get(reverse("jobs:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test View Job")
        self.assertNotContains(response, "recherche depuis la base locale")
        self.assertContains(response, "Offres IT françaises actualisées")

    def test_job_list_view_filters(self):
        response = self.client.get(reverse("jobs:list"), {"q": "Test", "location": "Paris"})
        self.assertEqual(response.status_code, 200)

    def test_job_list_view_shows_relevance_sort_when_query_requests_it(self):
        response = self.client.get(reverse("jobs:list"), {"q": "django", "sort": "relevance"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort"], "relevance")
        self.assertEqual(response.context["filters"]["sort"], "relevance")
        self.assertContains(response, '<option value="relevance" selected>', html=False)
        self.assertContains(response, '>Plus pertinentes</option>', html=False)

    def test_job_list_view_falls_back_to_newest_sort_without_query(self):
        response = self.client.get(reverse("jobs:list"), {"sort": "relevance"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort"], "newest")
        self.assertEqual(response.context["filters"]["sort"], "newest")
        self.assertContains(response, '<option value="newest" selected>', html=False)
        self.assertContains(response, '>Plus récentes</option>', html=False)

    def test_job_list_view_preserves_filter_params_in_pagination(self):
        for index in range(2, 23):
            raw = RawJobRecord.objects.create(
                source=self.source, source_job_id=str(index), raw_payload_json={}, payload_hash=str(index),
                first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
            )
            NormalizedJob.objects.create(
                source=self.source, raw_record=raw, source_job_id=str(index), title=f"Python Job {index}",
                status=JobStatus.ACTIVE,
                first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
            )

        from django.contrib.postgres.search import SearchVector
        NormalizedJob.objects.all().update(search_vector=SearchVector("title", "description"))

        response = self.client.get(reverse("jobs:list"), {"q": "Python", "page_size": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "q=Python")
        self.assertContains(response, "page=2")
        
    def test_job_detail_view_success(self):
        response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test View Job")
        self.assertContains(response, "Test Company")

    def test_job_detail_view_404(self):
        invalid_uuid = uuid.uuid4()
        response = self.client.get(reverse("jobs:detail", args=[invalid_uuid]))
        self.assertEqual(response.status_code, 404)

    def test_internal_integer_detail_route_does_not_exist(self):
        response = self.client.get(f"/jobs/{self.job.id}/")
        self.assertEqual(response.status_code, 404)

    def test_job_links_use_public_id_not_internal_id(self):
        response = self.client.get(reverse("jobs:list"))
        self.assertContains(response, reverse("jobs:detail", args=[self.job.public_id]))
        self.assertNotContains(response, f'href="/jobs/{self.job.id}/"')

    def test_public_job_card_matches_prototype_structure_and_order(self):
        self.job.contract_type = "CDI"
        self.job.location = "Paris"
        self.job.description = "Build Django services for a France-first job intelligence product."
        self.job.required_skills_json = ["Django", "REST API"]
        self.job.published_at = timezone.now()
        self.job.save(
            update_fields=[
                "contract_type",
                "location",
                "description",
                "required_skills_json",
                "published_at",
            ]
        )

        response = self.client.get(reverse("jobs:list"))
        html = response.content.decode()
        detail_url = reverse("jobs:detail", args=[self.job.public_id])

        self.assertContains(response, "tta-job-main")
        self.assertContains(response, "tta-job-side")
        self.assertContains(response, "tta-job-freshness")
        self.assertContains(response, "tta-job-actions")
        self.assertContains(response, "tta-card-date")
        self.assertContains(response, f'href="{detail_url}"')
        self.assertNotContains(response, f'href="/jobs/{self.job.id}/"')

        self.assertLess(html.index("tta-chip-row"), html.index("tta-job-title"))
        self.assertLess(html.index("tta-job-title"), html.index("tta-card-meta"))
        self.assertLess(html.index("tta-card-meta"), html.index("tta-job-desc"))
        self.assertLess(html.index("tta-job-desc"), html.index("tta-job-skill-row"))
        self.assertLess(html.index("</a>"), html.index("tta-job-actions"))

    def test_job_card_hides_placeholder_badges_and_shows_date(self):
        self.job.contract_type = "Unknown"
        self.job.remote_type = "unknown"
        self.job.job_type = "t"
        self.job.experience_level = "unknown"
        self.job.company_name = "t"
        self.job.location = "Unknown"
        self.job.city = "t"
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
                "published_at",
            ]
        )

        response = self.client.get(reverse("jobs:list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Unknown")
        self.assertNotContains(response, "unknown")
        self.assertNotContains(response, ">t<", html=False)
        self.assertContains(response, "Vu le")
        self.assertContains(response, "tta-card-date")
        self.assertContains(response, reverse("jobs:detail", args=[self.job.public_id]))
        self.assertContains(response, "Compétences en cours d'analyse")

    def test_job_card_prefers_published_date(self):
        published_at = timezone.datetime(2026, 1, 15, 9, 0, tzinfo=timezone.get_current_timezone())
        self.job.published_at = published_at
        self.job.save(update_fields=["published_at"])

        response = self.client.get(reverse("jobs:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Publié le")
        self.assertContains(response, "15")
        self.assertNotContains(response, "Vu le")

    def test_job_card_falls_back_to_first_seen_date(self):
        self.job.published_at = None
        self.job.save(update_fields=["published_at"])

        response = self.client.get(reverse("jobs:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vu le")
        self.assertContains(response, "tta-card-date")

    def test_job_card_falls_back_to_last_seen_date(self):
        self.job.published_at = None
        self.job.first_seen_at = None

        html = render_to_string("jobs/partials/job_card.html", {"job": self.job})

        self.assertIn("Vu le", html)
        self.assertIn("tta-card-date", html)

    def test_public_pages_survive_analytics_failure(self):
        with patch("apps.jobs.views.UserEventService.record_event", side_effect=Exception("analytics down")):
            list_response = self.client.get(reverse("jobs:list"))
            detail_response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)

    def test_detail_survives_revalidation_failure(self):
        with patch("apps.jobs.views.JobRevalidationService.revalidate_if_needed", side_effect=Exception("revalidation down")):
            response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))

        self.assertEqual(response.status_code, 200)

    def test_job_detail_hides_unknown_languages(self):
        self.job.language_requirements_json = {
            "anglais": "unknown",
            "français": "inconnu",
            "allemand": "",
            "espagnol": None,
        }
        self.job.save()
        response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Langues exigées")
        self.assertNotContains(response, "unknown")
        self.assertNotContains(response, "inconnu")

    def test_job_detail_shows_valid_languages(self):
        self.job.language_requirements_json = {"anglais": "B2", "français": "unknown"}
        self.job.save()
        response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Langues exigées")
        self.assertContains(response, "anglais")
        self.assertContains(response, "B2")
        self.assertNotContains(response, "français")
