from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.cvs.models import CVParsedData, CVUpload
from apps.jobs.models import (
    JobQualityIssue,
    JobSource,
    JobStatus,
    NormalizedJob,
    NormalizedJobSkill,
    RawJobRecord,
    RequirementType,
    SkillExtractionStatus,
    SkillSource,
    SourceType,
)
from apps.jobs.services.anomaly_review import JobAnomalyReviewService
from apps.skills.models import Skill, UnmatchedSkillCandidate


User = get_user_model()


class GateDAnomalyReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = JobSource.objects.create(
            name="Gate D",
            slug="gate-d",
            source_type=SourceType.MANUAL,
        )
        cls.skill = Skill.objects.create(canonical_name="Python", slug="python-gate-d")

    def _job(
        self,
        source_job_id,
        *,
        title="Developer",
        status=JobStatus.ACTIVE,
        skill_signal_quality="unknown",
        skill_extraction_status=SkillExtractionStatus.SUCCESS,
        quality_issue="",
    ):
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
            description="Technical role description.",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            status=status,
            skill_signal_quality=skill_signal_quality,
            skill_extraction_status=skill_extraction_status,
            quality_issue=quality_issue,
        )

    def test_anomaly_service_returns_active_zero_skill_jobs(self):
        zero = self._job("zero", title="Zero Skill")
        with_skill = self._job("with-skill", title="With Skill")
        NormalizedJobSkill.objects.create(
            job=with_skill,
            skill=self.skill,
            requirement_type=RequirementType.REQUIRED,
            source=SkillSource.RULE,
            confidence=Decimal("1.000"),
        )

        self.assertEqual(list(JobAnomalyReviewService.active_zero_skill_jobs()), [zero])

    def test_anomaly_service_returns_active_generic_only_jobs(self):
        generic = self._job("generic", skill_signal_quality="generic_only")
        self._job("strong", skill_signal_quality="strong")

        self.assertEqual(list(JobAnomalyReviewService.active_generic_only_jobs()), [generic])

    def test_anomaly_service_returns_low_confidence_job_skill_rows(self):
        job = self._job("low-confidence")
        low = NormalizedJobSkill.objects.create(
            job=job,
            skill=self.skill,
            requirement_type=RequirementType.REQUIRED,
            source=SkillSource.RULE,
            confidence=Decimal("0.500"),
        )
        NormalizedJobSkill.objects.create(
            job=self._job("high-confidence"),
            skill=self.skill,
            requirement_type=RequirementType.REQUIRED,
            source=SkillSource.LLM,
            confidence=Decimal("0.900"),
        )

        self.assertEqual(list(JobAnomalyReviewService.low_confidence_job_skills()), [low])

    def test_unmatched_candidate_service_ordering_and_counts_are_deterministic(self):
        UnmatchedSkillCandidate.objects.create(
            raw_skill_text="Django basics",
            normalized_text="django basics",
            source_type="cv",
            occurrence_count=3,
            status="pending",
        )
        UnmatchedSkillCandidate.objects.create(
            raw_skill_text="Action phrase",
            normalized_text="action phrase",
            source_type="job",
            occurrence_count=10,
            status="ignored",
        )
        UnmatchedSkillCandidate.objects.create(
            raw_skill_text="API design",
            normalized_text="api design",
            source_type="job",
            occurrence_count=3,
            status="pending",
        )

        ordered = list(JobAnomalyReviewService.unmatched_candidates().values_list("normalized_text", flat=True))
        counts = list(JobAnomalyReviewService.unmatched_candidate_counts())

        self.assertEqual(ordered, ["action phrase", "django basics", "api design"])
        self.assertEqual(
            counts,
            [
                {"status": "ignored", "source_type": "job", "candidate_count": 1, "total_occurrences": 10},
                {"status": "pending", "source_type": "cv", "candidate_count": 1, "total_occurrences": 3},
                {"status": "pending", "source_type": "job", "candidate_count": 1, "total_occurrences": 3},
            ],
        )

    def test_hidden_excluded_jobs_and_reasons_are_visible(self):
        hidden = self._job("hidden", status=JobStatus.EXPIRED, quality_issue=JobQualityIssue.EXPIRED)
        excluded = self._job("excluded", skill_signal_quality="excluded_non_it")
        self._job("active")

        result = list(JobAnomalyReviewService.hidden_or_excluded_jobs())

        self.assertEqual({job.id for job in result}, {hidden.id, excluded.id})
        self.assertEqual(hidden.quality_issue, JobQualityIssue.EXPIRED)

    def test_recent_cv_parses_with_warnings_does_not_expose_private_file_url(self):
        user = User.objects.create_user(username="cv-user", email="cv-user@example.test", password="pass")
        cv = CVUpload.objects.create(
            user=user,
            file=SimpleUploadedFile("cv.pdf", b"%PDF-test"),
            original_filename="cv.pdf",
            file_hash="hash-cv",
            file_size=9,
            parse_status="parsed_with_warnings",
        )
        parsed = CVParsedData.objects.create(cv_upload=cv, warnings_json=["low_text"])

        self.assertEqual(list(JobAnomalyReviewService.recent_cv_parses_with_warnings()), [parsed])
        with self.assertRaises(ValueError):
            cv.file.url

    def test_report_command_uses_public_ids_and_no_internal_job_links(self):
        job = self._job("report-zero", title="Report Zero")
        out = StringIO()

        call_command("report_admin_anomalies", limit=1, stdout=out)
        output = out.getvalue()

        self.assertIn(str(job.public_id), output)
        self.assertIn("source_job_id=report-zero", output)
        self.assertNotIn(f"/jobs/{job.id}/", output)


class GateDAdminPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.test",
            password="pass",
        )
        cls.normal_user = User.objects.create_user(
            username="normal",
            email="normal@example.test",
            password="pass",
        )
        cls.source = JobSource.objects.create(name="Gate D Admin", slug="gate-d-admin", source_type=SourceType.MANUAL)
        now = timezone.now()
        cls.raw = RawJobRecord.objects.create(
            source=cls.source,
            source_job_id="admin-job",
            raw_payload_json={},
            payload_hash="hash-admin-job",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
        )
        cls.job = NormalizedJob.objects.create(
            source=cls.source,
            raw_record=cls.raw,
            source_job_id="admin-job",
            title="Admin Job",
            description="Admin review job.",
            first_seen_at=now,
            last_seen_at=now,
            last_fetched_at=now,
            status=JobStatus.ACTIVE,
            skill_signal_quality="generic_only",
        )
        cls.skill = Skill.objects.create(canonical_name="Django", slug="django-gate-d-admin")
        NormalizedJobSkill.objects.create(
            job=cls.job,
            skill=cls.skill,
            requirement_type=RequirementType.REQUIRED,
            source=SkillSource.RULE,
            confidence=Decimal("0.500"),
        )
        UnmatchedSkillCandidate.objects.create(
            raw_skill_text="Raw Candidate",
            normalized_text="raw candidate",
            source_type="job",
            occurrence_count=5,
            status="pending",
        )
        cls.cv = CVUpload.objects.create(
            user=cls.normal_user,
            file=SimpleUploadedFile("private.pdf", b"%PDF-private"),
            original_filename="private.pdf",
            file_hash="hash-private",
            file_size=12,
            parse_status="parsed_with_warnings",
        )
        CVParsedData.objects.create(cv_upload=cls.cv, warnings_json=["low_text"], raw_text="private cv text")

    def test_admin_list_pages_load_for_superuser(self):
        self.client.force_login(self.admin_user)

        urls = [
            reverse("admin:jobs_normalizedjob_changelist"),
            reverse("admin:jobs_normalizedjobskill_changelist"),
            reverse("admin:skills_unmatchedskillcandidate_changelist"),
            reverse("admin:cvs_cvparseddata_changelist"),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_non_superuser_cannot_access_cv_parse_anomaly_admin_page(self):
        self.client.force_login(self.normal_user)

        response = self.client.get(reverse("admin:cvs_cvparseddata_changelist"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_cv_parse_admin_page_hides_private_file_and_raw_text(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:cvs_cvparseddata_changelist"))

        self.assertContains(response, str(self.cv.public_id))
        self.assertNotContains(response, self.cv.file.name)
        self.assertNotContains(response, "private cv text")
        self.assertNotContains(response, "Delete selected cv parsed datas")
        self.assertNotContains(response, "/admin/cvs/cvparseddata/add/")
