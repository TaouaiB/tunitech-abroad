# Zero-Skill Diagnostic Findings

## Current problem

Admin filter `Has materialized skills = No` is correctly showing active jobs with `job_skill_count=0`.

The problem is that some rows are genuinely technical and should not remain zero-skill.

## Diagnostic examples

### Should recover automatically

#### Apprenti(e) Technicien Informatique

Evidence:
- infrastructures
- réseaux
- sécurité
- parc informatique
- installation and maintenance of equipment
- incidents
- cybersécurité
- cloud
- support technique
- documentation technique

Expected possible skills, only if canonical skills exist:
- System Administration
- Network Administration
- Network Security
- IT Support
- Troubleshooting
- Hardware Maintenance
- Cybersecurity
- Cloud
- Technical Documentation
- Workstation Deployment

#### Apprenti / Apprentie infrastructure et sécurité informatique

Evidence:
- Infrastructure & Cybersécurité
- architecture réseau
- LAN/WAN
- VPN
- segmentation
- systèmes et réseaux
- supervision
- documentation technique
- durcissement

Expected possible skills:
- Network Administration
- Network Security
- Cybersecurity
- VPN
- System Administration
- Monitoring
- Technical Documentation
- Infrastructure Security

#### ALTERNANT EN INFORMATIQUE

Evidence:
- maintenance bureautique
- parc informatique
- configuration and update of software
- assistance technique
- support users
- déploiement et dépannage
- security access to network resources

Expected possible skills:
- IT Support
- Hardware Maintenance
- Workstation Deployment
- Software Installation
- Troubleshooting
- Access Management
- Network Administration

#### Développeur informatique

Evidence:
- développement web
- résolution de bugs
- optimisation
- suivi de projets

Expected possible skills:
- Web Development
- Debugging
- Performance Optimization
- Software Development

### Should probably stay excluded/manual

#### Business Developer / SDR Cybersécurité

Commercial role. Do not add cybersecurity as a technical skill unless the description requires technical security delivery.

#### Médiateur scientifique cybersécurité

Education/outreach role. May stay no technical skills or be excluded/low priority.

#### Consultant transformation digitale — transport/infrastructure/manufacturing/energy

May be business consulting, not IT candidate role. Keep excluded unless explicit technical tools/implementation skills exist.

## Root cause hypothesis

The current extractor/materializer is too dependent on explicit skill-list output. It misses mission-based technical evidence such as:
- support users
- incidents
- parc informatique
- systèmes et réseaux
- sécurité informatique
- LAN/WAN/VPN
- documentation technique
- déploiement
- dépannage

The `not_enough_text` status is misleading for jobs with descriptions of hundreds/thousands of characters. It likely means “not enough recognized skill candidates,” not truly “not enough text.”
