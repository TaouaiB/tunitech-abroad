from dataclasses import dataclass
from decimal import Decimal

from apps.skills.models import SkillCategory
from apps.skills.services.ambiguity import is_metadata_noise, normalize_context_text


class SkillCandidateKind:
    HARD_TECHNICAL = "hard_technical"
    BROAD_TECHNICAL = "broad_technical"
    METHODOLOGY_PROCESS = "methodology_process"
    SOFT_SKILL = "soft_skill"
    SOURCE_METADATA = "source_metadata"
    REJECTED_NOISE = "rejected_noise"


MATERIALIZABLE_KINDS = {
    SkillCandidateKind.HARD_TECHNICAL,
    SkillCandidateKind.BROAD_TECHNICAL,
}

NON_REQUIRED_KINDS = {
    SkillCandidateKind.BROAD_TECHNICAL,
    SkillCandidateKind.METHODOLOGY_PROCESS,
    SkillCandidateKind.SOFT_SKILL,
}

SOURCE_PHRASES = {
    "application web",
    "analyser exploiter structurer des donnees",
    "analyser les besoins informatiques",
    "analyser resoudre un probleme courant ou complexe",
    "administrer un systeme d informations",
    "anticiper les risques de cybersecurite",
    "apporter une assistance technique aux equipes",
    "coder des donnees",
    "collaborer avec des equipes multidisciplinaires",
    "collaborer avec une equipe projet",
    "communiquer aupres de ses interlocuteurs internes et externes",
    "concevoir l architecture d un systeme d un reseau",
    "concevoir un logiciel un systeme d informations une application",
    "concevoir une application web",
    "concevoir et developper une solution digitale",
    "concevoir et gerer un projet",
    "configurer et optimiser des systemes devops",
    "configurer le poste de travail aux besoins de l utilisateur",
    "depanner des equipements informatiques",
    "determiner des mesures correctives",
    "developper une application en lien avec une base de donnees",
    "developper un logiciel",
    "developper un logiciel un systeme d informations une application",
    "diagnostiquer la nature et l origine des incidents et mettre en oeuvre les mesures correctives",
    "evaluer le resultat de ses actions",
    "gerer et deployer des logiciels a distance",
    "gerer les risques de cybersecurite",
    "installer et integrer le materiel station equipement reseau peripheriques dans l environnement de production et configurer les ressources logistiques et physiques",
    "mener un processus de test en cybersecurite",
    "optimiser les processus de qualite pour assurer la fiabilite des logiciels",
    "promouvoir une proposition un projet",
    "recueillir et analyser les besoins client",
    "rediger un cahier des charges des specifications techniques",
    "tester un logiciel",
    "tester un logiciel un systeme d informations une application",
}

SOURCE_PHRASE_PREFIXES = (
    "administrer un systeme",
    "analyser les besoins",
    "analyser resoudre",
    "anticiper les risques",
    "apporter une assistance",
    "collaborer avec",
    "communiquer aupres",
    "concevoir l architecture",
    "concevoir un logiciel",
    "concevoir une application",
    "concevoir et",
    "configurer et optimiser",
    "configurer le poste",
    "depanner des equipements",
    "determiner des mesures",
    "developper une application",
    "diagnostiquer la nature",
    "evaluer le resultat",
    "gerer et deployer",
    "gerer les risques",
    "installer et integrer",
    "mener un processus",
    "optimiser les processus",
    "promouvoir une proposition",
    "rediger un cahier",
    "tester un logiciel",
)

BROAD_TECHNICAL_CANONICALS = {
    "api",
    "cloud",
    "monitoring",
    "technical documentation",
    "requirements analysis",
    "technical watch",
    "corrective maintenance",
    "software development",
    "software architecture",
    "software testing",
    "software analysis",
    "software quality",
    "digital project management",
    "technology selection",
    "specifications writing",
}

SPECIFIC_API_CANONICALS = {
    "rest api",
    "graphql",
    "swagger",
    "soap",
    "grpc",
    "stripe api",
    "twilio api",
}

SPECIFIC_MONITORING_CANONICALS = {
    "prometheus",
    "grafana",
    "datadog",
    "zabbix",
    "nagios",
    "sentry",
    "elk",
    "elasticsearch",
    "logstash",
    "kibana",
    "splunk",
    "new relic",
    "appdynamics",
    "rollbar",
    "icinga",
    "dynatrace",
}

API_TESTING_TERMS = {
    "api testing",
    "api automation",
    "api test automation",
    "api smoke tests",
}


@dataclass(frozen=True)
class SkillPolicyDecision:
    kind: str
    materialize: bool
    can_be_required: bool
    confidence_ceiling: Decimal | None = None


def is_generic_source_phrase(text: str | None) -> bool:
    normalized = normalize_context_text(text)
    if not normalized:
        return False
    return (
        normalized in SOURCE_PHRASES
        or any(phrase in normalized for phrase in SOURCE_PHRASES if len(phrase) > 14)
        or any(normalized.startswith(prefix) and len(normalized) > 18 for prefix in SOURCE_PHRASE_PREFIXES)
    )


def classify_skill_candidate(
    *,
    raw_text: str | None,
    canonical_name: str | None = None,
    category: str | None = None,
) -> SkillPolicyDecision:
    normalized_raw = normalize_context_text(raw_text)
    canonical = normalize_context_text(canonical_name)

    if not normalized_raw or is_metadata_noise(normalized_raw):
        return SkillPolicyDecision(SkillCandidateKind.SOURCE_METADATA, False, False)

    if is_generic_source_phrase(normalized_raw):
        return SkillPolicyDecision(SkillCandidateKind.SOURCE_METADATA, False, False)

    if normalized_raw in API_TESTING_TERMS:
        return SkillPolicyDecision(SkillCandidateKind.BROAD_TECHNICAL, True, False, Decimal("0.400"))

    if canonical in SPECIFIC_API_CANONICALS or canonical in SPECIFIC_MONITORING_CANONICALS:
        return SkillPolicyDecision(SkillCandidateKind.HARD_TECHNICAL, True, True)

    if canonical in BROAD_TECHNICAL_CANONICALS or normalized_raw in BROAD_TECHNICAL_CANONICALS:
        return SkillPolicyDecision(SkillCandidateKind.BROAD_TECHNICAL, True, False, Decimal("0.400"))

    if category == SkillCategory.SOFT_SKILL.value:
        return SkillPolicyDecision(SkillCandidateKind.SOFT_SKILL, False, False)

    if category == SkillCategory.METHODOLOGY.value:
        return SkillPolicyDecision(SkillCandidateKind.METHODOLOGY_PROCESS, False, False)

    return SkillPolicyDecision(SkillCandidateKind.HARD_TECHNICAL, True, True)

def classify_skill_candidate_with_alias(raw_text: str | None) -> SkillPolicyDecision:
    if not raw_text:
        return classify_skill_candidate(raw_text=raw_text)

    from apps.skills.models import SkillAlias
    from apps.skills.services.normalizer import candidate_normalized_skill_texts

    normalized_candidates = candidate_normalized_skill_texts(raw_text)
    aliases = list(
        SkillAlias.objects.filter(
            normalized_alias__in=normalized_candidates,
            skill__is_active=True,
        ).select_related("skill")
    )
    aliases.sort(key=lambda alias: len(alias.normalized_alias or ""), reverse=True)

    if aliases:
        alias = aliases[0]
        return classify_skill_candidate(
            raw_text=raw_text,
            canonical_name=alias.skill.canonical_name,
            category=alias.skill.category,
        )

    return classify_skill_candidate(raw_text=raw_text)
