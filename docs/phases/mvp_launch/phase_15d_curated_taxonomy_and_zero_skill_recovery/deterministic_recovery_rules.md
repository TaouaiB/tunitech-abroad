# Deterministic Zero-Skill Recovery Rules

## Principle

Only add skills when the stored job text explicitly supports them.

Do not add skills from title alone unless the title is highly specific and the description confirms the domain.

## Phrase-to-skill recovery candidates

The implementation must map through canonical `Skill` / `SkillAlias`; it must not create free-text `NormalizedJobSkill`.

### Support / workstation

French/English evidence:
- support aux utilisateurs
- support utilisateur
- assistance technique
- dépannage
- résoudre les incidents
- traitement des incidents
- parc informatique
- équipements informatiques
- maintenance matériel informatique
- installation/configuration des équipements
- déploiement postes / déploiement informatique
- logiciel bureautique

Candidate skills:
- IT Support
- Troubleshooting
- Hardware Maintenance
- Workstation Deployment
- Software Installation

### Systems / network

Evidence:
- administration systèmes et réseaux
- systèmes et réseaux
- serveurs
- réseau / réseaux
- LAN/WAN
- VPN
- segmentation
- infrastructure réseau
- architecture réseau
- supervision réseau
- disponibilité matérielle informatique

Candidate skills:
- System Administration
- Network Administration
- Network Security
- VPN
- Monitoring

### Security / cyber

Evidence:
- sécurité informatique
- cybersécurité
- règles de sécurité
- incidents de sécurité
- durcissement
- bonnes pratiques cybersécurité
- gestion des vulnérabilités
- exigences de cybersécurité

Candidate skills:
- Cybersecurity
- Network Security
- Vulnerability Management
- Security Hardening
- Risk Analysis

### Software/development

Evidence:
- développement web
- développement logiciel
- développement informatique
- maintien des applications
- applications existantes ou nouvelles
- correction de bugs
- résolution de bugs
- optimisation
- simulateurs
- outils logiciels
- tests automatisés

Candidate skills:
- Software Development
- Web Development
- Debugging
- Performance Optimization
- Software Testing
- Software Maintenance

### Documentation/project support

Evidence:
- documentation technique
- modes opératoires
- rédiger de nouveaux modes opératoires
- suivi de projets
- analyse des besoins

Candidate skills:
- Technical Documentation
- Requirements Analysis

## Guardrails

- If evidence only says `IT experience`, do not create a skill.
- If evidence is only diploma/training (`BTS SIO`, `Bac Pro CIEL`, `Bachelor`), do not create a skill.
- If job is commercial/business/outreach, do not force technical skills.
- Confidence should be lower than explicit extracted skills if the model supports confidence.
- Source should be `rule` or equivalent deterministic source, not `llm` and not `admin`.
- The recovery service must be idempotent.
- It must not duplicate existing `NormalizedJobSkill`.
