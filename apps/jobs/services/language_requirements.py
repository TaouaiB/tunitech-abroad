from dataclasses import dataclass
from enum import StrEnum
import re
import unicodedata


class LanguageRequirementKind(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    UNSPECIFIED = "unspecified"


@dataclass(frozen=True)
class LanguageRequirement:
    kind: LanguageRequirementKind
    minimum_level: str = ""


class LanguageRequirementClassifier:
    """Interpret every language-requirement representation used by ingestion."""

    LANGUAGE_ALIASES = {
        "french": {"fr", "fra", "francais", "french"},
        "english": {"en", "eng", "anglais", "english"},
    }
    # Negative requirement phrases: must never be classified as REQUIRED.
    NEGATIVE_MARKERS = (
        "not required",
        "no requirement",
        "not mandatory",
        "non requis",
        "pas requis",
        "non obligatoire",
        "pas obligatoire",
    )
    OPTIONAL_MARKERS = {
        "optional",
        "preferred",
        "preference",
        "nice to have",
        "nice-to-have",
        "bonus",
        "a plus",
        "un plus",
        "serait un plus",
        "apprecie",
        "souhaite",
        "facultatif",
    }
    REQUIRED_MARKERS = {
        "required",
        "mandatory",
        "requirement",
        "requis",
        "exige",
        "indispensable",
        "obligatoire",
    }
    UNKNOWN_MARKERS = {
        "",
        "unknown",
        "unspecified",
        "not specified",
        "none",
        "null",
        "inconnu",
        "non precise",
    }
    LEVEL_PATTERN = re.compile(r"\b([abc][12])\b", re.IGNORECASE)
    LEVEL_RANK = {"a1": 1, "a2": 2, "b1": 3, "b2": 4, "c1": 5, "c2": 6}
    # Candidate-level rank must be consistent with the actual Profile and
    # Quick Match UI choices:
    #   * Profile LANGUAGE_LEVEL_CHOICES: "", "basic", "intermediate", "fluent", "native"
    #   * Quick Match FRENCH_CHOICES/ENGLISH_CHOICES: "", "none", "basic",
    #     "intermediate", "advanced", "fluent"
    # "fluent" is labelled "Fluent / Native (C2)" in Quick Match and
    # "Professional / fluent" in Profile, so it must satisfy a required C2.
    #   * advanced satisfies C1 but NOT C2
    #   * intermediate satisfies B2 but NOT C1
    #   * basic satisfies A2 but NOT B1
    # Unknown/unrecognized candidate values are not present in this map and
    # therefore default to rank 0 (insufficient for a required language).
    CANDIDATE_LEVEL_RANK = {
        "": 0,
        "none": 0,
        "no": 0,
        "a0": 0,
        "basic": 2,
        "a1": 1,
        "a2": 2,
        "intermediate": 4,
        "b1": 3,
        "b2": 4,
        "advanced": 5,
        "c1": 5,
        "fluent": 6,
        "c2": 6,
        "native": 6,
    }
    # "no <language> required" / "no <language> mandatory" style negations
    # (e.g. "no English required", "no French required"). These are negated
    # phrases that contain a bare "required" word; checked before the bare
    # REQUIRED_MARKERS substring scan so they are not reversed.
    NEGATIVE_REQUIRED_PATTERN = re.compile(r"\bno\s+\w+(?:\s+\w+)*\s+required\b")
    NEGATIVE_MANDATORY_PATTERN = re.compile(r"\bno\s+\w+(?:\s+\w+)*\s+mandatory\b")
    # "not optional" / "not facultatif" must classify as REQUIRED, not optional.
    NOT_OPTIONAL_PATTERN = re.compile(r"\bnot\s+optional\b")
    NOT_FACULTATIF_PATTERN = re.compile(r"\bnon\s+facultatif\b|\bpas\s+facultatif\b")

    @staticmethod
    def normalize(value) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        return "".join(char for char in text if not unicodedata.combining(char)).strip().casefold()

    @classmethod
    def get_requirement(cls, requirements, language: str) -> LanguageRequirement:
        canonical_language = cls._canonical_language(language)
        if canonical_language is None:
            return LanguageRequirement(LanguageRequirementKind.UNSPECIFIED)

        classified = [
            cls._classify_value(value)
            for value in cls._values_for_language(requirements, canonical_language)
        ]
        return cls._merge(classified)

    @classmethod
    def classify(cls, requirements, language: str) -> LanguageRequirementKind:
        return cls.get_requirement(requirements, language).kind

    @classmethod
    def candidate_meets(cls, requirement: LanguageRequirement, candidate_level: str | None) -> bool:
        if requirement.kind != LanguageRequirementKind.REQUIRED:
            return True
        candidate_rank = cls.CANDIDATE_LEVEL_RANK.get(cls.normalize(candidate_level), 0)
        if candidate_rank == 0:
            return False
        if not requirement.minimum_level:
            return True
        return candidate_rank >= cls.LEVEL_RANK.get(requirement.minimum_level, 0)

    @classmethod
    def _merge(cls, classified) -> LanguageRequirement:
        if not classified:
            return LanguageRequirement(LanguageRequirementKind.UNSPECIFIED)
        # Deterministic precedence across multiple representations:
        #   explicit REQUIRED > explicit OPTIONAL/negative > UNSPECIFIED.
        # A structured record saying `required=false` already produced OPTIONAL
        # from `_classify_value`, so explicit REQUIRED from other records still wins
        # while that record does not silently override them.
        for requirement in classified:
            if requirement.kind == LanguageRequirementKind.REQUIRED:
                level = next(
                    (r.minimum_level for r in classified
                     if r.kind == LanguageRequirementKind.REQUIRED and r.minimum_level),
                    "",
                )
                return LanguageRequirement(LanguageRequirementKind.REQUIRED, level)
        for requirement in classified:
            if requirement.kind == LanguageRequirementKind.OPTIONAL:
                level = next(
                    (r.minimum_level for r in classified
                     if r.kind == LanguageRequirementKind.OPTIONAL and r.minimum_level),
                    "",
                )
                return LanguageRequirement(LanguageRequirementKind.OPTIONAL, level)
        return LanguageRequirement(LanguageRequirementKind.UNSPECIFIED)

    @classmethod
    def _canonical_language(cls, value: str) -> str | None:
        normalized = cls.normalize(value)
        for language, aliases in cls.LANGUAGE_ALIASES.items():
            if normalized in aliases:
                return language
        return None

    @classmethod
    def _values_for_language(cls, requirements, language: str):
        aliases = cls.LANGUAGE_ALIASES[language]
        if isinstance(requirements, dict):
            nested = requirements.get("languages")
            if isinstance(nested, (list, dict)):
                yield from cls._values_for_language(nested, language)
            entry_language = requirements.get("language") or requirements.get("name")
            if entry_language and cls.normalize(entry_language) in aliases:
                yield requirements
            for name, value in requirements.items():
                if cls.normalize(name) in aliases:
                    yield value
        elif isinstance(requirements, list):
            for item in requirements:
                if isinstance(item, dict):
                    entry_language = item.get("language") or item.get("name")
                    if entry_language and cls.normalize(entry_language) in aliases:
                        yield item
                elif any(alias in cls.normalize(item).split() for alias in aliases):
                    yield item

    @classmethod
    def _classify_value(cls, value) -> LanguageRequirement:
        if isinstance(value, bool):
            return LanguageRequirement(
                LanguageRequirementKind.REQUIRED if value else LanguageRequirementKind.OPTIONAL
            )
        if isinstance(value, dict):
            required = value.get("required")
            if isinstance(required, bool):
                kind = LanguageRequirementKind.REQUIRED if required else LanguageRequirementKind.OPTIONAL
                return LanguageRequirement(kind, cls._extract_level(value))
            if required is not None:
                classified = cls._classify_text(f"required={required}")
                if classified.kind != LanguageRequirementKind.UNSPECIFIED:
                    return LanguageRequirement(classified.kind, cls._extract_level(value))
            for key in ("requirement_type", "status", "type", "level"):
                if key in value:
                    classified = cls._classify_text(value[key])
                    if classified.kind != LanguageRequirementKind.UNSPECIFIED:
                        level = cls._extract_level(value)
                        return LanguageRequirement(classified.kind, level)
            level = cls._extract_level(value)
            if level:
                return LanguageRequirement(LanguageRequirementKind.REQUIRED, level)
            return LanguageRequirement(LanguageRequirementKind.UNSPECIFIED)
        return cls._classify_text(value)

    @classmethod
    def _classify_text(cls, value) -> LanguageRequirement:
        raw = str(value or "")
        normalized = cls.normalize(raw).replace("_", " ")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if normalized in cls.UNKNOWN_MARKERS:
            return LanguageRequirement(LanguageRequirementKind.UNSPECIFIED)
        if re.search(r"required\s*[:=]\s*(false|no|0)\b", normalized):
            return LanguageRequirement(LanguageRequirementKind.OPTIONAL, cls._extract_level(value))
        if re.search(r"required\s*[:=]\s*(true|yes|1)\b", normalized):
            return LanguageRequirement(LanguageRequirementKind.REQUIRED, cls._extract_level(value))
        # Negative requirement phrases must be detected before bare required markers,
        # otherwise "not required" / "no requirement" would match required/requirement.
        for negative in cls.NEGATIVE_MARKERS:
            if negative in normalized:
                return LanguageRequirement(LanguageRequirementKind.OPTIONAL, cls._extract_level(value))
        # "no <language> required" / "no <language> mandatory" negations must
        # not classify as REQUIRED even though they contain the bare "required"
        # word. Use targeted regex instead of broad substring rules.
        if cls.NEGATIVE_REQUIRED_PATTERN.search(normalized) or cls.NEGATIVE_MANDATORY_PATTERN.search(normalized):
            return LanguageRequirement(LanguageRequirementKind.OPTIONAL, cls._extract_level(value))
        # "not optional" / "non facultatif" / "pas facultatif" must classify as
        # REQUIRED, not optional; check before bare OPTIONAL_MARKERS so the
        # substring "optional" does not reverse the negated phrase.
        if cls.NOT_OPTIONAL_PATTERN.search(normalized) or cls.NOT_FACULTATIF_PATTERN.search(normalized):
            return LanguageRequirement(LanguageRequirementKind.REQUIRED, cls._extract_level(value))
        for marker in cls.OPTIONAL_MARKERS:
            if marker in normalized:
                return LanguageRequirement(LanguageRequirementKind.OPTIONAL, cls._extract_level(value))
        if normalized in {"true", "yes"} or any(marker in normalized for marker in cls.REQUIRED_MARKERS):
            return LanguageRequirement(LanguageRequirementKind.REQUIRED, cls._extract_level(value))
        if normalized in {"false", "no"}:
            return LanguageRequirement(LanguageRequirementKind.OPTIONAL, cls._extract_level(value))
        level = cls._extract_level(value)
        if level:
            # Bare CEFR level expressions (B2, B2+, B2 ou plus, B2 minimum, niveau B2)
            # are interpreted as REQUIRED with that minimum level, because "plus"
            # here means a higher level, not a "nice to have" marker.
            return LanguageRequirement(LanguageRequirementKind.REQUIRED, level)
        return LanguageRequirement(LanguageRequirementKind.UNSPECIFIED)

    @classmethod
    def _extract_level(cls, value) -> str:
        values = value.values() if isinstance(value, dict) else [value]
        for item in values:
            match = cls.LEVEL_PATTERN.search(cls.normalize(item))
            if match:
                return match.group(1).casefold()
        return ""