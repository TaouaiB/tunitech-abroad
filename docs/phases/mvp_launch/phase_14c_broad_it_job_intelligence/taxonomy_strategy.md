# Broad IT Taxonomy Strategy

## Goal

Support IT opportunities broadly, not only software developer titles.

## Mandatory mapping

The classification service, skill extraction service, recommendation service, and match UI must all obey:

```text
docs/phases/phase_14c_broad_it_job_intelligence/confidence_mapping.md
```

Do not invent another mapping in implementation or tests.

## Job family labels

Use stable internal keys and French display labels.

```python
software_development = "Développement logiciel"
web_mobile = "Web / Mobile"
data_ai_bi = "Data / IA / BI"
devops_cloud_sre = "DevOps / Cloud / SRE"
cybersecurity = "Cybersécurité"
qa_testing = "QA / Test"
systems_network = "Systèmes / Réseaux"
database = "Base de données / DBA"
erp_crm = "ERP / CRM"
it_support = "Support IT"
it_project_product_analysis = "Projet / Produit / Analyse IT"
it_training_apprenticeship = "Formation / Alternance IT"
low_confidence_it = "IT faible confiance"
non_it = "Non IT"
unknown = "Inconnu"
```

Do not create separate `it_project_product` and `business_analysis` keys in this phase. They are intentionally collapsed into `it_project_product_analysis` because the current MVP does not need separate scoring logic for them.

## Classification input signals

Use combined evidence from:

- title / `intitule`
- description
- ROME code/libelle
- appellation libelle
- competences labels and exigence
- formations domain
- secteur activité
- contract/alternance fields: `natureContrat`, `alternance`, `typeContratLibelle`
- experience metadata: `experienceLibelle`, `experienceExige` for level/scoring support, not as primary IT-family proof
- language metadata: `langues[]` for language scoring/display support, not as primary IT-family proof

## Role family examples

### Software development

Signals:

```text
software engineer, développeur logiciel, développeur d'application, Java, C#, .NET, PHP, Python, backend, API, architecture logicielle, application métier
```

### Web / mobile

Signals:

```text
full stack, frontend, backend web, mobile, React, Angular, Vue, Flutter, Swift, Kotlin, Node.js, TypeScript, HTML, CSS, REST APIs, GraphQL
```

### Data / AI / BI

Signals:

```text
Data scientist, data analyst, data engineer, BI, Power BI, Tableau, Python, pandas, scikit-learn, machine learning, SQL, ETL, reporting, Crystal Reports, MyReport
```

### DevOps / Cloud / SRE

Signals:

```text
DevOps, cloud, SRE, CI/CD, Docker, Kubernetes, Terraform, AWS, Azure, GCP, OVHcloud, Linux, Bash, GitLab CI, monitoring, infrastructure as code
```

### Cybersecurity

Signals:

```text
cybersécurité, sécurité des systèmes d'information, SOC, pentest, IAM, vulnerability, audit sécurité, ISO 27001, durcissement, sécurité applicative
```

### QA / testing

Signals:

```text
QA, test automation, tests unitaires, tests d'intégration, Cypress, Selenium, Playwright, Jest, qualité logiciel, recette technique
```

### Systems / network / infrastructure

Signals:

```text
administrateur système, réseau, infrastructure, Windows Server, Linux, Active Directory, VMware, OVH, supervision, support N2/N3, serveurs, sauvegardes
```

### Database / DBA

Signals:

```text
DBA, base de données, SQL Server, PostgreSQL, MySQL, MariaDB, Oracle, DB2, PL/SQL, requêtes SQL, performance des requêtes, reporting data
```

### ERP / CRM

Signals:

```text
Salesforce, Apex, CRM, ERP, Sage X3, PeopleSoft, SAP, Odoo, Dynamics, PeopleCode, SQR, Integration Broker, SQL, GraphQL, API, ETL
```

### IT support

Positive IT support signals:

```text
support informatique, helpdesk, support N1/N2/N3, assistance technique, poste de travail, incidents, tickets, réseau, Active Directory, Windows, Linux, matériel informatique, déploiement logiciel
```

Negative/non-IT support examples:

```text
support client commercial, conseiller clientèle assurance, support administratif, service client vente, relation client non technique
```

If support wording appears without technical context, classify as `non_it` or `low_confidence_it` with `unavailable` match confidence.

### IT project / product / analysis

Use `it_project_product_analysis` for clearly technical/SI context.

Positive signals:

```text
chef de projet IT, chef de projet SI, product owner logiciel, product owner digital, business analyst SI, analyste fonctionnel IT, AMOA SI, MOA systèmes d'information, cahier des charges logiciel, spécifications fonctionnelles, ERP/CRM project, data product
```

Negative/non-IT examples:

```text
chef de projet commercial, chargé de projet événementiel, product owner marketing without tech/SI, business analyst finance without IT/SI/product system context, AMOA métier with no software/SI terms
```

### IT training / apprenticeship

Signals:

```text
alternance développeur, contrat apprentissage IT, stage développeur, stage PFE, apprentissage cybersécurité, alternance data, alternance support informatique, préparation Licence/Master informatique, Bac+2/Bac+3/Bac+5 informatique with technical duties
```

Use `natureContrat`, `alternance`, `typeContratLibelle`, description, and formations domain. Apprenticeship/training must still have IT technical context; a commercial apprenticeship is non-IT.

## Generic France Travail labels

These are useful as weak domain signals, not canonical stack skills:

```text
Application web
Concevoir une application web
Concevoir et développer une solution digitale
Développer un logiciel, un système d'informations, une application
Analyser, exploiter, structurer des données
Recueillir et analyser les besoins client
Coder des données
Tester un logiciel
Collaborer avec des équipes multidisciplinaires
Optimiser les processus de qualité pour assurer la fiabilité des logiciels
```

Do not show these as “required stack” unless no better data exists. If no better data exists, label them as generic job signals and set `skill_signal_quality=generic_only`, not `strong`.
