import uuid
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.http import Http404

from apps.jobs.models import (
    ExperienceLevel,
    JobSource,
    JobStatus,
    JobType,
    NormalizedJob,
    RawJobRecord,
    RemoteType,
    SourceType,
)
from apps.jobs.services.query import JobQueryService
from apps.jobs.services.revalidation import JobRevalidationService
from apps.jobs.services.search import JobSearchService


class JobSearchServiceTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="France Travail", slug="france_travail", source_type=SourceType.API)
        self.inactive_source = JobSource.objects.create(name="Disabled", slug="disabled", source_type=SourceType.FIXTURE, is_active=False)
        
        raw1 = RawJobRecord.objects.create(
            source=self.source, source_job_id="1", raw_payload_json={}, payload_hash="1",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.job1 = NormalizedJob.objects.create(
            source=self.source, raw_record=raw1, source_job_id="1", title="Python Developer",
            company_name="Tech Corp", location="Paris", city="Paris",
            contract_type="CDI",
            remote_type=RemoteType.REMOTE, job_type=JobType.FULL_TIME_JOB, experience_level=ExperienceLevel.MID_LEVEL,
            description="We need Python devs.", status=JobStatus.ACTIVE,
            required_skills_json=["Python", "Django"], optional_skills_json=["Docker"],
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        
        raw2 = RawJobRecord.objects.create(
            source=self.source, source_job_id="2", raw_payload_json={}, payload_hash="2",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.job2 = NormalizedJob.objects.create(
            source=self.source, raw_record=raw2, source_job_id="2", title="Frontend Engineer",
            company_name="Web Studio", location="Lyon", city="Lyon",
            contract_type="STAGE",
            remote_type=RemoteType.ON_SITE, job_type=JobType.INTERNSHIP, experience_level=ExperienceLevel.INTERNSHIP,
            description="Looking for React devs.", status=JobStatus.ACTIVE,
            required_skills_json=["JavaScript", "React"],
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )

        raw3 = RawJobRecord.objects.create(
            source=self.source, source_job_id="3", raw_payload_json={}, payload_hash="3",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.inactive_job = NormalizedJob.objects.create(
            source=self.source, raw_record=raw3, source_job_id="3", title="Old Job",
            status=JobStatus.EXPIRED,
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        raw4 = RawJobRecord.objects.create(
            source=self.source, source_job_id="4", raw_payload_json={}, payload_hash="4",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.expired_active_job = NormalizedJob.objects.create(
            source=self.source, raw_record=raw4, source_job_id="4", title="Expired Active Job",
            status=JobStatus.ACTIVE, expires_at=timezone.now() - timezone.timedelta(days=1),
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        raw5 = RawJobRecord.objects.create(
            source=self.inactive_source, source_job_id="5", raw_payload_json={}, payload_hash="5",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.disabled_source_job = NormalizedJob.objects.create(
            source=self.inactive_source, raw_record=raw5, source_job_id="5", title="Disabled Source Job",
            status=JobStatus.ACTIVE,
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )

    def test_search_returns_only_active_jobs(self):
        result = JobSearchService.search({})
        self.assertEqual(result.total_count, 2)
        job_ids = [j.id for j in result.page_obj]
        self.assertIn(self.job1.id, job_ids)
        self.assertIn(self.job2.id, job_ids)
        self.assertNotIn(self.inactive_job.id, job_ids)
        self.assertNotIn(self.expired_active_job.id, job_ids)
        self.assertNotIn(self.disabled_source_job.id, job_ids)

    def test_search_query_uses_postgres_full_text(self):
        from django.contrib.postgres.search import SearchVector
        NormalizedJob.objects.filter(id=self.job1.id).update(search_vector=SearchVector("title", "description"))
        result = JobSearchService.search({"q": "Python"})
        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.page_obj[0].id, self.job1.id)

    def test_search_filter_location(self):
        result = JobSearchService.search({"location": "Paris"})
        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.page_obj[0].id, self.job1.id)

    def test_search_filter_contract_job_and_experience(self):
        result = JobSearchService.search({
            "contract_type": "STAGE",
            "job_type": "internship",
            "experience_level": "internship",
        })
        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.page_obj[0].id, self.job2.id)

    def test_search_filter_remote_type(self):
        result = JobSearchService.search({"remote_type": "remote"})
        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.page_obj[0].id, self.job1.id)

    def test_search_filter_skill(self):
        result = JobSearchService.search({"skill": "Docker"})
        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.page_obj[0].id, self.job1.id)

    def test_search_pagination(self):
        result = JobSearchService.search({"page_size": 1})
        self.assertEqual(result.total_count, 2)
        self.assertEqual(len(result.page_obj), 1)
        self.assertTrue(result.paginator.num_pages > 1)

    def test_invalid_page_input_is_safe(self):
        result = JobSearchService.search({"page": "not-a-page", "page_size": "not-a-size"})
        self.assertEqual(result.page_obj.number, 1)
        self.assertEqual(result.paginator.per_page, 20)

    def test_unknown_sort_falls_back_safely(self):
        result = JobSearchService.search({"sort": "invalid_sort"})
        self.assertEqual(result.sort, "newest")
        self.assertEqual(result.total_count, 2)

    def test_search_does_not_call_france_travail_client(self):
        with patch("apps.jobs.services.france_travail.client.FranceTravailClient.search_offers") as search_offers:
            JobSearchService.search({"q": "Python"})
        search_offers.assert_not_called()


class JobQueryServiceTests(TestCase):
    def setUp(self):
        self.source = JobSource.objects.create(name="FT", slug="ft", source_type=SourceType.API)
        raw = RawJobRecord.objects.create(
            source=self.source, source_job_id="1", raw_payload_json={}, payload_hash="1",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.job = NormalizedJob.objects.create(
            source=self.source, raw_record=raw, source_job_id="1", title="Job",
            status=JobStatus.ACTIVE,
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        raw2 = RawJobRecord.objects.create(
            source=self.source, source_job_id="2", raw_payload_json={}, payload_hash="2",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.inactive_job = NormalizedJob.objects.create(
            source=self.source, raw_record=raw2, source_job_id="2", title="Old",
            status=JobStatus.REMOVED,
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        raw3 = RawJobRecord.objects.create(
            source=self.source, source_job_id="3", raw_payload_json={}, payload_hash="3",
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.expired_active_job = NormalizedJob.objects.create(
            source=self.source, raw_record=raw3, source_job_id="3", title="Expired Active",
            status=JobStatus.ACTIVE, expires_at=timezone.now() - timezone.timedelta(days=1),
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )

    def test_get_public_job_success(self):
        job = JobQueryService.get_public_job(self.job.public_id)
        self.assertEqual(job.id, self.job.id)

    def test_get_public_job_404_on_inactive(self):
        with self.assertRaises(Http404):
            JobQueryService.get_public_job(self.inactive_job.public_id)

    def test_get_public_job_404_on_expired_active_job(self):
        with self.assertRaises(Http404):
            JobQueryService.get_public_job(self.expired_active_job.public_id)

    def test_get_public_job_404_on_invalid_uuid(self):
        with self.assertRaises(Http404):
            JobQueryService.get_public_job("not-a-uuid")

    def test_get_public_job_404_on_unknown_uuid(self):
        with self.assertRaises(Http404):
            JobQueryService.get_public_job(uuid.uuid4())

    def test_detail_lookup_does_not_call_france_travail_client(self):
        with patch("apps.jobs.services.france_travail.client.FranceTravailClient.get_offer_detail") as get_offer_detail:
            JobQueryService.get_public_job(self.job.public_id)
        get_offer_detail.assert_not_called()


class JobRevalidationServiceTests(TestCase):
    def test_revalidate_if_needed(self):
        job = NormalizedJob()
        # Ensure it safely returns the job without errors
        result = JobRevalidationService.revalidate_if_needed(job)
        self.assertEqual(result, job)
