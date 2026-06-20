import re
from dataclasses import dataclass

from apps.jobs.services.skill_extraction import GENERIC_FT_LABELS


STRONG_SKILL_TERMS = (
    "python",
    "django",
    "java",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "nodejs",
    "angular",
    "c#",
    ".net",
    "devops",
    "sre",
    "data engineer",
    "tech lead",
    "cybersécurité",
    "cybersecurite",
    "cybersecurity",
    "réseau",
    "reseau",
    "cloud",
    "aws",
    "gcp",
    "azure",
    "linux",
    "postgresql",
    "postgres",
    "sql",
    "api",
    "backend",
    "back-end",
    "frontend",
    "front-end",
    "full-stack",
    "full stack",
    "administrateur systèmes",
    "administrateur systemes",
    "administrateur système",
    "administrateur systeme",
    "ingénieur logiciel",
    "ingenieur logiciel",
    "algorithme",
    "algorithmes",
    "algorithmique",
    "optimisation logicielle",
)

IT_ROLE_TERMS = (
    "développeur",
    "developpeur",
    "développeuse",
    "developpeuse",
    "software engineer",
    "ingénieur logiciel",
    "ingenieur logiciel",
    "data engineer",
    "tech lead",
    "devops",
    "sre",
    "administrateur systèmes",
    "administrateur systemes",
    "administrateur système",
    "administrateur systeme",
    "cybersécurité",
    "cybersecurite",
    "cybersecurity",
    "ingénieur en optimisation",
    "ingenieur en optimisation",
)


@dataclass(frozen=True)
class SkillSignalResult:
    quality: str
    evidence_terms: tuple[str, ...]


def _contains_term(text: str, term: str) -> bool:
    if not term:
        return False
    escaped = re.escape(term.lower())
    if re.search(rf"(?<![\w+#.-]){escaped}(?![\w+#.-])", text):
        return True
    return term.lower() in text


def _terms_in_text(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if _contains_term(text, term)]


def _raw_payload_skills(job) -> tuple[list[str], list[str]]:
    raw_payload = {}
    raw_record = getattr(job, "raw_record", None)
    if raw_record and isinstance(raw_record.raw_payload_json, dict):
        raw_payload = raw_record.raw_payload_json

    required: list[str] = []
    optional: list[str] = []
    competences = raw_payload.get("competences") or []
    if not isinstance(competences, list):
        return required, optional

    for competence in competences:
        if not isinstance(competence, dict):
            continue
        label = competence.get("libelle")
        if not isinstance(label, str) or not label.strip():
            continue
        if competence.get("exigence") == "E":
            required.append(label)
        else:
            optional.append(label)
    return required, optional


def compute_deterministic_skill_signal_quality(job) -> SkillSignalResult:
    classification_json = job.classification_json or {}
    family = classification_json.get("family")
    is_it = classification_json.get("is_it")
    confidence = classification_json.get("confidence")

    if is_it is False or family == "non_it" or confidence == "excluded":
        return SkillSignalResult("excluded_non_it", ())

    title_description = f"{job.title or ''} {job.description or ''}".lower()
    required_json = job.required_skills_json if isinstance(job.required_skills_json, list) else []
    optional_json = job.optional_skills_json if isinstance(job.optional_skills_json, list) else []
    raw_required, raw_optional = _raw_payload_skills(job)

    required_text = " ".join(str(value) for value in [*required_json, *raw_required]).lower()
    optional_text = " ".join(str(value) for value in [*optional_json, *raw_optional]).lower()
    source_skill_text = f"{required_text} {optional_text}".strip()
    all_text = f"{title_description} {source_skill_text}".strip()

    required_terms = _terms_in_text(required_text, STRONG_SKILL_TERMS)
    optional_terms = _terms_in_text(optional_text, STRONG_SKILL_TERMS)
    text_terms = _terms_in_text(title_description, STRONG_SKILL_TERMS)
    role_terms = _terms_in_text(title_description, IT_ROLE_TERMS)
    generic_terms = [
        label
        for label in GENERIC_FT_LABELS
        if label and label.lower() in source_skill_text
    ]

    if required_json or required_terms:
        return SkillSignalResult("strong", tuple(dict.fromkeys([*required_terms, *text_terms])))

    if optional_json or optional_terms:
        return SkillSignalResult("partial", tuple(dict.fromkeys([*optional_terms, *text_terms])))

    if len(text_terms) >= 2:
        return SkillSignalResult("partial", tuple(text_terms))

    if role_terms and text_terms:
        return SkillSignalResult("partial", tuple(dict.fromkeys([*role_terms, *text_terms])))

    if role_terms and confidence == "high":
        return SkillSignalResult("partial", tuple(role_terms))

    if text_terms and confidence == "high":
        return SkillSignalResult("partial", tuple(text_terms))

    if generic_terms:
        return SkillSignalResult("generic_only", tuple(generic_terms))

    if not all_text:
        return SkillSignalResult("missing", ())

    return SkillSignalResult("missing", ())
