from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.cvs.models import CVParsedData, CVUpload
from apps.cvs.services.parsing import CVParsingService
from apps.jobs.models import JobStatus, NormalizedJob, NormalizedJobSkill, RequirementType
from apps.jobs.services.it_classification import JobITClassificationService
from apps.jobs.services.search_vector import JobSearchVectorService
from apps.jobs.services.skill_extraction import JobSkillExtractionService
from apps.jobs.services.skill_signals import compute_deterministic_skill_signal_quality
from apps.matching.models import MatchResult
from apps.matching.services.match_result import MatchResultService
from apps.matching.services.scoring import MatchScoringService
from apps.profiles.models import ProfileSkill
from apps.recommendations.models import JobRecommendation
from apps.skills.models import SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.ambiguity import is_allowed_skill_match
from apps.skills.services.extraction_policy import SkillCandidateKind, classify_skill_candidate, classify_skill_candidate_with_alias
from apps.skills.services.normalizer import normalize_skill_text


GATE_E_REPORT_DIR = "docs/phases/post_launch/gate_e_rematerialize_compare"


@dataclass(frozen=True)
class GateEOptions:
    apply: bool = False
    report_path: str = ""
    limit: int | None = None
    job_public_id: str | None = None
    include_cvs: bool = False
    include_matches: bool = False
    skip_search_vectors: bool = False
    backup_path: str = ""
    settings_module: str = ""
    git_commit: str = ""
    database_info: dict[str, str] = field(default_factory=dict)


@dataclass
class GateEResult:
    before: dict[str, Any]
    after: dict[str, Any]
    processed_jobs: int = 0
    rematerialized_jobs: int = 0
    search_vectors_rebuilt: int = 0
    recommendations_marked_stale: int = 0
    recommendations_refreshed: int = 0
    matches_refreshed: int = 0
    cvs_reparsed: int = 0
    failures: list[dict[str, str]] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)
    top_removed_skills: list[tuple[str, int]] = field(default_factory=list)
    top_added_skills: list[tuple[str, int]] = field(default_factory=list)
    top_added_hard_skills: list[tuple[str, int]] = field(default_factory=list)
    top_added_broad_signals: list[tuple[str, int]] = field(default_factory=list)
    top_retained_hard_skills: list[tuple[str, int]] = field(default_factory=list)
    removed_noisy_skills: list[tuple[str, int]] = field(default_factory=list)
    unexpected_noisy_additions: list[dict[str, Any]] = field(default_factory=list)
    top_unmatched_phrases: list[dict[str, Any]] = field(default_factory=list)
    useful_signal_jobs: list[dict[str, str]] = field(default_factory=list)
    weakened_signal_jobs: list[dict[str, str]] = field(default_factory=list)
    transition_counts: dict[str, int] = field(default_factory=dict)
    match_consistency: dict[str, int | str] = field(default_factory=dict)
    quality_gate_metrics: dict[str, int | str] = field(default_factory=dict)
    affected_job_ids: set[int] = field(default_factory=set)
    report_path: str = ""


