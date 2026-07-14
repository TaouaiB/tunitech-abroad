from collections import defaultdict
from dataclasses import dataclass, field

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.matching.services.match_result import MatchResultService
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.profiles.services.materialization import ProfileSkillMaterializationService
from apps.recommendations.services.recommendation import RecommendationService
from apps.recommendations.services.staleness import RecommendationStalenessService
from apps.skills.models import SkillAlias
from apps.skills.services.ambiguity import is_allowed_skill_match, is_metadata_noise
from apps.skills.services.ignored import IgnoredSkillService
from apps.skills.services.normalizer import candidate_normalized_skill_texts, normalize_skill_text

User = get_user_model()


@dataclass
class RepairRowPlan:
    profile_skill_id: int
    raw_name: str
    normalized_name: str
    classification: str
    skill_id: int | None = None
    skill_name: str | None = None
    candidate_skill_names: list[str] = field(default_factory=list)


@dataclass
class RepairUserReport:
    user_id: int
    rows_scanned: int = 0
    rows_already_linked: int = 0
    rows_linked: int = 0
    rows_ambiguous: int = 0
    rows_unmatched: int = 0
    rows_ignored: int = 0
    rows_invalid: int = 0
    rows_conflicting: int = 0
    refreshed: bool = False
    recommendations_created: int = 0
    recommendations_updated: int = 0
    matches_recomputed: int = 0
    changed: bool = False
    row_plans: list[RepairRowPlan] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "rows_scanned": self.rows_scanned,
            "rows_already_linked": self.rows_already_linked,
            "rows_linked": self.rows_linked,
            "rows_ambiguous": self.rows_ambiguous,
            "rows_unmatched": self.rows_unmatched,
            "rows_ignored": self.rows_ignored,
            "rows_invalid": self.rows_invalid,
            "rows_conflicting": self.rows_conflicting,
            "refreshed": self.refreshed,
            "recommendations_created": self.recommendations_created,
            "recommendations_updated": self.recommendations_updated,
            "matches_recomputed": self.matches_recomputed,
            "changed": self.changed,
            "errors": self.errors,
            "row_plans": [
                {
                    "profile_skill_id": plan.profile_skill_id,
                    "raw_name": plan.raw_name,
                    "normalized_name": plan.normalized_name,
                    "classification": plan.classification,
                    "skill_id": plan.skill_id,
                    "skill_name": plan.skill_name,
                    "candidate_skill_names": plan.candidate_skill_names,
                }
                for plan in self.row_plans
            ],
        }


@dataclass
class RepairReport:
    users_scanned: int = 0
    users_changed: int = 0
    rows_scanned: int = 0
    rows_linked: int = 0
    rows_already_linked: int = 0
    rows_ambiguous: int = 0
    rows_unmatched: int = 0
    rows_ignored_or_invalid: int = 0
    conflicts: int = 0
    users_refreshed: int = 0
    recommendations_created: int = 0
    recommendations_updated: int = 0
    matches_recomputed: int = 0
    errors: int = 0
    user_reports: list[RepairUserReport] = field(default_factory=list)

    def to_dict(self):
        return {
            "users_scanned": self.users_scanned,
            "users_changed": self.users_changed,
            "rows_scanned": self.rows_scanned,
            "rows_linked": self.rows_linked,
            "rows_already_linked": self.rows_already_linked,
            "rows_ambiguous": self.rows_ambiguous,
            "rows_unmatched": self.rows_unmatched,
            "rows_ignored_or_invalid": self.rows_ignored_or_invalid,
            "conflicts": self.conflicts,
            "users_refreshed": self.users_refreshed,
            "recommendations_created": self.recommendations_created,
            "recommendations_updated": self.recommendations_updated,
            "matches_recomputed": self.matches_recomputed,
            "errors": self.errors,
            "user_reports": [ur.to_dict() for ur in self.user_reports],
        }


