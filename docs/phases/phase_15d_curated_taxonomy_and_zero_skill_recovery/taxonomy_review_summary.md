# TuniTech Phase 15D Taxonomy Review Summary
## Input files reviewed
- current_skills.csv
- current_skill_aliases.csv
- unmatched_skill_candidates_review.csv/jsonl
- jobs_needing_skill_review.csv/jsonl
## Main findings
- Pending unmatched candidates reviewed: **780**
- Candidates already resolved by current Skill/SkillAlias taxonomy: **166**
- Suggested aliases to existing canonical skills: **90**
- Suggested new canonical skills: **78**
- Suggested permanent ignore rules: **35**
- Keep pending for later/manual review: **411**

## Phase 15D approved scope
Phase 15D should implement only rows where `approved_for_phase_15d=yes`.

- already_resolved: 166
- alias_to_existing: 90
- create_new_skill: 78
- ignore: 35

## Top 50 approved decisions

| raw | count | decision | target | category | reason |
|---|---:|---|---|---|---|
| Agile Methodologies | 54 | alias_to_existing | Agile | methodology | methodology variant |
| Analyse technique | 27 | alias_to_existing | Software Analysis | backend | technical analysis in software context |
| Google Cloud Platform (GCP) | 27 | alias_to_existing | Google Cloud | cloud | GCP alias |
| Intégration continue | 27 | alias_to_existing | CI/CD | devops | French continuous integration |
| Complex Software Solutions Development | 19 | alias_to_existing | Software Development | backend | broad software development wording |
| Modern Application Architectures | 19 | alias_to_existing | Software Architecture | backend | architecture wording |
| Agile Scrum | 18 | alias_to_existing | Scrum | methodology | scrum/agile synonym |
| Cloud Functions | 18 | alias_to_existing | Google Cloud | cloud | GCP service; current taxonomy has Google Cloud |
| Correction d'anomalies | 18 | alias_to_existing | Debugging | tools | bug fixing/debugging |
| Logging | 18 | alias_to_existing | Monitoring | devops | logging observability |
| Maintenance applicative | 18 | alias_to_existing | Software Deployment | devops | application maintenance is lifecycle/deployment support |
| Monitoring Tools | 18 | alias_to_existing | Monitoring | devops | monitoring alias |
| Network Administration | 18 | alias_to_existing | System and Network Administration | security | network admin maps to system/network admin |
| Network Management | 18 | alias_to_existing | System and Network Administration | security | network management maps to system/network admin |
| Routage | 18 | alias_to_existing | System and Network Administration | security | routing/network admin |
| System Administration | 18 | alias_to_existing | System and Network Administration | security | system admin maps to existing canonical |
| Analyse de vulnérabilités sur systèmes embarqués | 10 | alias_to_existing | Vulnerability Management | security | vulnerability analysis |
| Analyse des risques | 10 | alias_to_existing | Risk Analysis | security | risk analysis |
| CDM framework | 10 | alias_to_existing | Cybersecurity | security | security framework |
| CIS framework | 10 | alias_to_existing | Cybersecurity | security | security framework |
| Cybersécurité offensive | 10 | alias_to_existing | Penetration Testing | security | offensive cybersecurity |
| Firmwares | 10 | alias_to_existing | Embedded Systems | other | firmware plural |
| Intelligence artificielle | 10 | alias_to_existing | Artificial Intelligence | data_ai | French AI |
| NIST framework | 10 | alias_to_existing | Cybersecurity | security | security framework |
| SAP FI/CO | 10 | alias_to_existing | SAP ERP | tools | SAP module |
| SAP Integration Suite (CPI) | 10 | alias_to_existing | SAP ERP | tools | SAP integration |
| SAP PP/QM | 10 | alias_to_existing | SAP ERP | tools | SAP module |
| SAP SD/MM | 10 | alias_to_existing | SAP ERP | tools | SAP module |
| Systèmes numériques | 10 | alias_to_existing | Embedded Systems | other | digital systems context |
| Sécurisation de systèmes embarqués | 10 | alias_to_existing | Cybersecurity | security | embedded cybersecurity |
| .Net Core 3.1 | 9 | alias_to_existing | .NET Core | backend | .NET version |
| AI/ML/LLM | 9 | alias_to_existing | Artificial Intelligence | data_ai | AI umbrella |
| API Gateway | 9 | alias_to_existing | API | backend | API infrastructure wording |
| API Integration | 9 | alias_to_existing | API | backend | API integration wording |
| API SOAP | 9 | alias_to_existing | SOAP | backend | SOAP protocol |
| API architecture | 9 | alias_to_existing | API | backend | API architecture wording |
| APM Instana | 9 | alias_to_existing | Monitoring | devops | APM/monitoring tool |
| AWS Certification | 9 | alias_to_existing | AWS | cloud | AWS certification wording |
| AWS ECS | 9 | alias_to_existing | AWS | cloud | AWS service |
| Agile Framework | 9 | alias_to_existing | Agile | methodology | agile wording |
| Analyse d'incidents de sécurité | 9 | alias_to_existing | SIEM | security | security incident analysis usually SIEM/SOC |
| Analyse de flux réseau | 9 | alias_to_existing | Network Security | security | network flow analysis |
| Analyse de journaux d'événements | 9 | alias_to_existing | SIEM | security | event log analysis |
| Analytics Engineering | 9 | alias_to_existing | Data Engineering | data_ai | data engineering role specialty |
| Angular 17 | 9 | alias_to_existing | Angular | frontend | Angular version |
| Angular 2 | 9 | alias_to_existing | Angular | frontend | Angular version |
| Ansible Automation Platform V2 | 9 | alias_to_existing | Ansible | devops | Ansible product name |
| Application Development | 9 | alias_to_existing | Software Development | backend | application development synonym |
| Architecture applicative | 9 | alias_to_existing | Software Architecture | backend | application architecture |
| Architectures applicatives | 9 | alias_to_existing | Software Architecture | backend | application architecture |

## Do not implement automatically
Rows with `keep_pending` are intentionally not approved. They may be useful later, but need context or domain review.

## Important implementation notes
- `already_resolved` rows should not create new seed data. They should be marked resolved/closed by a reconciliation command if the app has such statuses.
- `alias_to_existing` rows should add `SkillAlias` entries targeting an existing canonical `Skill`.
- `create_new_skill` rows should add a canonical `Skill`; if raw text differs, also add it as an alias.
- `ignore` rows should become permanent ignore rules so they do not reappear as pending unmatched candidates.
- Never bulk-create all unmatched candidates.