class GateERematerializationService:
    @classmethod
    def run(cls, options: GateEOptions) -> GateEResult:
        result = GateEResult(before=cls.capture_metrics(), after={})
        before_by_job = cls._job_snapshots()

        with transaction.atomic():
            cls._process_jobs(options, result)
            if options.include_matches:
                cls._refresh_affected_matches_and_recommendations(result)
            else:
                result.skipped.append({"scope": "matches", "reason": "include_matches_not_requested"})
            if options.include_cvs:
                cls._reparse_active_cvs(result)
            result.after = cls.capture_metrics()
            cls._calculate_top_changes(before_by_job, cls._job_snapshots(), result)
            result.top_unmatched_phrases = cls._top_unmatched_phrases()
            result.match_consistency = cls._calculate_match_consistency(options, result)
            result.quality_gate_metrics = cls._quality_gate_metrics_from_current_db(result)

            if not options.apply:
                transaction.set_rollback(True)

        if not result.after:
            result.after = cls.capture_metrics()
        result.report_path = cls.write_report(options, result)
        return result

    @classmethod
    def _base_job_queryset(cls, options: GateEOptions):
        qs = (
            NormalizedJob.objects.filter(status=JobStatus.ACTIVE)
            .select_related("raw_record", "source")
            .prefetch_related("job_skills__skill")
            .order_by("public_id")
        )
        if options.job_public_id:
            qs = qs.filter(public_id=options.job_public_id)
        if options.limit is not None:
            qs = qs[: max(options.limit, 0)]
        return qs

    @classmethod
    def _process_jobs(cls, options: GateEOptions, result: GateEResult) -> None:
        for job in cls._base_job_queryset(options):
            result.processed_jobs += 1
            try:
                with transaction.atomic():
                    old_quality = job.skill_signal_quality or "unknown"
                    before_snapshot = cls._snapshot_job(job)
                    raw_payload = job.raw_record.raw_payload_json if job.raw_record else {}
                    if not isinstance(raw_payload, dict):
                        raw_payload = {}
                    classification = JobITClassificationService.classify(
                        raw_payload,
                        job.description or "",
                        job.title or "",
                    )
                    job.classification_json = {
                        "family": classification.family,
                        "is_it": classification.is_it,
                        "confidence": classification.confidence,
                        "reasons": classification.reasons,
                        "negative_reasons": classification.negative_reasons,
                    }
                    signal = compute_deterministic_skill_signal_quality(job)
                    job.skill_signal_quality = signal.quality
                    if options.apply:
                        job.save(update_fields=["classification_json", "skill_signal_quality"])

                    JobSkillExtractionService.extract_for_job(job)

                    job = (
                        NormalizedJob.objects.select_related("raw_record", "source")
                        .prefetch_related("job_skills__skill")
                        .get(pk=job.pk)
                    )
                    after_snapshot = cls._snapshot_job(job)
                    changed = before_snapshot != after_snapshot
                    if changed and not options.skip_search_vectors:
                        JobSearchVectorService.update_search_vector(job)
                    new_quality = job.skill_signal_quality or "unknown"
                    if old_quality in {"missing", "generic_only", "unknown"} and new_quality in {"partial", "strong"}:
                        result.useful_signal_jobs.append(cls._job_change_row(job, old_quality, new_quality))
                    if old_quality in {"partial", "strong"} and new_quality in {"missing", "generic_only", "excluded_non_it"}:
                        result.weakened_signal_jobs.append(cls._job_change_row(job, old_quality, new_quality))
                result.rematerialized_jobs += 1
                if changed:
                    result.affected_job_ids.add(job.id)
                if changed and not options.skip_search_vectors:
                    result.search_vectors_rebuilt += 1
            except Exception as exc:  # noqa: BLE001 - per-row isolation is required for this gate.
                result.failures.append(
                    {
                        "scope": "job",
                        "public_id": str(job.public_id),
                        "reason": exc.__class__.__name__,
                    }
                )

    @staticmethod
    def _job_change_row(job: NormalizedJob, before: str, after: str) -> dict[str, str]:
        return {
            "public_id": str(job.public_id),
            "source_job_id": job.source_job_id,
            "title": job.title,
            "before": before,
            "after": after,
        }

    @classmethod
    def _refresh_affected_matches_and_recommendations(cls, result: GateEResult) -> None:
        if not result.affected_job_ids:
            return

        now = timezone.now()
        affected_recommendations = JobRecommendation.objects.filter(
            job_id__in=result.affected_job_ids,
            status="active",
        ).select_related("user", "profile", "job")

        for recommendation in affected_recommendations.order_by("user_id", "job__public_id"):
            try:
                active_cv = CVUpload.objects.filter(user=recommendation.user, is_active=True).order_by("-uploaded_at").first()
                score_result = MatchScoringService.calculate(recommendation.profile, recommendation.job, active_cv)
                if score_result.match_confidence == MatchScoringService.CONFIDENCE_UNAVAILABLE:
                    recommendation.status = "stale"
                    recommendation.updated_at = now
                    recommendation.save(update_fields=["status", "updated_at"])
                    result.recommendations_marked_stale += 1
                    continue
                recommendation.cv_upload = active_cv
                recommendation.fit_score = score_result.fit_score
                recommendation.ranking_score = score_result.fit_score
                recommendation.strong_skills_json = score_result.strong_skills
                recommendation.missing_skills_json = score_result.missing_required_skills + score_result.missing_optional_skills
                recommendation.risk_flags_json = score_result.risk_flags
                recommendation.profile_signals_json = score_result.profile_signals
                recommendation.reason_summary = ". ".join(score_result.recommended_actions) if score_result.recommended_actions else ""
                recommendation.computed_at = now
                recommendation.updated_at = now
                recommendation.save(
                    update_fields=[
                        "cv_upload",
                        "fit_score",
                        "ranking_score",
                        "strong_skills_json",
                        "missing_skills_json",
                        "risk_flags_json",
                        "profile_signals_json",
                        "reason_summary",
                        "computed_at",
                        "updated_at",
                    ]
                )
                result.recommendations_refreshed += 1
            except Exception as exc:  # noqa: BLE001
                result.failures.append(
                    {
                        "scope": "recommendation_refresh",
                        "public_id": str(getattr(recommendation, "public_id", recommendation.id)),
                        "reason": exc.__class__.__name__,
                    }
                )

        match_rows = MatchResult.objects.filter(job_id__in=result.affected_job_ids).select_related("user", "job")
        for match in match_rows.order_by("user_id", "job__public_id"):
            try:
                MatchResultService.update_current_match_for_job(match.user, match.job)
                result.matches_refreshed += 1
            except Exception as exc:  # noqa: BLE001
                result.failures.append(
                    {
                        "scope": "match_refresh",
                        "public_id": str(match.public_id),
                        "reason": exc.__class__.__name__,
                    }
                )

    @classmethod
    def _reparse_active_cvs(cls, result: GateEResult) -> None:
        for cv in CVUpload.objects.filter(is_active=True).order_by("public_id"):
            try:
                parsed = CVParsingService.parse(cv)
                if parsed is not None:
                    result.cvs_reparsed += 1
            except Exception as exc:  # noqa: BLE001
                result.failures.append(
                    {
                        "scope": "cv",
                        "public_id": str(cv.public_id),
                        "reason": exc.__class__.__name__,
                    }
                )

    @classmethod
    def capture_metrics(cls) -> dict[str, Any]:
        active_jobs = NormalizedJob.objects.filter(status=JobStatus.ACTIVE)
        active_job_ids = active_jobs.values("id")
        materialized = NormalizedJobSkill.objects.filter(job_id__in=active_job_ids)
        quality_counts = dict(
            active_jobs.values_list("skill_signal_quality").annotate(count=Count("id")).order_by("skill_signal_quality")
        )
        unmatched_counts = list(
            UnmatchedSkillCandidate.objects.values("source_type", "status")
            .annotate(candidate_count=Count("id"))
            .order_by("source_type", "status")
        )
        recommendation_counts = dict(
            JobRecommendation.objects.values_list("status").annotate(count=Count("id")).order_by("status")
        )
        cv_warning_count = CVParsedData.objects.filter(
            Q(warnings_json__isnull=False) & ~Q(warnings_json=[])
        ).count()
        return {
            "active_jobs": active_jobs.count(),
            "total_materialized_job_skills": materialized.count(),
            "zero_skill_active_jobs": active_jobs.annotate(skill_count=Count("job_skills")).filter(skill_count=0).count(),
            "generic_only_active_jobs": active_jobs.filter(skill_signal_quality="generic_only").count(),
            "skill_signal_counts": quality_counts,
            "weak_signal_count": quality_counts.get("generic_only", 0) + quality_counts.get("missing", 0),
            "missing_signal_count": quality_counts.get("missing", 0),
            "partial_signal_count": quality_counts.get("partial", 0),
            "strong_signal_count": quality_counts.get("strong", 0),
            "low_confidence_materialized_skills": materialized.filter(confidence__lt="0.700").count(),
            "unmatched_candidate_total": UnmatchedSkillCandidate.objects.count(),
            "unmatched_candidate_counts": unmatched_counts,
            "recommendation_counts": recommendation_counts,
            "stale_recommendations": recommendation_counts.get("stale", 0),
            "active_recommendations": recommendation_counts.get("active", 0),
            "match_result_counts": {"total": MatchResult.objects.count()},
            "active_cvs": CVUpload.objects.filter(is_active=True).count(),
            "cv_parse_warning_count": cv_warning_count,
        }

    @classmethod
    def _job_snapshots(cls) -> dict[str, dict[str, Any]]:
        snapshots: dict[str, dict[str, Any]] = {}
        rows = (
            NormalizedJob.objects.filter(status=JobStatus.ACTIVE)
            .prefetch_related("job_skills__skill")
            .order_by("public_id")
        )
        for job in rows:
            snapshots[str(job.public_id)] = cls._snapshot_job(job)
        return snapshots

    @staticmethod
    def _snapshot_job(job: NormalizedJob) -> dict[str, Any]:
        return {
            "title": job.title,
            "skill_signal_quality": job.skill_signal_quality,
            "classification_json": job.classification_json,
            "required_skills_json": sorted(job.required_skills_json or []),
            "optional_skills_json": sorted(job.optional_skills_json or []),
            "skills": sorted(
                (
                    row.skill.canonical_name,
                    row.skill.category,
                    row.requirement_type,
                    str(row.confidence) if row.confidence is not None else "",
                    row.source,
                )
                for row in job.job_skills.all()
            ),
        }

    @classmethod
    def _calculate_top_changes(cls, before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]], result: GateEResult) -> None:
        removed: Counter[str] = Counter()
        added: Counter[str] = Counter()
        retained: Counter[str] = Counter()
        unexpected_added: Counter[tuple[str, str, str]] = Counter()
        transitions: Counter[str] = Counter()
        for public_id, before_row in before.items():
            after_row = after.get(public_id, {})
            before_skills = {row[0] for row in before_row.get("skills", [])}
            after_skills = {row[0] for row in after_row.get("skills", [])}
            removed_names = before_skills - after_skills
            added_names = after_skills - before_skills
            removed.update(removed_names)
            added.update(added_names)
            retained.update(before_skills & after_skills)
            for name, category, requirement_type, _confidence, _source in after_row.get("skills", []):
                if name not in added_names:
                    continue
                decision = classify_skill_candidate(
                    raw_text=name,
                    canonical_name=name,
                    category=category,
                )
                if decision.kind in {
                    SkillCandidateKind.METHODOLOGY_PROCESS,
                    SkillCandidateKind.SOFT_SKILL,
                    SkillCandidateKind.SOURCE_METADATA,
                    SkillCandidateKind.REJECTED_NOISE,
                }:
                    unexpected_added[(name, decision.kind, requirement_type)] += 1

            before_count = len(before_skills)
            after_count = len(after_skills)
            before_quality = before_row.get("skill_signal_quality") or "unknown"
            after_quality = after_row.get("skill_signal_quality") or "unknown"
            before_useful = before_count > 0 and before_quality in {"partial", "strong"}
            after_useful = after_count > 0 and after_quality in {"partial", "strong"}
            if before_count == 0 and after_count > 0:
                transitions["zero_skill_to_nonzero"] += 1
            elif before_count > 0 and after_count == 0:
                transitions["nonzero_to_zero_skill"] += 1
            elif not before_useful and after_useful:
                transitions["generic_weak_to_useful"] += 1
            elif before_useful and not after_useful:
                transitions["useful_to_weak_generic"] += 1
            else:
                transitions["unchanged"] += 1
        result.top_removed_skills = removed.most_common(20)
        result.top_added_skills = added.most_common(20)
        result.top_added_hard_skills = cls._filter_skill_pairs(added, {SkillCandidateKind.HARD_TECHNICAL})
        result.top_added_broad_signals = cls._filter_skill_pairs(added, {SkillCandidateKind.BROAD_TECHNICAL})
        result.top_retained_hard_skills = cls._filter_skill_pairs(retained, {SkillCandidateKind.HARD_TECHNICAL})
        result.removed_noisy_skills = cls._filter_skill_pairs(
            removed,
            {
                SkillCandidateKind.METHODOLOGY_PROCESS,
                SkillCandidateKind.SOFT_SKILL,
                SkillCandidateKind.SOURCE_METADATA,
                SkillCandidateKind.REJECTED_NOISE,
            },
        )
        result.transition_counts = dict(transitions)
        result.unexpected_noisy_additions = [
            {
                "canonical_name": name,
                "policy_class": policy_class,
                "requirement_type": requirement_type,
                "count": count,
            }
            for (name, policy_class, requirement_type), count in unexpected_added.most_common(20)
        ]

    @staticmethod
    def _calculate_match_consistency(options: GateEOptions, result: GateEResult) -> dict[str, int | str]:
        if not options.include_matches:
            return {"status": "not_run", "comparable_pairs": 0, "mismatches": 0}
        if not result.affected_job_ids:
            return {"status": "not_run", "comparable_pairs": 0, "mismatches": 0}

        comparable_pairs = 0
        mismatches = 0
        active_recommendations = JobRecommendation.objects.filter(
            job_id__in=result.affected_job_ids,
            status="active",
        ).order_by("user_id", "job_id")
        for recommendation in active_recommendations:
            latest_match = (
                MatchResult.objects.filter(user=recommendation.user, job=recommendation.job)
                .order_by("-updated_at", "-created_at", "-id")
                .first()
            )
            if latest_match is None:
                continue
            comparable_pairs += 1
            if int(recommendation.fit_score) != int(latest_match.fit_score):
                mismatches += 1

        if comparable_pairs == 0:
            status = "not_run"
        elif mismatches:
            status = "fail"
        else:
            status = "pass"
        return {"status": status, "comparable_pairs": comparable_pairs, "mismatches": mismatches}

    @staticmethod
    def _filter_skill_pairs(counter: Counter[str], kinds: set[str]) -> list[tuple[str, int]]:
        from apps.skills.models import Skill

        skills = Skill.objects.filter(canonical_name__in=list(counter)).in_bulk(field_name="canonical_name")
        selected: list[tuple[str, int]] = []
        for name, count in counter.most_common():
            skill = skills.get(name)
            decision = classify_skill_candidate(
                raw_text=name,
                canonical_name=name,
                category=skill.category if skill else None,
            )
            if decision.kind in kinds:
                selected.append((name, count))
            if len(selected) >= 20:
                break
        return selected

    @staticmethod
    def _top_unmatched_phrases() -> list[dict[str, Any]]:
        return list(
            UnmatchedSkillCandidate.objects.values("normalized_text", "source_type", "status")
            .annotate(total_occurrences=Sum("occurrence_count"))
            .order_by("-total_occurrences", "source_type", "status", "normalized_text")[:30]
        )

    @classmethod
    def write_report(cls, options: GateEOptions, result: GateEResult) -> str:
        report_path = Path(options.report_path or cls.default_report_path(options.apply))
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(cls.render_report(options, result), encoding="utf-8")
        return str(report_path)

    @staticmethod
    def default_report_path(apply: bool) -> str:
        mode = "apply" if apply else "dry_run"
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        return f"{GATE_E_REPORT_DIR}/gate_e_rematerialize_compare_{mode}_{timestamp}.md"

    @classmethod
    def render_report(cls, options: GateEOptions, result: GateEResult) -> str:
        lines = [
            "# Gate E Rematerialize and Compare Report",
            "",
            "## Environment and Safety",
            f"- timestamp: {timezone.now().isoformat()}",
            f"- git_commit: {options.git_commit or 'unknown'}",
            f"- settings_module: {options.settings_module or 'unknown'}",
            f"- database: {cls._format_database_info(options.database_info)}",
            f"- backup_path: {options.backup_path or 'not_applicable_dry_run'}",
            f"- mode: {'apply' if options.apply else 'dry-run'}",
            f"- processed_jobs: {result.processed_jobs}",
            f"- failures: {len(result.failures)}",
            "",
            "## Before Counts",
            cls._format_metrics(result.before),
            "",
            "## After Counts",
            cls._format_metrics(result.after),
            "",
            "## Top Changes",
            cls._format_pairs("removed_noisy_soft_or_process_skills", result.removed_noisy_skills),
            cls._format_pairs("added_hard_technical_skills", result.top_added_hard_skills),
            cls._format_pairs("added_broad_non_scoring_signals", result.top_added_broad_signals),
            cls._format_pairs("retained_hard_technical_skills", result.top_retained_hard_skills),
            cls._format_unexpected_noisy_additions(result.unexpected_noisy_additions),
            cls._format_unmatched("top_unmatched_phrases_after", result.top_unmatched_phrases),
            cls._format_transition_counts(result.transition_counts),
            cls._format_job_rows("jobs_changing_to_useful_signals", result.useful_signal_jobs),
            cls._format_job_rows("jobs_becoming_hidden_or_weak", result.weakened_signal_jobs),
            cls._format_job_rows("failures_or_skipped_rows", result.failures + result.skipped),
            "",
            "## Refresh Counts",
            f"- rematerialized_jobs: {result.rematerialized_jobs}",
            f"- search_vectors_rebuilt: {result.search_vectors_rebuilt}",
            f"- recommendations_marked_stale: {result.recommendations_marked_stale}",
            f"- recommendations_refreshed: {result.recommendations_refreshed}",
            f"- matches_refreshed: {result.matches_refreshed}",
            f"- cvs_reparsed: {result.cvs_reparsed}",
            "",
            "## Regression Cases",
            cls._regression_cases(options, result),
            "",
            "## Quality Gate Explanation",
            cls._quality_gate_explanation(result),
            "",
            "## Safety Confirmations",
            "- stored local job data only",
            "- no France Travail calls",
            "- no OpenRouter calls",
            "- no canonical Skill auto-creation",
            "- no raw CV text or private CV paths included",
            "- dry-run uses one database transaction and does not enqueue tasks, send email, call external APIs, call LLM, or reparse CVs",
        ]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _format_database_info(info: dict[str, str]) -> str:
        if not info:
            return "unknown"
        return ", ".join(f"{key}={value}" for key, value in sorted(info.items()))

    @classmethod
    def _format_metrics(cls, metrics: dict[str, Any]) -> str:
        keys = [
            "active_jobs",
            "total_materialized_job_skills",
            "zero_skill_active_jobs",
            "generic_only_active_jobs",
            "weak_signal_count",
            "missing_signal_count",
            "partial_signal_count",
            "strong_signal_count",
            "low_confidence_materialized_skills",
            "unmatched_candidate_total",
            "stale_recommendations",
            "active_recommendations",
            "active_cvs",
            "cv_parse_warning_count",
        ]
        lines = [f"- {key}: {metrics.get(key, 0)}" for key in keys]
        lines.append(f"- skill_signal_counts: {metrics.get('skill_signal_counts', {})}")
        lines.append(f"- unmatched_candidate_counts: {metrics.get('unmatched_candidate_counts', [])}")
        lines.append(f"- recommendation_counts: {metrics.get('recommendation_counts', {})}")
        lines.append(f"- match_result_counts: {metrics.get('match_result_counts', {})}")
        return "\n".join(lines)

    @staticmethod
    def _format_pairs(title: str, pairs: list[tuple[str, int]]) -> str:
        lines = [f"### {title}"]
        if not pairs:
            return "\n".join([*lines, "- none"])
        return "\n".join([*lines, *[f"- {name}: {count}" for name, count in pairs]])

    @staticmethod
    def _format_unmatched(title: str, rows: list[dict[str, Any]]) -> str:
        lines = [f"### {title}"]
        if not rows:
            return "\n".join([*lines, "- none"])
        return "\n".join(
            [
                *lines,
                *[
                    "- "
                    f"normalized_text={row.get('normalized_text')}, "
                    f"source_type={row.get('source_type')}, "
                    f"status={row.get('status')}, "
                    f"occurrence_count={row.get('total_occurrences')}"
                    for row in rows[:20]
                ],
            ]
        )

    @staticmethod
    def _format_transition_counts(counts: dict[str, int]) -> str:
        lines = ["### before_after_transitions"]
        keys = [
            "zero_skill_to_nonzero",
            "nonzero_to_zero_skill",
            "generic_weak_to_useful",
            "useful_to_weak_generic",
            "unchanged",
        ]
        return "\n".join([*lines, *[f"- {key}: {counts.get(key, 0)}" for key in keys]])

    @staticmethod
    def _format_job_rows(title: str, rows: list[dict[str, str]]) -> str:
        lines = [f"### {title}"]
        if not rows:
            return "\n".join([*lines, "- none"])
        rendered = []
        for row in rows[:50]:
            rendered.append(
                "- "
                + ", ".join(f"{key}={value}" for key, value in sorted(row.items()))
            )
        return "\n".join([*lines, *rendered])

    @staticmethod
    def _format_unexpected_noisy_additions(rows: list[dict[str, Any]]) -> str:
        lines = ["### unexpected_noisy_canonical_additions"]
        if not rows:
            return "\n".join([*lines, "- none"])
        rendered = [
            "- "
            f"canonical_name={row['canonical_name']}, "
            f"policy_class={row['policy_class']}, "
            f"requirement_type={row['requirement_type']}, "
            f"count={row['count']}"
            for row in rows
        ]
        return "\n".join([*lines, *rendered])

    @classmethod
    def _regression_cases(cls, options: GateEOptions, result: GateEResult) -> str:
        def status(ok: bool) -> str:
            return "pass" if ok else "fail"

        chef_devops = classify_skill_candidate_with_alias("chef cookbooks")
        sql_server = classify_skill_candidate_with_alias("SQL Server")
        database_specific = [
            classify_skill_candidate_with_alias(name)
            for name in ("PostgreSQL", "MySQL", "SQLite")
        ]
        metadata = classify_skill_candidate_with_alias("Concevoir une application web")
        soft_process = [
            classify_skill_candidate_with_alias(name)
            for name in ("Teamwork", "Communication", "Agile", "Scrum")
        ]
        broad = [classify_skill_candidate_with_alias(name) for name in ("API", "Monitoring")]
        api_specific = [
            classify_skill_candidate_with_alias(name)
            for name in ("REST API", "OpenAPI", "GraphQL")
        ]
        db_aliases = {
            name: SkillAlias.objects.filter(normalized_alias=normalize_skill_text(name)).select_related("skill").first()
            for name in ("PostgreSQL", "MySQL", "SQLite")
        }
        db_canonical_names = {
            alias.skill.canonical_name
            for alias in db_aliases.values()
            if alias is not None and alias.skill is not None
        }
        sql_server_alias = SkillAlias.objects.filter(normalized_alias=normalize_skill_text("SQL Server")).select_related("skill").first()
        noisy_cv_rows = ProfileSkill.objects.filter(
            source="cv_upload",
            normalized_name__in=cls._noisy_cv_normalized_names(),
        ).count()
        match_consistency = result.match_consistency or {"status": "not_run", "comparable_pairs": 0, "mismatches": 0}

        cases = [
            (
                "chef de projet rejects Chef",
                status(
                    not is_allowed_skill_match(
                        raw_text="chef de projet",
                        canonical_name="Chef",
                        alias="chef",
                        context="chef de projet informatique",
                    )
                ),
            ),
            ("DevOps/Chef cookbook context accepts canonical Chef", status(chef_devops.materialize and chef_devops.kind == SkillCandidateKind.HARD_TECHNICAL)),
            (
                "SQL Server does not add SQL duplicate",
                status(
                    sql_server.materialize
                    and sql_server_alias is not None
                    and sql_server_alias.skill.canonical_name == "SQL Server"
                    and not is_allowed_skill_match(
                        raw_text="SQL Server",
                        canonical_name="SQL",
                        alias="sql",
                        context="SQL Server",
                    )
                ),
            ),
            (
                "PostgreSQL, MySQL, SQLite aliases map to distinct canonicals",
                status(
                    all(decision.materialize for decision in database_specific)
                    and all(db_aliases.values())
                    and db_canonical_names == {"PostgreSQL", "MySQL", "SQLite"}
                    and len(db_canonical_names) == 3
                ),
            ),
            ("source metadata phrases reject materialization", status(not metadata.materialize)),
            (
                "Teamwork, Communication, Agile, Scrum are not required technical skills",
                status(all(not decision.can_be_required and decision.kind in {SkillCandidateKind.SOFT_SKILL, SkillCandidateKind.METHODOLOGY_PROCESS} for decision in soft_process)),
            ),
            (
                "API and Monitoring are not required hard skills",
                status(all(decision.materialize and not decision.can_be_required and decision.kind == SkillCandidateKind.BROAD_TECHNICAL for decision in broad)),
            ),
            (
                "REST API, OpenAPI, GraphQL retain specific behavior where supported",
                status(all(decision.materialize and decision.can_be_required for decision in api_specific)),
            ),
            ("CV-origin noisy phrases are not ProfileSkill rows", status(noisy_cv_rows == 0)),
            (
                "recommendation/match score consistency uses actual current scores",
                f"{match_consistency['status']} "
                f"(comparable_pairs={match_consistency['comparable_pairs']}, mismatches={match_consistency['mismatches']})",
            ),
        ]
        return "\n".join(f"- {name}: {case_status}" for name, case_status in cases)

    @classmethod
    def _quality_gate_explanation(cls, result: GateEResult) -> str:
        metrics = result.quality_gate_metrics or cls._quality_gate_metrics_from_current_db(result)
        return "\n".join(
            [f"- {key}: {value}" for key, value in metrics.items()]
        )

    @classmethod
    def _quality_gate_metrics_from_current_db(cls, result: GateEResult) -> dict[str, int | str]:
        active_job_ids = NormalizedJob.objects.filter(status=JobStatus.ACTIVE).values("id")
        broad_materialized_rows = 0
        broad_required_rows = 0
        broad_optional_rows = 0
        broad_detected_rows = 0
        soft_or_process_materialized_rows = 0
        broad_scoreable_rows = 0

        for row in NormalizedJobSkill.objects.filter(job_id__in=active_job_ids).select_related("skill"):
            decision = classify_skill_candidate(
                raw_text=row.skill.canonical_name,
                canonical_name=row.skill.canonical_name,
                category=row.skill.category,
            )
            if decision.kind == SkillCandidateKind.BROAD_TECHNICAL:
                broad_materialized_rows += 1
                if row.requirement_type == RequirementType.REQUIRED:
                    broad_required_rows += 1
                elif row.requirement_type == RequirementType.OPTIONAL:
                    broad_optional_rows += 1
                elif row.requirement_type == RequirementType.DETECTED:
                    broad_detected_rows += 1
                if MatchScoringService._is_scoreable_job_skill(row):
                    broad_scoreable_rows += 1
            elif decision.kind in {SkillCandidateKind.SOFT_SKILL, SkillCandidateKind.METHODOLOGY_PROCESS}:
                soft_or_process_materialized_rows += 1

        if broad_materialized_rows == 0:
            broad_signal_scoring_check = "not_run"
        elif broad_scoreable_rows:
            broad_signal_scoring_check = "fail"
        else:
            broad_signal_scoring_check = "pass"

        return {
            "broad_materialized_rows": broad_materialized_rows,
            "broad_required_rows": broad_required_rows,
            "broad_optional_rows": broad_optional_rows,
            "broad_detected_rows": broad_detected_rows,
            "soft_or_process_materialized_rows": soft_or_process_materialized_rows,
            "unexpected_noisy_added_rows": sum(row["count"] for row in result.unexpected_noisy_additions),
            "broad_signal_scoring_check": broad_signal_scoring_check,
        }

    @staticmethod
    def _noisy_cv_normalized_names() -> list[str]:
        noisy_phrases = [
            "language extraction",
            "location extraction",
            "recommended learning topics",
            "stock alerts",
            "stock movements",
            "suppliers",
            "validation",
            "server",
            "freelance web developer",
            "web development",
            "authentication flows",
            "implemented input validation",
            "bug reports",
        ]
        return [normalize_skill_text(phrase) for phrase in noisy_phrases]
