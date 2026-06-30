from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from apps.recommendations.models import JobRecommendation, RecommendationQualityFeedback, RecommendationQualityIssue
from apps.recommendations.services.feedback import RecommendationFeedbackService
from django.contrib.auth import get_user_model
from apps.profiles.models import CandidateProfile
from apps.jobs.models import JobSource, RawJobRecord, NormalizedJob

UserModel = get_user_model()

class Phase16FRecommendationFeedbackTests(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create_user(username="rec_reviewer", email="rec_reviewer@example.com", password="password")
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            years_experience=3.0,
            current_level="mid",
            french_level="c1",
            profile_completion_score=100
        )
        now = timezone.now()
        source = JobSource.objects.create(name="test", slug="test", source_type="fixture")
        raw = RawJobRecord.objects.create(source=source, source_job_id="test3", payload_hash="test3", first_seen_at=now, last_seen_at=now, last_fetched_at=now, raw_payload_json={})
        self.job = NormalizedJob.objects.create(
            source=source,
            raw_record=raw,
            source_job_id="test3",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            public_id="22222222-2222-2222-2222-222222222222",
            title="Dev Rec",
            status="active",
        )
        self.rec = JobRecommendation.objects.create(
            user=self.user,
            profile=self.profile,
            job=self.job,
            fit_score=85,
            ranking_score=85.0,
            rank=1,
            computed_at=now,
            status="active"
        )

    def test_recommendation_quality_feedback_creation(self):
        feedback = RecommendationQualityFeedback.objects.create(
            recommendation=self.rec,
            reason=RecommendationQualityIssue.GOOD_RECOMMENDATION,
            notes="Spot on!",
            reviewed_by=self.user
        )
        self.assertEqual(feedback.reason, RecommendationQualityIssue.GOOD_RECOMMENDATION)
        self.assertEqual(self.rec.quality_feedback.count(), 1)

    def test_recommendation_feedback_service_rejects_invalid_reason(self):
        with self.assertRaises(ValidationError):
            RecommendationFeedbackService.record_feedback(
                self.user,
                self.job.public_id,
                "not_a_valid_reason",
                "bad value",
            )

        self.assertEqual(self.rec.quality_feedback.count(), 0)

    def test_recommendation_feedback_url_uses_job_public_id_not_integer_pk(self):
        with self.assertRaises(NoReverseMatch):
            reverse("recommendations:feedback", kwargs={"public_id": self.rec.pk})

        url = reverse("recommendations:feedback", kwargs={"public_id": self.job.public_id})
        self.assertIn(str(self.job.public_id), url)
        self.assertNotIn(f"/{self.rec.pk}/", url)

    def test_recommendation_feedback_view_is_owner_filtered(self):
        other_user = UserModel.objects.create_user(
            username="other_rec_reviewer",
            email="other_rec_reviewer@example.com",
            password="password",
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("recommendations:feedback", kwargs={"public_id": self.job.public_id}),
            {"reason": RecommendationQualityIssue.GOOD_RECOMMENDATION, "notes": "useful"},
        )

        self.assertRedirects(response, reverse("dashboard:recommendations"))
        self.assertTrue(
            RecommendationQualityFeedback.objects.filter(
                recommendation=self.rec,
                reason=RecommendationQualityIssue.GOOD_RECOMMENDATION,
                reviewed_by=self.user,
            ).exists()
        )

        self.client.force_login(other_user)
        response = self.client.post(
            reverse("recommendations:feedback", kwargs={"public_id": self.job.public_id}),
            {"reason": RecommendationQualityIssue.GOOD_RECOMMENDATION},
        )
        self.assertEqual(response.status_code, 404)
