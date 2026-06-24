# Classification Hardening Rules

## Positive IT override signals

These should strongly protect a job from being classified as non-IT:

Titles:
- Data Engineer
- Data Analyst, BI Developer, Analytics Engineer
- DevOps, SRE, Cloud Engineer
- Tech Lead
- Software Engineer, Ingénieur Logiciel
- Développeur / Developer / Fullstack / Backend / Frontend
- Java, Angular, .NET, C#, Python, SQL, Scala
- Cybersecurity Consultant when security delivery/audit/risk evidence exists
- System/Network Administrator
- IT Support / Technicien Informatique
- QA / Test Engineer
- Embedded Software / Informatique industrielle

Description evidence:
- develop software, maintain applications, backend/frontend
- ETL/ELT, pipelines, data warehouse, dbt, Snowflake, BigQuery
- cloud platforms such as GCP, AWS, Azure
- CI/CD, Docker, Kubernetes
- audits/security risk/GRC/ISO/NIS2/DORA/EBIOS/RGPD when job is cyber consultant
- systems/network operations, LAN/WAN, VPN, firewall

## Negative exclusion signals

Exclude only when role context is clearly non-technical:

Commercial/sales:
- SDR, BDR
- business developer
- chargé d'affaires
- développement commercial
- prospection
- portefeuille clients/prospects
- CRM as sales CRM
- account executive / sales pipeline

Franchise/business network:
- réseau de franchise
- franchisés
- points de vente
- animer un réseau commercial
- politique commerciale
- contrat de partenariat

Education/outreach:
- médiateur scientifique
- pédagogie
- orientation
- promotion de la filière
- grand public
- ateliers de découverte
- salons/forums/séminaires when main role is outreach

Business consulting:
- transformation digitale
- stratégie
- business model / business plan
- conduite du changement
- performance commerciale / organisation
- industrial excellence without technical implementation

## Conflict rule

If strong positive IT evidence and negative business words both exist:
- do not exclude immediately
- classify as IT or admin_review depending strength
- prefer materialized skills + technical title over generic negative words

Example:
`Data Engineer GCP` mentions clients/sectors, but remains IT.

Example:
`Tech Lead / DevOps` mentions consulting/client context, but remains IT.

Example:
`SDR/BDR Cybersécurité` mentions cybersecurity, but remains commercial and excluded.
