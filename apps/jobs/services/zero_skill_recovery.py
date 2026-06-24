from typing import Dict, TypedDict, List
from apps.jobs.models import NormalizedJob, NormalizedJobSkill, RequirementType, SkillSource
from apps.skills.models import Skill
from apps.skills.services.normalizer import normalize_skill_text

class RecoveryResult(TypedDict):
    jobs_inspected: int
    skipped_excluded: int
    recovered_jobs: int
    skills_created: int
    still_zero_skill: int
    skipped_existing_skills: int
    examples: list[str]

class ZeroSkillJobRecoveryService:
    # phrase -> canonical names
    # As defined in deterministic_recovery_rules.md
    RECOVERY_RULES = {
        # Support / workstation
        "support aux utilisateurs": ["IT Support"],
        "support utilisateur": ["IT Support"],
        "assistance technique": ["IT Support"],
        "dépannage": ["Troubleshooting"],
        "depannage": ["Troubleshooting"],
        "résoudre les incidents": ["Troubleshooting"],
        "resoudre les incidents": ["Troubleshooting"],
        "traitement des incidents": ["Troubleshooting"],
        "parc informatique": ["Hardware Maintenance", "IT Support"],
        "équipements informatiques": ["Hardware Maintenance"],
        "equipements informatiques": ["Hardware Maintenance"],
        "maintenance matériel informatique": ["Hardware Maintenance"],
        "maintenance materiel informatique": ["Hardware Maintenance"],
        "installation/configuration des équipements": ["Workstation Deployment"],
        "installation configuration des equipements": ["Workstation Deployment"],
        "déploiement postes": ["Workstation Deployment"],
        "deploiement postes": ["Workstation Deployment"],
        "déploiement informatique": ["Workstation Deployment"],
        "deploiement informatique": ["Workstation Deployment"],
        "logiciel bureautique": ["Software Installation"],
        
        # Systems / network
        "administration systèmes et réseaux": ["System Administration", "Network Administration"],
        "administration systemes et reseaux": ["System Administration", "Network Administration"],
        "systèmes et réseaux": ["System Administration", "Network Administration"],
        "systemes et reseaux": ["System Administration", "Network Administration"],
        "serveurs": ["System Administration"],
        "réseau": ["Network Administration"],
        "réseaux": ["Network Administration"],
        "reseau": ["Network Administration"],
        "reseaux": ["Network Administration"],
        "lan/wan": ["Network Administration"],
        "lan wan": ["Network Administration"],
        "vpn": ["VPN"],
        "segmentation": ["Network Security"],
        "infrastructure réseau": ["Network Administration"],
        "infrastructure reseau": ["Network Administration"],
        "architecture réseau": ["Network Administration"],
        "architecture reseau": ["Network Administration"],
        "supervision réseau": ["Monitoring"],
        "supervision reseau": ["Monitoring"],
        "disponibilité matérielle informatique": ["Hardware Maintenance"],
        "disponibilite materielle informatique": ["Hardware Maintenance"],
        
        # Security / cyber
        "sécurité informatique": ["Cybersecurity"],
        "securite informatique": ["Cybersecurity"],
        "cybersécurité": ["Cybersecurity"],
        "cybersecurite": ["Cybersecurity"],
        "règles de sécurité": ["Cybersecurity"],
        "regles de securite": ["Cybersecurity"],
        "incidents de sécurité": ["Cybersecurity"],
        "incidents de securite": ["Cybersecurity"],
        "durcissement": ["Security Hardening"],
        "bonnes pratiques cybersécurité": ["Cybersecurity"],
        "bonnes pratiques cybersecurite": ["Cybersecurity"],
        "gestion des vulnérabilités": ["Vulnerability Management"],
        "gestion des vulnerabilites": ["Vulnerability Management"],
        "exigences de cybersécurité": ["Cybersecurity"],
        "exigences de cybersecurite": ["Cybersecurity"],

        # Software/development
        "développement web": ["Web Development"],
        "developpement web": ["Web Development"],
        "développement logiciel": ["Software Development"],
        "developpement logiciel": ["Software Development"],
        "développement informatique": ["Software Development"],
        "developpement informatique": ["Software Development"],
        "maintien des applications": ["Software Maintenance"],
        "applications existantes ou nouvelles": ["Software Development"],
        "correction de bugs": ["Debugging"],
        "résolution de bugs": ["Debugging"],
        "resolution de bugs": ["Debugging"],
        "optimisation": ["Performance Optimization"],
        "simulateurs": ["Software Development"],
        "outils logiciels": ["Software Development"],
        "tests automatisés": ["Software Testing"],
        "tests automatises": ["Software Testing"],

        # Documentation/project support
        "documentation technique": ["Technical Documentation"],
        "modes opératoires": ["Technical Documentation"],
        "modes operatoires": ["Technical Documentation"],
        "rédiger de nouveaux modes opératoires": ["Technical Documentation"],
        "rediger de nouveaux modes operatoires": ["Technical Documentation"],
        "suivi de projets": ["Requirements Analysis"],
        "analyse des besoins": ["Requirements Analysis"],
    }
    
    EXCLUDED_JOB_TITLES = [
        "sdr", "bdr", "business developer", "commercial", "médiateur", "mediateur", 
        "scientifique", "professeur", "enseignant", "formateur", "transformation digitale",
        "consultant transformation"
    ]
    EXCLUDED_ROLE_TEXT = [
        "vente de solutions",
        "prospection",
        "developpement commercial",
        "développement commercial",
        "sensibilisation",
        "mediation scientifique",
        "médiation scientifique",
        "accompagnement transformation",
        "transformation digitale",
    ]

    @classmethod
    def _is_excluded(cls, job: NormalizedJob) -> bool:
        classification = job.classification_json if isinstance(job.classification_json, dict) else {}
        if (
            classification.get("is_it") is False
            or classification.get("family") in {"non_it", "business", "commercial", "outreach"}
            or job.skill_signal_quality == "excluded_non_it"
        ):
            return True

        title_lower = (job.title or "").lower()
        for excluded in cls.EXCLUDED_JOB_TITLES:
            if excluded in title_lower:
                return True

        normalized_text = normalize_skill_text(f"{job.title or ''} {job.description or ''}")
        for excluded in cls.EXCLUDED_ROLE_TEXT:
            if normalize_skill_text(excluded) in normalized_text:
                return True
        return False

    @classmethod
    def _get_skill_map(cls) -> Dict[str, Skill]:
        skill_names = set()
        for names in cls.RECOVERY_RULES.values():
            skill_names.update(names)
            
        skills = Skill.objects.filter(canonical_name__in=skill_names, is_active=True)
        return {s.canonical_name: s for s in skills}

    @classmethod
    def recover_queryset(cls, queryset, *, dry_run: bool = False) -> RecoveryResult:
        result = RecoveryResult(
            jobs_inspected=0,
            skipped_excluded=0,
            recovered_jobs=0,
            skills_created=0,
            still_zero_skill=0,
            skipped_existing_skills=0,
            examples=[],
        )
        
        skill_map = cls._get_skill_map()
        
        for job in queryset:
            result['jobs_inspected'] += 1
            if NormalizedJobSkill.objects.filter(job=job).exists():
                result['skipped_existing_skills'] += 1
                continue

            if cls._is_excluded(job):
                result['skipped_excluded'] += 1
                result['still_zero_skill'] += 1
                continue
                
            text_to_search = f"{job.title} {job.description}".lower()
            normalized_text = normalize_skill_text(text_to_search)
            
            skills_to_add = set()
            for phrase, canonicals in cls.RECOVERY_RULES.items():
                if phrase.lower() in text_to_search or normalize_skill_text(phrase) in normalized_text:
                    for c in canonicals:
                        if c in skill_map:
                            skills_to_add.add(skill_map[c])
                            
            if skills_to_add:
                created_count = 0
                for skill in skills_to_add:
                    if dry_run:
                        created_count += 1
                        continue
                    _, created = NormalizedJobSkill.objects.get_or_create(
                        job=job,
                        skill=skill,
                        requirement_type=RequirementType.DETECTED,
                        defaults={
                            'source': SkillSource.RULE,
                            'confidence': 0.8
                        }
                    )
                    if created:
                        created_count += 1
                
                result['skills_created'] += created_count
                if created_count > 0:
                    result['recovered_jobs'] += 1
                    if len(result["examples"]) < 5:
                        skill_names = ", ".join(sorted(skill.canonical_name for skill in skills_to_add))
                        result["examples"].append(f"{job.id}: {job.title} -> {skill_names}")
                else:
                    # Skills were already present, which shouldn't happen if we strictly query jobs with 0 skills, but handles idempotency
                    result['still_zero_skill'] += 1
            else:
                result['still_zero_skill'] += 1
                
        return result

    @classmethod
    def recover_job(cls, job: NormalizedJob) -> RecoveryResult:
        return cls.recover_queryset([job])
