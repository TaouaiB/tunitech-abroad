from dataclasses import dataclass
from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from apps.profiles.models import CandidateProfile
from apps.cvs.models import CVUpload
from apps.jobs.models import NormalizedJob, JobStatus
from apps.matching.services.scoring import MatchScoringService
from apps.recommendations.models import JobRecommendation, RecommendationRun

RECOMMENDATION_VERSION = "reco_v1"
MAX_RECOMMENDATIONS = 20

@dataclass(frozen=True)
class RecommendationResult:
    run_id: int | None
    recommendations_created: int
    recommendations_updated: int
    recommendations_marked_stale: int
    candidate_jobs_count: int
    scored_jobs_count: int
    stored_recommendations_count: int
    skipped_reason: str | None = None


class RecommendationService:
    @classmethod
    def refresh_for_user(cls, user, trigger_type: str) -> RecommendationResult:
        run = RecommendationRun.objects.create(
            user=user,
            trigger_type=trigger_type,
            status="running",
            started_at=timezone.now(),
        )

        try:
            profile = CandidateProfile.objects.filter(user=user).first()
            if not profile or profile.profile_completion_score < 50:
                run.status = "skipped"
                run.error_message = "profile_incomplete"
                run.finished_at = timezone.now()
                run.save(update_fields=["status", "finished_at", "error_message"])
                return RecommendationResult(
                    run_id=run.id,
                    recommendations_created=0,
                    recommendations_updated=0,
                    recommendations_marked_stale=0,
                    candidate_jobs_count=0,
                    scored_jobs_count=0,
                    stored_recommendations_count=0,
                    skipped_reason="profile_incomplete"
                )

            active_cv = (
                CVUpload.objects.filter(user=user, is_active=True)
                .order_by("-uploaded_at")
                .first()
            )

            # Job prefilter: active, local France-first jobs, not expired
            now = timezone.now()
            candidate_jobs = (
                NormalizedJob.objects.filter(
                    Q(country__iexact="FR") | Q(country__iexact="France"),
                    status=JobStatus.ACTIVE,
                    source__is_active=True,
                )
                .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now))
                .select_related("source")
                .prefetch_related("job_skills__skill")
                .order_by("-published_at", "title", "public_id")
            )
            
            # Dismissed recommendations logic (for future, if implemented)
            dismissed_job_ids = JobRecommendation.objects.filter(
                user=user, status="dismissed"
            ).values_list("job_id", flat=True)
            if dismissed_job_ids:
                candidate_jobs = candidate_jobs.exclude(id__in=dismissed_job_ids)
                
            candidate_jobs_count = candidate_jobs.count()
            
            scored_results = []
            for job in candidate_jobs:
                score_res = MatchScoringService.calculate(profile, job, active_cv)
                if score_res.match_confidence == MatchScoringService.CONFIDENCE_UNAVAILABLE:
                    continue
                
                # Ranking formula is deterministic:
                # fit_score + freshness_boost + target_type_boost
                # + user_preference_boost - stale_job_penalty.
                # fit_score comes from Phase 7 MatchScoringService; Phase 8 only
                # adds bounded, rule-based ranking boosts and tie ordering.
                freshness_boost = 0
                if job.published_at:
                    days_old = (now - job.published_at).days
                    if days_old <= 2:
                        freshness_boost = 10
                    elif days_old <= 7:
                        freshness_boost = 5
                        
                target_type_boost = 0
                if profile.target_roles and job.title:
                    for role in profile.target_roles:
                        if role.lower() in job.title.lower():
                            target_type_boost = 10
                            break

                user_preference_boost = 0
                stale_job_penalty = 0
                
                ranking_score = (
                    score_res.fit_score
                    + freshness_boost
                    + target_type_boost
                    + user_preference_boost
                    - stale_job_penalty
                )
                ranking_score = max(0, min(100, ranking_score))
                
                confidence_rank = 0 if score_res.match_confidence == MatchScoringService.CONFIDENCE_RELIABLE else 1
                scored_results.append((job, score_res, Decimal(str(ranking_score)), confidence_rank))
            
            scored_jobs_count = len(scored_results)
            
            scored_results.sort(
                key=lambda item: (
                    item[3],
                    -item[2],
                    -(item[0].published_at.timestamp() if item[0].published_at else 0),
                    item[0].title.lower(),
                    str(item[0].public_id),
                )
            )
            top_recommendations = scored_results[:MAX_RECOMMENDATIONS]
            
            created_count = 0
            updated_count = 0
            stale_count = 0
            
            with transaction.atomic():
                expired_count = JobRecommendation.objects.filter(
                    Q(job__expires_at__lt=now) | ~Q(job__status=JobStatus.ACTIVE),
                    user=user,
                    status="active",
                ).update(status="expired_job", updated_at=now)

                old_active = JobRecommendation.objects.filter(user=user, status="active")
                stale_count = old_active.update(status="stale", updated_at=now)
                
                # Store top recommendations
                for rank, (job, score_res, ranking_score, _confidence_rank) in enumerate(top_recommendations, start=1):
                    rec, created = JobRecommendation.objects.update_or_create(
                        user=user,
                        job=job,
                        recommendation_version=RECOMMENDATION_VERSION,
                        defaults={
                            "profile": profile,
                            "cv_upload": active_cv,
                            "fit_score": score_res.fit_score,
                            "ranking_score": ranking_score,
                            "rank": rank,
                            "strong_skills_json": score_res.strong_skills,
                            "missing_skills_json": score_res.missing_required_skills + score_res.missing_optional_skills,
                            "risk_flags_json": score_res.risk_flags,
                            "profile_signals_json": score_res.profile_signals,
                            "reason_summary": ". ".join(score_res.recommended_actions) if score_res.recommended_actions else "",
                            "computed_at": now,
                            "status": "active",
                            "updated_at": now,
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                stale_count += expired_count

            run.candidate_jobs_count = candidate_jobs_count
            run.scored_jobs_count = scored_jobs_count
            run.stored_recommendations_count = len(top_recommendations)
            run.status = "success"
            run.finished_at = timezone.now()
            run.save()

            return RecommendationResult(
                run_id=run.id,
                recommendations_created=created_count,
                recommendations_updated=updated_count,
                recommendations_marked_stale=stale_count,
                candidate_jobs_count=candidate_jobs_count,
                scored_jobs_count=scored_jobs_count,
                stored_recommendations_count=len(top_recommendations),
            )
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.finished_at = timezone.now()
            run.save(update_fields=["status", "error_message", "finished_at"])
            raise e
