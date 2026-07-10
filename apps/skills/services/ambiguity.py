import re
import unicodedata


METADATA_NOISE_TERMS = {
    "a verifier",
    "badge",
    "certifie",
    "source",
    "status",
    "statut",
    "to verify",
    "verified",
    "verifie",
    "verifie",
    "verifiee",
    "verifies",
}


def normalize_context_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s#\.+]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_metadata_noise(text: str | None) -> bool:
    normalized = normalize_context_text(text)
    return normalized in METADATA_NOISE_TERMS


def implied_aliases_for_phrase(text: str | None) -> list[str]:
    normalized = normalize_context_text(text)
    if not normalized:
        return []

    implied: list[str] = []
    if _has_standalone_sql_evidence(normalized):
        implied.append("sql")
    if re.search(r"\b(?:chef cookbooks?|chef infra|chef recipes?|devops chef)\b", normalized):
        implied.append("chef")
    if re.search(r"\bconfiguration management with chef\b", normalized):
        implied.append("chef")
    if re.search(r"\b(?:go developer|go programming|backend go|golang)\b", normalized):
        implied.append("go")
    if "c c++" in normalized or re.search(r"\b(?:ansi c|embedded c|c programming|c language|langage c)\b", normalized):
        implied.append("c")
    if "c c++" in normalized:
        implied.append("c++")
    if re.search(r"\b(?:r programming|r shiny|r language|rstudio|r studio)\b", normalized):
        implied.append("r")
    if re.search(r"\b(?:oracle database|oracle db|oracle pl/sql|oracle sql|oracle dba)\b", normalized):
        implied.append("oracle")

    return list(dict.fromkeys(implied))


def is_allowed_skill_match(
    *,
    raw_text: str | None,
    canonical_name: str | None,
    alias: str | None = None,
    context: str | None = None,
) -> bool:
    normalized_raw = normalize_context_text(raw_text)
    normalized_context = normalize_context_text(context) if context else normalized_raw
    normalized_alias = normalize_context_text(alias) if alias else normalized_raw
    canonical = normalize_context_text(canonical_name)

    if not normalized_raw or is_metadata_noise(normalized_raw):
        return False

    if canonical == "sql":
        return _has_standalone_sql_evidence(normalized_context or normalized_raw)
    if canonical == "chef":
        return _has_chef_devops_evidence(normalized_context or normalized_raw)
    if canonical == "go" and normalized_alias == "go":
        return _has_go_language_evidence(normalized_context or normalized_raw, bool(context))
    if canonical == "c" and normalized_alias == "c":
        return _has_c_language_evidence(normalized_context or normalized_raw, bool(context))
    if canonical == "r" and normalized_alias == "r":
        return _has_r_language_evidence(normalized_context or normalized_raw, bool(context))
    if canonical in {"spring boot", "spring"} and normalized_alias == "spring":
        return _has_spring_framework_evidence(normalized_context or normalized_raw)
    if canonical in {"oracle db", "oracle"} and normalized_alias == "oracle":
        return _has_oracle_database_evidence(normalized_context or normalized_raw)

    return True


def evidence_candidate_for_match(*, alias: str, canonical_name: str | None, context: str | None) -> str:
    normalized_alias = normalize_context_text(alias)
    normalized_context = normalize_context_text(context)
    canonical = normalize_context_text(canonical_name)

    if canonical == "chef" and normalized_alias == "chef":
        return _first_match(
            normalized_context,
            [
                r"\bchef cookbooks?\b",
                r"\bchef infra\b",
                r"\bchef recipes?\b",
                r"\bdevops chef\b",
                r"\bconfiguration management with chef\b",
            ],
            alias,
        )
    if canonical in {"oracle db", "oracle"} and normalized_alias == "oracle":
        return _first_match(
            normalized_context,
            [r"\boracle database\b", r"\boracle db\b", r"\boracle pl/sql\b", r"\boracle sql\b", r"\boracle dba\b"],
            alias,
        )
    if canonical == "r" and normalized_alias == "r":
        return _first_match(
            normalized_context,
            [r"\br programming\b", r"\br shiny\b", r"\br language\b", r"\br studio\b", r"\brstudio\b"],
            alias,
        )
    if canonical == "c" and normalized_alias == "c":
        return _first_match(
            normalized_context,
            [r"\bc c\+\+\b", r"\bansi c\b", r"\bembedded c\b", r"\bc programming\b", r"\bc language\b"],
            alias,
        )
    if canonical == "go" and normalized_alias == "go":
        return _first_match(
            normalized_context,
            [r"\bgo developer\b", r"\bgo programming\b", r"\bbackend go\b", r"\bgo language\b"],
            alias,
        )
    if canonical in {"spring boot", "spring"} and normalized_alias == "spring":
        return _first_match(normalized_context, [r"\bspring boot\b", r"\bspring framework\b", r"\bjava spring\b"], alias)
    return alias


def _first_match(text: str, patterns: list[str], fallback: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return fallback


def _has_standalone_sql_evidence(text: str) -> bool:
    if re.search(r"\bnosql\b", text):
        text = re.sub(r"\bnosql\b", " ", text)

    blocked_followers = {"server"}
    for match in re.finditer(r"\bsql\b", text):
        tail = text[match.end(): match.end() + 24]
        next_word = re.match(r"\s+([a-z0-9#\.+]+)", tail)
        if next_word and next_word.group(1) in blocked_followers:
            continue
        return True
    return False


def _has_chef_devops_evidence(text: str) -> bool:
    if re.search(
        r"\b(?:chef de projet|chef projet|chef d equipe|chef d'equipe|chef d equipe|chef de produit|"
        r"chef cuisinier|cuisinier|cuisine|restauration|hospitality|restaurant chef|kitchen chef|"
        r"head chef|project manager|team lead|product manager)\b",
        text,
    ):
        return False
    return bool(
        re.search(
            r"\b(?:chef cookbooks?|chef infra|chef recipes?|devops chef|configuration management with chef)\b",
            text,
        )
    )


def _has_go_language_evidence(text: str, requires_context: bool) -> bool:
    if re.search(r"\b(?:go to|go live|go to market|go no go)\b", text):
        return False
    if "golang" in text:
        return True
    if re.search(r"\b(?:go developer|go programming|backend go|go language|langage go)\b", text):
        return True
    return not requires_context and text == "go"


def _has_c_language_evidence(text: str, requires_context: bool) -> bool:
    if re.search(r"\b(?:c level|c-level|category c|permis c|section c)\b", text):
        return False
    if "c c++" in text or re.search(r"\b(?:ansi c|embedded c|c programming|c language|langage c)\b", text):
        return True
    return not requires_context and text == "c"


def _has_r_language_evidence(text: str, requires_context: bool) -> bool:
    if re.search(r"\b(?:r&d|r d|r and d)\b", text):
        return False
    if re.search(r"\b(?:r programming|r shiny|r language|r studio|rstudio)\b", text):
        return True
    return not requires_context and text == "r"


def _has_spring_framework_evidence(text: str) -> bool:
    if re.search(r"\b(?:spring season|spring internship)\b", text):
        return False
    return bool(re.search(r"\b(?:spring boot|spring framework|java spring)\b", text))


def _has_oracle_database_evidence(text: str) -> bool:
    return bool(re.search(r"\b(?:oracle database|oracle db|oracle pl/sql|oracle sql|oracle dba)\b", text))
