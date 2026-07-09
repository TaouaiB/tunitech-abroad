import re
from typing import Any, TypedDict


class NameExtractionResult(TypedDict):
    value: str | None
    confidence: int
    candidates: list[dict[str, Any]]
    warnings: list[str]


class CVNameExtractionService:
    FIRST_PERSON_PATTERNS = (
        r"\bje\s+(me\s+)?suis\b",
        r"\bj['’]ai\b",
        r"\bje\s+m['’]appelle\b",
        r"\bi\s+am\b",
        r"\bmy\s+name\s+is\b",
        r"\bmy\b",
    )
    SECTION_HEADERS = {
        "skills",
        "skill",
        "competences",
        "compétences",
        "experience",
        "expérience",
        "education",
        "formation",
        "profile",
        "profil",
        "about me",
        "à propos",
        "contact",
        "languages",
        "langues",
        "projects",
        "projets",
        "certifications",
    }
    JOB_TITLE_TOKENS = {
        "developer",
        "développeur",
        "developpeur",
        "engineer",
        "ingénieur",
        "ingenieur",
        "student",
        "étudiant",
        "etudiant",
        "junior",
        "senior",
        "intern",
        "stagiaire",
        "stage",
        "full stack",
        "frontend",
        "front-end",
        "backend",
        "back-end",
        "software",
        "data scientist",
        "designer",
    }
    CV_PROSE_TOKENS = {
        "passionné",
        "passionne",
        "passionate",
        "motivated",
        "motivé",
        "experience",
        "expérience",
        "seeking",
        "looking",
        "recherche",
        "candidate",
    }
    LABEL_PATTERN = re.compile(
        r"^(?:nom(?:\s+et\s+pr[eé]nom)?|pr[eé]nom\s+nom|name|full\s+name)\s*:\s*(?P<value>[^\n\r]+)$",
        re.IGNORECASE,
    )

    @classmethod
    def extract(cls, raw_text: str, auth_user_name: str = "", email: str = "", user=None) -> NameExtractionResult:
        if user is not None:
            auth_user_name = auth_user_name or cls._name_from_user(user)
            email = email or getattr(user, "email", "")

        candidates: list[dict[str, Any]] = []
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        for line in lines[:30]:
            match = cls.LABEL_PATTERN.search(line)
            if match:
                cls._add_candidate(candidates, match.group("value").strip(), "explicit_label", 95)

        for index, line in enumerate(lines[:10]):
            score = max(45, 82 - (index * 5))
            if line.isupper():
                score += 4
            cls._add_candidate(candidates, line, "top_line", score)

        email_words = cls._email_words(email)
        if email_words:
            for line in lines[:15]:
                accepted, _reason = cls._validate_name(line)
                if not accepted:
                    continue
                candidate_words = {word.lower() for word in line.split()}
                if candidate_words.intersection(email_words):
                    cls._add_candidate(candidates, line, "email_hint", 86)

        if auth_user_name:
            cls._add_candidate(candidates, auth_user_name.strip(), "auth_user", 75)

        accepted = [candidate for candidate in candidates if candidate["reject_reason"] is None]
        best = max(accepted, key=lambda candidate: candidate["score"], default=None)
        warnings: list[str] = []

        if best and best["score"] >= 70:
            return {
                "value": cls._format_name(best["value"]),
                "confidence": int(best["score"]),
                "candidates": candidates,
                "warnings": warnings,
            }

        warnings.append("low_confidence_name")
        return {
            "value": None,
            "confidence": int(best["score"]) if best else 0,
            "candidates": candidates,
            "warnings": warnings,
        }

    @classmethod
    def _add_candidate(cls, candidates: list[dict[str, Any]], value: str, source: str, score: int) -> None:
        cleaned = cls._clean_candidate(value)
        accepted, reject_reason = cls._validate_name(cleaned)
        candidates.append(
            {
                "value": cleaned,
                "source": source,
                "score": int(score) if accepted else 0,
                "reject_reason": reject_reason,
            }
        )

    @classmethod
    def _validate_name(cls, value: str) -> tuple[bool, str | None]:
        if not value:
            return False, "empty"
        if len(value) > 80:
            return False, "too_long"

        lowered = value.lower().strip()
        ascii_lowered = cls._strip_accents_for_matching(lowered)

        if lowered in cls.SECTION_HEADERS or ascii_lowered in cls.SECTION_HEADERS:
            return False, "section_header"
        if any(re.search(pattern, lowered) for pattern in cls.FIRST_PERSON_PATTERNS):
            return False, "first_person_phrase"
        if any(token in lowered or token in ascii_lowered for token in cls.JOB_TITLE_TOKENS):
            return False, "job_title"
        if any(token in lowered or token in ascii_lowered for token in cls.CV_PROSE_TOKENS):
            return False, "cv_prose"
        if "@" in value or "http" in lowered or "www" in lowered:
            return False, "contact_or_url"
        if re.search(r"\b(?:\+?\d[\d .-]{5,}\d)\b", value):
            return False, "phone"
        if re.search(r"\b(?:19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", value):
            return False, "date"
        if any(mark in value for mark in (".", ",", "|", "•", ";", ":", "!", "?")):
            return False, "sentence_or_delimited_text"

        words = value.split()
        if not 2 <= len(words) <= 4:
            return False, "word_count"
        if value.islower() and len(words) >= 3:
            return False, "lowercase_prose"
        if not all(re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ'’-]+", word) for word in words):
            return False, "invalid_characters"
        if len(value) > 45 and len(words) >= 4:
            return False, "sentence_like"

        return True, None

    @staticmethod
    def _clean_candidate(value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().strip("-–—"))

    @staticmethod
    def _format_name(value: str) -> str:
        if value.isupper():
            return value
        return " ".join(word[:1].upper() + word[1:] for word in value.split())

    @staticmethod
    def _email_words(email: str) -> set[str]:
        if not email or "@" not in email:
            return set()
        local_part = email.split("@", 1)[0]
        return {
            word.lower()
            for word in re.split(r"[._+\-\d]+", local_part)
            if len(word) > 2 and word.isalpha()
        }

    @staticmethod
    def _name_from_user(user) -> str:
        first_name = getattr(user, "first_name", "") or ""
        last_name = getattr(user, "last_name", "") or ""
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            return full_name
        profile = getattr(user, "candidate_profile", None)
        return getattr(profile, "full_name", "") or ""

    @staticmethod
    def _strip_accents_for_matching(value: str) -> str:
        translation = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")
        return value.translate(translation)
