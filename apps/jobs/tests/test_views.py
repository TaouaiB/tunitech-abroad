from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import uuid
from unittest.mock import patch

from apps.cvs.models import CVUpload
from apps.jobs.models import (
    JobSource,
    NormalizedJob,
    NormalizedJobSkill,
    RawJobRecord,
    RequirementType,
    SkillSource,
    JobStatus,
    SourceType,
)
from apps.matching.models import MatchResult
from apps.profiles.models import CandidateProfile
from apps.recommendations.services.saved_jobs import SavedJobService
from apps.skills.models import Skill


User = get_user_model()


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
            skill_signal_quality="strong",
            skill_extraction_status="success",
            classification_json={"is_it": True, "confidence": "high"},
            required_skills_json=["Django"],
            first_seen_at=timezone.now(), last_seen_at=timezone.now(), last_fetched_at=timezone.now()
        )
        self.skill = Skill.objects.create(
            canonical_name="Django",
            slug="django",
            category="backend",
        )
        NormalizedJobSkill.objects.create(
            job=self.job,
            skill=self.skill,
            requirement_type=RequirementType.REQUIRED,
            source=SkillSource.LLM,
        )

    def _create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="pass",
        )

    def test_job_list_view_anonymous(self):
        response = self.client.get(reverse("jobs:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test View Job")
        self.assertNotContains(response, "recherche depuis la base locale")
        self.assertContains(response, "Trouvez plus vite des offres tech en France")
        self.assertContains(response, "Jobs, stages et alternance au même endroit.")
        self.assertContains(response, "Rechercher")
        self.assertContains(response, "Statistiques")
        self.assertContains(response, "Filtres")
        self.assertContains(response, "Rôle, entreprise, compétence")
        self.assertContains(response, "Ville : Paris, Nantes, Lyon")
        self.assertContains(response, "France uniquement")
        self.assertContains(response, "Matching CV prêt")
        self.assertContains(response, "Télétravail + hybride")
        self.assertContains(response, "Dernières opportunités")

    def test_job_list_view_filters(self):
        response = self.client.get(reverse("jobs:list"), {"q": "Test", "location": "Paris"})
        self.assertEqual(response.status_code, 200)

    def test_job_list_view_shows_relevance_sort_when_query_requests_it(self):
        response = self.client.get(reverse("jobs:list"), {"q": "django", "sort": "relevance"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort"], "relevance")
        self.assertEqual(response.context["filters"]["sort"], "relevance")

    def test_job_list_view_falls_back_to_newest_sort_without_query(self):
        response = self.client.get(reverse("jobs:list"), {"sort": "relevance"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort"], "newest")
        self.assertEqual(response.context["filters"]["sort"], "newest")

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

    def test_anonymous_job_cards_do_not_render_save_controls(self):
        response = self.client.get(reverse("jobs:list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("jobs:save", args=[self.job.public_id]))
        self.assertNotContains(response, reverse("jobs:unsave", args=[self.job.public_id]))
        self.assertNotContains(response, 'class="btn save', html=False)
        self.assertNotContains(response, "Sauvegardées")

    def test_logged_in_job_cards_render_save_state_and_htmx_response(self):
        user = self._create_user("saved")
        self.client.force_login(user)

        response = self.client.get(reverse("jobs:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("jobs:save", args=[self.job.public_id]))
        self.assertContains(response, "Sauvegarder")
        self.assertContains(response, 'class="btn save"', html=False)

        SavedJobService.save_job(user, self.job.public_id)
        response = self.client.get(reverse("jobs:list"))
        self.assertContains(response, reverse("jobs:unsave", args=[self.job.public_id]))
        self.assertContains(response, "Sauvegardé")
        self.assertContains(response, 'class="btn save saved"', html=False)

        htmx_response = self.client.post(
            reverse("jobs:unsave", args=[self.job.public_id]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(htmx_response.status_code, 200)
        self.assertContains(htmx_response, f'hx-post="{reverse("jobs:save", args=[self.job.public_id])}"', html=False)
        self.assertContains(htmx_response, f'hx-target="#save-button-{self.job.public_id}"', html=False)
        self.assertContains(htmx_response, 'hx-swap="outerHTML"', html=False)

    def test_anonymous_job_detail_hides_save_and_quick_match_and_shows_sign_in_cta(self):
        response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("jobs:save", args=[self.job.public_id]))
        self.assertNotContains(response, "Sauvegarder")
        self.assertNotContains(response, "Sauvegardé")
        self.assertNotContains(response, "quick-match-container")
        self.assertNotContains(response, "Test rapide")
        self.assertContains(response, "Se connecter pour tester")
        self.assertContains(response, f"?next={reverse('jobs:detail', args=[self.job.public_id])}", html=False)

    def test_logged_in_not_ready_job_detail_shows_profile_cv_cta(self):
        user = self._create_user("not-ready")
        profile, _ = CandidateProfile.objects.get_or_create(user=user)
        profile.profile_completion_score = 10
        profile.save(update_fields=["profile_completion_score"])
        self.client.force_login(user)

        response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compléter profil / CV")
        self.assertContains(response, reverse("dashboard:profile"))
        self.assertNotContains(response, "Calculer la compatibilité")

    def test_logged_in_ready_without_match_shows_calculate_match_cta(self):
        user = self._create_user("ready")
        profile, _ = CandidateProfile.objects.get_or_create(user=user)
        profile.profile_completion_score = 80
        profile.save(update_fields=["profile_completion_score"])
        self.client.force_login(user)

        response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Calculer la compatibilité")
        self.assertContains(response, reverse("matching:create", args=[self.job.public_id]))

    def test_logged_in_existing_match_uses_match_public_id_for_score_link(self):
        user = self._create_user("matched")
        profile, _ = CandidateProfile.objects.get_or_create(user=user)
        profile.profile_completion_score = 80
        profile.save(update_fields=["profile_completion_score"])
        cv = CVUpload.objects.create(
            user=user,
            original_filename="cv.pdf",
            file_hash="hash-match",
            file_size=100,
            is_active=True,
            parse_status="parsed",
        )
        match = MatchResult.objects.create(
            user=user,
            profile=profile,
            cv_upload=cv,
            job=self.job,
            profile_snapshot_json={},
            job_snapshot_json={},
            fit_score=72,
            technical_skills_score=80,
            experience_score=70,
            role_title_score=70,
            language_score=60,
            location_score=80,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Voir le score")
        self.assertContains(response, reverse("matching:detail", args=[match.public_id]))
        self.assertNotContains(response, f"/dashboard/matches/{match.id}/")

    def test_llm_explanation_failure_does_not_hide_existing_match_score(self):
        user = self._create_user("failed-match")
        profile, _ = CandidateProfile.objects.get_or_create(user=user)
        profile.profile_completion_score = 80
        profile.save(update_fields=["profile_completion_score"])
        match = MatchResult.objects.create(
            user=user,
            profile=profile,
            job=self.job,
            profile_snapshot_json={},
            job_snapshot_json={},
            fit_score=72,
            technical_skills_score=80,
            experience_score=70,
            role_title_score=70,
            language_score=60,
            location_score=80,
            llm_explanation_status="failed",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Voir le score")
        self.assertContains(response, reverse("matching:detail", args=[match.public_id]))
        self.assertNotContains(response, "Réessayer")

    def test_job_detail_escapes_external_description_html_and_preserves_line_breaks(self):
        self.job.description = 'Line 1\n<img src=x onerror="alert(1)"><script>alert(2)</script>'
        self.job.save(update_fields=["description"])

        response = self.client.get(reverse("jobs:detail", args=[self.job.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Line 1<br>", html=False)
        self.assertContains(response, "&lt;script&gt;alert(2)&lt;/script&gt;", html=False)
        self.assertNotContains(response, "<script>alert(2)</script>", html=False)
        self.assertNotContains(response, '<img src=x onerror="alert(1)">', html=False)

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

        self.assertContains(response, "job-card")
        self.assertContains(response, "pill-row")
        self.assertContains(response, "job-title")
        self.assertContains(response, "job-meta")
        self.assertContains(response, "job-desc")

    def test_job_card_hides_placeholder_badges_and_shows_date(self):
        published_at = timezone.datetime(2026, 1, 15, 9, 0, tzinfo=timezone.get_current_timezone())
        self.job.company_name = "not specified"
        self.job.location = "Unknown"
        self.job.city = "unknown"
        self.job.contract_type = "Unknown"
        self.job.remote_type = "unknown"
        self.job.experience_level = "unknown"
        self.job.published_at = published_at
        self.job.save(
            update_fields=[
                "company_name",
                "location",
                "city",
                "contract_type",
                "remote_type",
                "experience_level",
                "published_at",
            ]
        )

        response = self.client.get(reverse("jobs:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "15 Jan")
        self.assertNotContains(response, "not specified")
        self.assertNotContains(response, "Unknown")
        self.assertNotContains(response, ">unknown<", html=False)

    def test_job_card_prefers_published_date(self):
        published_at = timezone.datetime(2026, 1, 15, 9, 0, tzinfo=timezone.get_current_timezone())
        self.job.published_at = published_at
        self.job.save(update_fields=["published_at"])

        response = self.client.get(reverse("jobs:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "15 Jan")

    def test_job_card_falls_back_to_first_seen_date(self):
        self.job.published_at = None
        self.job.save(update_fields=["published_at"])

        response = self.client.get(reverse("jobs:list"))

        self.assertEqual(response.status_code, 200)

    def test_job_card_falls_back_to_last_seen_date(self):
        self.job.published_at = None
        self.job.first_seen_at = None

        html = render_to_string("jobs/partials/job_card.html", {"job": self.job})

        self.assertNotIn("Vu le", html)

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
