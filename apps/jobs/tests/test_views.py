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
        
    def test_job_list_view_filters(self):
        response = self.client.get(reverse("jobs:list"), {"q": "Test", "location": "Paris"})
        self.assertEqual(response.status_code, 200)

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
