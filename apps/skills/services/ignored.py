import re
import unicodedata

from apps.skills.services.phase_15d_decisions import approved_ignore_terms


def _normalize_for_ignore(text: str) -> str:
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s#\.+]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class IgnoredSkillService:
    # Exact normalized terms to ignore
    EXACT_TERMS = {
        "cnil eds",
        "documentation",
        "e commerce",
        "pedagogie",
        "groupes frigorifiques centrifuges",
        "informatique",
        "moteurs",
        "pompes",
        "reporting",
        "secteur iot",
        "secteur automobile",
        "secteur industriel",
        "systemes de traitement chimique de l eau",
        "systemes frigorifiques",
        "systemes mecaniques",
        "systemes electriques",
        "tableaux de bord",
        "tours de refroidissement",
        "asset management",
        "bac pro ciel",
        "bac pro mspc",
        "driver s license",
        "e health experience",
        "elementary",
        "experience in aeronautics sector",
        "experience in defense sector",
        "experience in industry sector",
        "experience secteur defense",
        "experience secteur industrie",
        "experience secteur public",
        "financial markets",
        "respect des procedures de securite",
        "respect des procedures qualite",
        "first experience",
    }

    # Prefix/suffix patterns for ignore
    NARROW_PATTERNS = [
        r"^bac pro\s",
        r"^secteur\s",
        r"^experience in .*(?:sector|industry|aeronautics|aerospace|defense|public)$",
        r"^experience secteur\s",
    ]

    NARROW_REGEX = re.compile("|".join(NARROW_PATTERNS)) if NARROW_PATTERNS else None

    @classmethod
    def is_ignored(cls, normalized_text: str) -> bool:
        if not normalized_text:
            return False

        normalized_text = _normalize_for_ignore(normalized_text)
            
        if normalized_text in cls.EXACT_TERMS or normalized_text in approved_ignore_terms():
            return True
            
        if cls.NARROW_REGEX and cls.NARROW_REGEX.match(normalized_text):
            return True
            
        return False
