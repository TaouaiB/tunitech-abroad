from collections import defaultdict

from django.db import transaction
from apps.profiles.models import ProfileSkill
from apps.skills.models import SkillAlias, UnmatchedSkillCandidate
from apps.skills.services.normalizer import candidate_normalized_skill_texts

class ProfileSkillBackfillService:
    SOURCE_TYPE_MAP = {
        "cv_upload": "cv",
        "cv": "cv",
        "cv_parse": "cv",
        "cv_parser": "cv",
        "quick_match": "quick_match",
        "job": "job",
        "ingestion": "job",
        "job_ingestion": "job",
        "manual": "manual",
        "profile": "manual",
    }

    @classmethod
    def backfill_profile_skills(cls) -> dict:
        qs = ProfileSkill.objects.filter(skill__isnull=True)
        total = qs.count()
        mapped = 0
        unmatched = 0
        unmatched_by_source: dict[tuple[str, str], dict] = defaultdict(
            lambda: {"count": 0, "raw_skill_text": "", "source_object_id": None}
        )

        for ps in qs.iterator(chunk_size=1000):
            lookup_candidates = candidate_normalized_skill_texts(ps.normalized_name or ps.raw_name)
            if not lookup_candidates:
                continue

            alias = SkillAlias.objects.filter(
                normalized_alias__in=lookup_candidates,
                skill__is_active=True,
            ).select_related("skill").first()
            if alias:
                ps.skill = alias.skill
                ps.save(update_fields=['skill'])
                mapped += 1
            else:
                source_type = cls._source_type_for_profile_skill(ps.source)
                key = (lookup_candidates[0], source_type)
                unmatched_by_source[key]["count"] += 1
                unmatched_by_source[key]["raw_skill_text"] = ps.raw_name[:255]
                unmatched_by_source[key]["source_object_id"] = ps.id
                unmatched += 1

        with transaction.atomic():
            for (normalized_text, source_type), data in unmatched_by_source.items():
                candidate, created = UnmatchedSkillCandidate.objects.get_or_create(
                    normalized_text=normalized_text,
                    source_type=source_type,
                    defaults={
                        'raw_skill_text': data["raw_skill_text"],
                        'source_model': 'ProfileSkill',
                        'source_object_id': data["source_object_id"],
                        'occurrence_count': data["count"],
                        'status': 'pending',
                    }
                )
                if not created and candidate.occurrence_count < data["count"]:
                    candidate.occurrence_count = data["count"]
                    candidate.save(update_fields=["occurrence_count", "updated_at"])

        return {
            "total_processed": total,
            "mapped_to_canonical": mapped,
            "unmatched_candidates": unmatched,
        }

    @classmethod
    def _source_type_for_profile_skill(cls, source: str | None) -> str:
        normalized_source = (source or "").strip().lower()
        source_type = cls.SOURCE_TYPE_MAP.get(normalized_source, "unknown")
        valid_sources = {choice[0] for choice in UnmatchedSkillCandidate.SOURCE_CHOICES}
        return source_type if source_type in valid_sources else "unknown"
