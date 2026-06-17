import re
from urllib.parse import urlparse


CURRENT_LEVEL_CHOICES = [
    ("", "Sélectionner"),
    ("student", "Étudiant"),
    ("intern", "Stagiaire"),
    ("junior", "Junior"),
    ("mid", "Confirmé"),
    ("senior", "Senior"),
]

LANGUAGE_LEVEL_CHOICES = [
    ("", "Sélectionner"),
    ("basic", "Notions"),
    ("intermediate", "Intermédiaire"),
    ("fluent", "Professionnel / courant"),
    ("native", "Natif"),
]

REMOTE_PREFERENCE_CHOICES = [
    ("", "Sélectionner"),
    ("on_site", "Présentiel"),
    ("hybrid", "Hybride"),
    ("remote_only", "Télétravail"),
    ("any", "Ouvert à plusieurs formats"),
]

RELOCATION_PREFERENCE_CHOICES = [
    ("", "Sélectionner"),
    ("yes", "Oui"),
    ("no", "Non"),
    ("open", "À discuter"),
]

TARGET_TYPE_CHOICES = [
    ("", "Sélectionner"),
    ("job", "Emploi"),
    ("internship", "Stage"),
    ("apprenticeship", "Alternance"),
    ("any", "Ouvert à plusieurs opportunités"),
]

TARGET_JOB_TYPE_CHOICES = [
    ("full_time_job", "CDI / temps plein"),
    ("contract", "Contrat / mission"),
    ("internship", "Stage"),
    ("apprenticeship", "Alternance"),
]

MEANINGLESS_VALUES = {
    "qsd",
    "qsdqsd",
    "asdf",
    "azerty",
    "test",
    "none",
    "n/a",
    "na",
    "xxx",
}


def normalize_profile_url(value: str | None) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Saisissez une URL complète commençant par http:// ou https://.")
    return value


def is_meaningful_text(value: str | None, *, min_length: int = 3) -> bool:
    cleaned = re.sub(r"\s+", " ", (value or "").strip()).lower()
    if len(cleaned) < min_length:
        return False
    compact = re.sub(r"[^a-z0-9]+", "", cleaned)
    if compact in MEANINGLESS_VALUES:
        return False
    if len(set(compact)) <= 2 and len(compact) >= 3:
        return False
    return True


def meaningful_list(values: list[str] | None) -> list[str]:
    cleaned = []
    for value in values or []:
        text = re.sub(r"\s+", " ", str(value).strip())
        if is_meaningful_text(text):
            cleaned.append(text)
    return cleaned