class ProfileSkillBackfillService:
    """
    Safe planner/executor for repairing null-linked ProfileSkill rows.

    - Dry-run by default; ``apply=True`` is required for writes.
    - One atomic transaction per user.
    - Deterministic matches link the null row to the resolved canonical skill.
    - Ambiguous and unmatched rows are preserved.
    - Non-null links are never overwritten.
    - Per-user errors are caught and reported; other users continue.
    """

    @classmethod
    def repair(
        cls,
        user=None,
        apply: bool = False,
        refresh_results: bool = False,
    ) -> RepairReport:
        report = RepairReport()
        users = cls._users(user)

        for user_obj in users.order_by("pk").iterator(chunk_size=100):
            user_report = RepairUserReport(user_id=user_obj.pk)
            try:
                with transaction.atomic():
                    user_report = cls._repair_user(
                        user_obj,
                        apply=apply,
                        refresh_results=refresh_results,
                    )
            except Exception as exc:
                user_report.errors.append(str(exc))
                report.errors += 1

            report.user_reports.append(user_report)
            report.users_scanned += 1
            report.rows_scanned += user_report.rows_scanned
            report.rows_linked += user_report.rows_linked
            report.rows_already_linked += user_report.rows_already_linked
            report.rows_ambiguous += user_report.rows_ambiguous
            report.rows_unmatched += user_report.rows_unmatched
            report.rows_ignored_or_invalid += user_report.rows_ignored + user_report.rows_invalid
            report.conflicts += user_report.rows_conflicting
            report.recommendations_created += user_report.recommendations_created
            report.recommendations_updated += user_report.recommendations_updated
            report.matches_recomputed += user_report.matches_recomputed
            if user_report.changed:
                report.users_changed += 1
            if user_report.refreshed:
                report.users_refreshed += 1

        return report

    @classmethod
    def backfill_profile_skills(cls, apply: bool = False, refresh_results: bool = False) -> dict:
        """
        Compatibility wrapper that no longer accepts writes.

        ``apply=True`` is refused; use :meth:`repair` or the
        ``repair_profile_skill_links`` management command for deterministic
        profile-skill repair. Dry-runs remain available.
        """
        if apply:
            raise RuntimeError(
                "backfill_profile_skills no longer accepts apply=True. "
                "Use repair_profile_skill_links or ProfileSkillBackfillService.repair()."
            )
        report = cls.repair(apply=False, refresh_results=refresh_results)
        return report.to_dict()

    @classmethod
    def _users(cls, user):
        if user is not None:
            return User.objects.filter(pk=user.pk)
        return User.objects.filter(candidate_profile__isnull=False).distinct()

    @classmethod
    def _repair_user(cls, user_obj, *, apply: bool, refresh_results: bool) -> RepairUserReport:
        profile = getattr(user_obj, "candidate_profile", None)
        report = RepairUserReport(user_id=user_obj.pk)
        if profile is None:
            return report

        # Lock base ProfileSkill rows first; no nullable outer joins.
        locked_rows = list(
            ProfileSkill.objects.select_for_update()
            .filter(profile=profile)
            .order_by("pk")
        )

        report.rows_scanned = len(locked_rows)
        report.rows_already_linked = sum(1 for row in locked_rows if row.skill_id is not None)

        for row in locked_rows:
            if row.skill_id is not None:
                continue

            plan = cls._plan_row(row)
            report.row_plans.append(plan)

            if plan.classification == "deterministic":
                if apply:
                    skill = cls._get_skill(plan.skill_id)
                    if skill is None:
                        raise RuntimeError(
                            f"ProfileSkill {row.pk}: resolved skill {plan.skill_id} disappeared"
                        )

                    result = ProfileSkillMaterializationService.materialize(
                        profile=profile,
                        skill=skill,
                        source=row.source or "cv_upload",
                        confidence=row.confidence or 80,
                        is_confirmed=row.is_confirmed,
                        raw_name=row.raw_name or skill.canonical_name,
                        existing_profile_skill=row,
                    )

                    if result.conflict:
                        report.rows_conflicting += 1
                    elif result.changed:
                        report.rows_linked += 1
                        report.changed = True
            elif plan.classification == "ambiguous":
                report.rows_ambiguous += 1
            elif plan.classification == "unmatched":
                report.rows_unmatched += 1
            elif plan.classification == "ignored":
                report.rows_ignored += 1
            elif plan.classification == "invalid":
                report.rows_invalid += 1

        if apply and report.changed and refresh_results:
            cls._refresh_results(user_obj, profile, report)

        return report

    @classmethod
    def _plan_row(cls, row: ProfileSkill) -> RepairRowPlan:
        raw = (row.raw_name or "").strip()
        normalized = (row.normalized_name or "").strip()
        lookup_text = normalized or raw

        if not lookup_text or is_metadata_noise(lookup_text):
            return RepairRowPlan(
                profile_skill_id=row.pk,
                raw_name=raw,
                normalized_name=normalized,
                classification="invalid",
            )

        if IgnoredSkillService.is_ignored(normalize_skill_text(lookup_text)):
            return RepairRowPlan(
                profile_skill_id=row.pk,
                raw_name=raw,
                normalized_name=normalized,
                classification="ignored",
            )

        candidates = candidate_normalized_skill_texts(lookup_text)
        if not candidates:
            return RepairRowPlan(
                profile_skill_id=row.pk,
                raw_name=raw,
                normalized_name=normalized,
                classification="invalid",
            )

        aliases = list(
            SkillAlias.objects.filter(
                normalized_alias__in=candidates,
                skill__is_active=True,
            ).select_related("skill")
        )

        matches_by_skill: dict[int, list[SkillAlias]] = defaultdict(list)
        for alias in aliases:
            if is_allowed_skill_match(
                raw_text=raw,
                canonical_name=alias.skill.canonical_name,
                alias=alias.normalized_alias,
            ):
                matches_by_skill[alias.skill_id].append(alias)

        if not matches_by_skill:
            return RepairRowPlan(
                profile_skill_id=row.pk,
                raw_name=raw,
                normalized_name=normalized,
                classification="unmatched",
            )

        if len(matches_by_skill) > 1:
            candidate_names = sorted(
                {alias.skill.canonical_name for alias_list in matches_by_skill.values() for alias in alias_list}
            )
            return RepairRowPlan(
                profile_skill_id=row.pk,
                raw_name=raw,
                normalized_name=normalized,
                classification="ambiguous",
                candidate_skill_names=candidate_names,
            )

        skill_id = next(iter(matches_by_skill.keys()))
        skill_name = matches_by_skill[skill_id][0].skill.canonical_name
        return RepairRowPlan(
            profile_skill_id=row.pk,
            raw_name=raw,
            normalized_name=normalized,
            classification="deterministic",
            skill_id=skill_id,
            skill_name=skill_name,
        )

    @classmethod
    def _get_skill(cls, skill_id: int):
        from apps.skills.models import Skill

        try:
            return Skill.objects.get(pk=skill_id)
        except Skill.DoesNotExist:
            return None

    @classmethod
    def _refresh_results(cls, user_obj, profile, report: RepairUserReport) -> None:
        RecommendationStalenessService.mark_user_recommendations_stale(
            user_obj, reason="profile_skill_repair"
        )
        rec_result = RecommendationService.refresh_for_user(user_obj, "profile_skill_repair")
        report.recommendations_created = rec_result.recommendations_created
        report.recommendations_updated = rec_result.recommendations_updated
        report.matches_recomputed = MatchResultService.recompute_current_matches_for_user(
            user_obj
        )
        report.refreshed = True
