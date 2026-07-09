# Phase 15B — Alias Seed Plan

Gemini must convert the successful local alias experiment into permanent seed data inside `apps/skills/services/seed.py`.

Do not paste the shell script. Integrate the alias/canonical data into the existing taxonomy seed architecture.

## Batch 1 — High-value IT/security/dev/data aliases

These aliases were proven locally to improve coverage from 75.84% to 87.08%.

```python
PHASE_15B_ALIAS_CANDIDATES_BATCH_1 = [
    # Security / cyber
    ("Cybersecurity", "Cybersécurité", "security"),
    ("Cybersecurity", "Cybersecurité", "security"),
    ("Cybersecurity", "Sécurité informatique", "security"),
    ("Cybersecurity", "Security", "security"),
    ("Cybersecurity", "Fondamentaux de sécurité", "security"),
    ("Cybersecurity", "Frameworks de sécurité", "security"),
    ("Cybersecurity", "Architecture de sécurité", "security"),
    ("Cybersecurity", "Sécurité des Systèmes d'Information", "security"),
    ("Cybersecurity", "Sécurité système", "security"),
    ("Network Security", "Sécurité réseau", "security"),
    ("Network Security", "Réseau sécurisé", "security"),
    ("Network Security", "Réseaux", "security"),
    ("Network Security", "Réseau", "security"),
    ("Network Security", "Networking", "security"),
    ("Application Security", "Sécurité des applications", "security"),
    ("Database Security", "Sécurité des bases de données", "security"),
    ("Cloud Security", "Sécurité cloud", "security"),
    ("Vulnerability Management", "Gestion des vulnérabilités", "security"),
    ("Vulnerability Management", "Analyse de vulnérabilités", "security"),
    ("Risk Analysis", "Analyse de risques", "security"),
    ("Risk Analysis", "Évaluation des risques", "security"),
    ("Cryptography", "Cryptographie", "security"),
    ("GRC", "Gouvernance, Risques et Conformité (GRC)", "security"),
    ("GRC", "GRC", "security"),
    ("ISO 27001", "ISO 27001", "security"),
    ("ISO 27005", "ISO 27005", "security"),
    ("NIS2", "NIS2", "security"),
    ("IAM", "IAM", "security"),
    ("SIEM", "SIEM", "security"),
    ("Entra ID", "Entra ID", "security"),
    ("Active Directory", "Active Directory", "security"),
    # Systems / network / support
    ("Windows", "Windows", "tools"),
    ("PowerShell", "PowerShell", "tools"),
    ("Microsoft 365", "Microsoft 365", "tools"),
    ("Office 365", "Office 365", "tools"),
    ("TCP/IP", "TCP/IP", "security"),
    ("LAN", "LAN", "security"),
    ("WAN", "WAN", "security"),
    ("VLAN", "VLAN", "security"),
    ("VPN", "VPN", "security"),
    ("Firewall", "Firewall", "security"),
    ("Troubleshooting", "Troubleshooting", "tools"),
    ("GLPI", "GLPI", "tools"),
    # DevOps / cloud
    ("DevOps", "DevOps", "devops"),
    ("Cloud", "Cloud", "cloud"),
    ("OpenShift", "OpenShift", "devops"),
    ("Azure DevOps", "Azure DevOps", "devops"),
    ("Infrastructure as Code", "Infrastructure as Code", "devops"),
    ("Argo CD", "ArgoCD", "devops"),
    ("Helm", "Helm", "devops"),
    ("Dynatrace", "Dynatrace", "devops"),
    ("VMware", "VmWare", "devops"),
    ("Monitoring", "Monitoring", "devops"),
    ("Scripting", "Scripting", "devops"),
    # API / software engineering
    ("REST API", "API REST", "backend"),
    ("API", "API", "backend"),
    ("Software Testing", "Tests unitaires", "testing"),
    ("Automated Testing", "Automated Testing", "testing"),
    ("Software Quality", "Software Quality", "testing"),
    ("Design Patterns", "Design Patterns", "backend"),
    ("Object-Oriented Programming", "Programmation Orientée Objet", "programming_language"),
    ("Object-Oriented Programming", "Object-Oriented Programming", "programming_language"),
    ("Debugging", "Debugging", "tools"),
    ("Code Review", "Code review", "methodology"),
    ("UML", "UML", "methodology"),
    # Data / AI
    ("Data Modeling", "Data Modeling", "data_ai"),
    ("Data Engineering", "Data Engineering", "data_ai"),
    ("ETL", "ETL", "data_ai"),
    ("dbt", "dbt", "data_ai"),
    ("NoSQL", "NoSQL", "database"),
    ("Azure Data Factory", "Azure Data Factory", "data_ai"),
    ("PySpark", "PySpark", "data_ai"),
    ("Prompt Engineering", "Prompt Engineering", "data_ai"),
    ("RAG", "RAG (Retrieval Augmented Generation)", "data_ai"),
    ("RAG", "RAG (Retrieval-Augmented Generation)", "data_ai"),
    ("Azure OpenAI", "Azure OpenAI", "data_ai"),
    ("Copilot Studio", "Copilot Studio", "data_ai"),
    ("Power Automate", "Power Automate", "tools"),
    ("Power Platform", "Power Platform", "tools"),
    # ERP / legacy / SAP
    ("ERP", "ERP", "tools"),
    ("ABAP", "ABAP", "programming_language"),
    ("SAP ECC6", "SAP ECC6", "tools"),
    ("SAP S/4HANA", "SAP S/4HANA", "tools"),
    ("SAP Fiori", "SAP Fiori", "frontend"),
    ("SAP UI5", "SAP UI5", "frontend"),
    ("COBOL", "COBOL", "programming_language"),
    ("Mainframe", "Mainframe", "tools"),
    ("JCL", "JCL", "programming_language"),
    ("CICS", "CICS", "tools"),
    ("IBM Mainframe", "IBM Mainframe", "tools"),
    # Embedded / industrial
    ("Embedded Systems", "systèmes embarqués", "other"),
    ("Embedded Linux", "Linux embarqué", "other"),
    ("RTOS", "RTOS", "other"),
    ("Yocto Project", "Yocto Project", "other"),
    ("Buildroot", "Buildroot", "other"),
    ("SPI", "SPI", "other"),
    ("I2C", "I2C", "other"),
    ("UDP", "UDP", "other"),
    ("Ethernet", "Ethernet", "other"),
]
```

