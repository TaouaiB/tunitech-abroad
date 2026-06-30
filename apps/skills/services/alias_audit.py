from django.db.models import Count
from django.utils import timezone

from apps.skills.models import Skill, SkillAlias, UnmatchedSkillCandidate


class SkillAliasAuditService:
    REQUIRED_ALIAS_MAPPINGS = (
        (".NET", ".NET"),
        (".NET Core", ".NET"),
        ("dotnet", ".NET"),
        ("ASP.NET Core", "ASP.NET Core"),
        ("EF Core", "Entity Framework Core"),
        ("C#", "C#"),
        ("C sharp", "C#"),
        ("csharp", "C#"),
        ("Node.js", "Node.js"),
        ("node js", "Node.js"),
        ("ReactJS", "React"),
        ("Postgres", "PostgreSQL"),
        ("postgresql", "PostgreSQL"),
        ("JS", "JavaScript"),
        ("TS", "TypeScript"),
        ("C++", "C++"),
        ("CI/CD", "CI/CD"),
        ("Docker Compose", "Docker Compose"),
        ("GitHub Actions", "GitHub Actions"),
    )

    @classmethod
    def audit(cls) -> dict:
        duplicate_aliases = list(
            SkillAlias.objects.values("normalized_alias")
            .annotate(count=Count("id"), skill_count=Count("skill_id", distinct=True))
            .filter(count__gt=1)
            .order_by("normalized_alias")
        )
        ambiguous_aliases = [
            item for item in duplicate_aliases if item["skill_count"] > 1
        ]

        inactive_aliases = [
            {
                "alias": alias.alias,
                "normalized_alias": alias.normalized_alias,
                "skill": alias.skill.canonical_name,
                "skill_id": alias.skill_id,
            }
            for alias in SkillAlias.objects.filter(skill__is_active=False)
            .select_related("skill")
            .order_by("normalized_alias")[:100]
        ]

        top_unmatched = [
            {
                "raw_skill_text": candidate.raw_skill_text,
                "normalized_text": candidate.normalized_text,
                "source_type": candidate.source_type,
                "occurrence_count": candidate.occurrence_count,
                "status": candidate.status,
            }
            for candidate in UnmatchedSkillCandidate.objects.filter(status="pending")
            .order_by("-occurrence_count", "normalized_text")[:50]
        ]

        skills_with_no_aliases = [
            {
                "skill_id": skill.id,
                "canonical_name": skill.canonical_name,
                "category": skill.category,
            }
            for skill in Skill.objects.filter(is_active=True)
            .annotate(alias_count=Count("aliases"))
            .filter(alias_count=0)
            .order_by("canonical_name")[:100]
        ]

        punctuation_sensitive_terms = [
            ".NET",
            ".NET Core",
            "ASP.NET Core",
            "C#",
            "C++",
            "Node.js",
            "CI/CD",
        ]
        punctuation_sensitive = []
        for term in punctuation_sensitive_terms:
            normalized = cls._normalizer(term)
            alias = SkillAlias.objects.filter(normalized_alias=normalized).select_related("skill").first()
            punctuation_sensitive.append(
                {
                    "term": term,
                    "normalized_alias": normalized,
                    "mapped_skill": alias.skill.canonical_name if alias else None,
                    "present": alias is not None,
                }
            )

        required_alias_failures = cls._required_alias_mapping_failures()

        errors = []
        if duplicate_aliases:
            errors.append("duplicate_normalized_aliases")
        if ambiguous_aliases:
            errors.append("ambiguous_aliases")
        if inactive_aliases:
            errors.append("aliases_pointing_to_inactive_skills")
        if required_alias_failures:
            errors.append("required_alias_mapping_failed")

        warnings = []
        if top_unmatched:
            warnings.append("pending_unmatched_skill_candidates")
        if skills_with_no_aliases:
            warnings.append("active_skills_without_aliases")
        missing_punctuation = [
            item["term"] for item in punctuation_sensitive if not item["present"]
        ]
        if missing_punctuation:
            warnings.append("missing_punctuation_sensitive_aliases")

        return {
            "ok": not errors,
            "service": "skill_alias_audit",
            "generated_at": timezone.now().isoformat(),
            "scope": {"max_items_per_bucket": 100, "top_unmatched_limit": 50},
            "counts": {
                "duplicate_normalized_aliases": len(duplicate_aliases),
                "ambiguous_aliases": len(ambiguous_aliases),
                "aliases_pointing_to_inactive_skills": len(inactive_aliases),
                "required_alias_mapping_failures": len(required_alias_failures),
                "pending_unmatched_candidates": UnmatchedSkillCandidate.objects.filter(status="pending").count(),
                "reported_unmatched_candidates": len(top_unmatched),
                "active_skills_without_aliases": len(skills_with_no_aliases),
            },
            "statuses": {
                "duplicate_normalized_aliases": duplicate_aliases,
                "ambiguous_aliases": ambiguous_aliases,
                "aliases_pointing_to_inactive_skills": inactive_aliases,
                "punctuation_sensitive_aliases": punctuation_sensitive,
                "required_alias_mapping_failures": required_alias_failures,
            },
            "reasons": {"required_alias_mapping_failed": required_alias_failures},
            "top_items": top_unmatched,
            "warnings": warnings,
            "errors": errors,
            "recommended_actions": cls._recommended_actions(
                errors=errors,
                warnings=warnings,
                missing_punctuation=missing_punctuation,
            ),
            "artifacts": {},
        }

    @staticmethod
    def _normalizer(text: str) -> str:
        from apps.skills.services.normalizer import normalize_skill_text

        return normalize_skill_text(text)

    @classmethod
    def _required_alias_mapping_failures(cls) -> list[dict]:
        normalized_aliases = [
            cls._normalizer(raw_alias)
            for raw_alias, _expected_canonical in cls.REQUIRED_ALIAS_MAPPINGS
        ]
        aliases = SkillAlias.objects.filter(
            normalized_alias__in=normalized_aliases,
            skill__is_active=True,
        ).select_related("skill")
        alias_by_normalized = {alias.normalized_alias: alias for alias in aliases}

        failures = []
        for raw_alias, expected_canonical in cls.REQUIRED_ALIAS_MAPPINGS:
            normalized_alias = cls._normalizer(raw_alias)
            alias = alias_by_normalized.get(normalized_alias)
            actual_canonical = alias.skill.canonical_name if alias else None
            if actual_canonical != expected_canonical:
                failures.append(
                    {
                        "raw_alias": raw_alias,
                        "normalized_alias": normalized_alias,
                        "expected_canonical": expected_canonical,
                        "actual_canonical": actual_canonical,
                    }
                )
        return failures

    @staticmethod
    def _recommended_actions(
        *,
        errors: list[str],
        warnings: list[str],
        missing_punctuation: list[str],
    ) -> list[str]:
        actions = []
        if "duplicate_normalized_aliases" in errors:
            actions.append("Resolve duplicate normalized aliases before relying on exports.")
        if "ambiguous_aliases" in errors:
            actions.append("Ensure each normalized alias maps to exactly one canonical skill.")
        if "aliases_pointing_to_inactive_skills" in errors:
            actions.append("Move aliases away from inactive skills or reactivate the intended canonical skill.")
        if "required_alias_mapping_failed" in errors:
            actions.append("Run seed_skills and repair any required Phase 16D aliases still mapped incorrectly.")
        if missing_punctuation:
            actions.append("Seed missing punctuation-sensitive aliases: " + ", ".join(missing_punctuation))
        if "pending_unmatched_skill_candidates" in warnings:
            actions.append("Review high-frequency pending unmatched skill candidates in admin.")
        if "active_skills_without_aliases" in warnings:
            actions.append("Add at least the canonical-name alias for active skills without aliases.")
        return actions