## Batch 2 — Additional aliases proven locally

These aliases were proven locally to push coverage from 87.08% to 91.57%.

```python
PHASE_15B_ALIAS_CANDIDATES_BATCH_2 = [
    # Software delivery
    ("Software Development", "développement logiciel", "backend"),
    ("Software Development", "Développer un logiciel, un système d'informations, une application", "backend"),
    ("Software Analysis", "analyse et conception", "backend"),
    ("Software Architecture", "Conception d'architecture logicielle", "backend"),
    ("Software Architecture", "Conception d'architecture système", "backend"),
    ("Software Testing", "tests et qualité", "testing"),
    ("Software Deployment", "déploiement et maintenance", "devops"),
    ("Software Deployment", "Optimisation de développement", "devops"),
    ("Technical Documentation", "Documentation technique", "methodology"),
    ("Technical Documentation", "Documentation de support", "methodology"),
    ("Requirements Analysis", "Analyse des besoins", "methodology"),
    ("Technical Watch", "Veille technologique", "methodology"),
    ("Specifications Writing", "Rédaction de cahier des charges", "methodology"),
    ("Digital Project Management", "Gestion de projet numérique", "methodology"),
    ("Technology Selection", "Sélection de technologies", "methodology"),
    # Data / automation
    ("Data Modeling", "Modélisation de données", "data_ai"),
    ("Data Warehouse", "Architecture d'entrepôts de données décisionnelles", "data_ai"),
    ("RPA", "RPA", "tools"),
    ("Automation", "Surveillance des systèmes automatisés", "tools"),
    ("Blockchain", "Blockchain", "tools"),
    # IT support / technician
    ("IT Support", "Assistance technique", "tools"),
    ("IT Support", "Support aux utilisateurs", "tools"),
    ("System and Network Administration", "Systèmes et Réseaux", "security"),
    ("IT Asset Management", "Gestion de parc informatique", "tools"),
    ("IT Asset Management", "Gestion des consommables", "tools"),
    ("Hardware Maintenance", "Maintenance matériel", "tools"),
    ("Hardware Troubleshooting", "Diagnostic de pannes matérielles et logicielles", "tools"),
    ("Hardware Repair", "Réparation de composants", "tools"),
    ("Operating System Installation", "Installation et configuration de systèmes d'exploitation", "tools"),
    ("Software Installation", "Installation et configuration de logiciels", "tools"),
    ("Workstation Deployment", "Préparation de postes informatiques", "tools"),
    ("IT Deployment", "Déploiement informatique", "devops"),
    ("IT Inventory Management", "Gestion des stocks de matériel informatique", "tools"),
    ("Intervention Tracking", "Suivi des interventions", "tools"),
    # Security ops / audit / recovery
    ("Security Planning", "Security Plan Development", "security"),
    ("Security Implementation", "Security Solution Implementation", "security"),
    ("Security Audit", "Organizational Audits", "security"),
    ("Security Audit", "Technical Audits", "security"),
    ("Disaster Recovery", "Disaster Recovery Plan (DRP) Definition", "security"),
    ("Disaster Recovery", "Disaster Recovery Plan (DRP) Deployment", "security"),
    ("Disaster Recovery", "Disaster Recovery Plan (PRA)", "security"),
    # Rail / safety software
    ("ERTMS", "ERTMS", "testing"),
    ("EN 50128", "EN 50128", "testing"),
    ("SIL4", "SIL4", "testing"),
    # Data center / infrastructure-adjacent
    ("Data Center Operations", "Data Center Operations", "devops"),
    ("Root Cause Analysis", "Root Cause Analysis (RCA)", "methodology"),
    ("Root Cause Analysis", "Analyse des causes racines", "methodology"),
    ("SLA Management", "SLA Management", "methodology"),
    ("SOP Development", "Standard Operating Procedure (SOP) Development", "methodology"),
    ("Safety Procedures", "Safety Procedures", "methodology"),
    ("CMMS", "CMMS", "tools"),
    ("Preventive Maintenance", "Maintenance préventive", "tools"),
    ("Corrective Maintenance", "Maintenance corrective", "tools"),
    ("Diagnostic", "Diagnostic", "tools"),
    ("Troubleshooting", "Dépannage", "tools"),
]
```

## Strict review notes

Gemini and Codex must review this list against existing taxonomy. If an alias already exists, seed must be idempotent. If a canonical skill already exists under a slightly different name, prefer aliasing to the existing canonical skill instead of creating duplicates.

Do not add every pending unmatched candidate.
