from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class JobITClassificationResult:
    family: str
    is_it: bool
    confidence: str  # high | medium | low | excluded
    reasons: List[str]
    negative_reasons: List[str]

class JobITClassificationService:
    @staticmethod
    def classify(payload: dict, description: str, title: str) -> JobITClassificationResult:
        combined_text = f"{title} {description}".lower()
        rome_code = payload.get("romeCode", "")
        rome_libelle = payload.get("romeLibelle", "").lower()
        appellation_libelle = payload.get("appellationlibelle", "").lower()
        
        reasons = []
        negative_reasons = []

        is_it = False
        family = "unknown"
        confidence = "unknown"

        # Check for negative signals first
        negative_signals = [
            "commercial", "photographe", "photographie", "vendeur", "vendeuse",
            "développement commercial", "business development", "retail",
            "conseiller clientèle", "chargé de projet événementiel"
        ]
        import re
        for neg in negative_signals:
            pattern = rf"\b{re.escape(neg)}\b"
            if re.search(pattern, combined_text) or re.search(pattern, appellation_libelle):
                negative_reasons.append("Contains explicit non-IT negative signals")
                return JobITClassificationResult(
                family="non_it",
                is_it=False,
                confidence="excluded",
                reasons=reasons,
                negative_reasons=negative_reasons
            )

        import re
        def has_signals(signals: List[str]) -> bool:
            for sig in signals:
                pattern = rf"\b{re.escape(sig)}\b"
                if re.search(pattern, combined_text) or re.search(pattern, title.lower()) or re.search(pattern, appellation_libelle):
                    return True
            return False

        if has_signals(["data scientist", "data analyst", "data engineer", "bi", "power bi", "tableau", "pandas", "scikit-learn", "machine learning", "sql", "etl", "reporting", "crystal reports", "myreport"]):
            family = "data_ai_bi"
            reasons.append("data_ai_bi signals")
        elif has_signals(["devops", "cloud", "sre", "ci/cd", "docker", "kubernetes", "terraform", "aws", "azure", "gcp", "ovhcloud", "linux", "bash", "gitlab ci", "monitoring", "infrastructure as code"]):
            family = "devops_cloud_sre"
            reasons.append("devops_cloud_sre signals")
        elif has_signals(["cybersécurité", "sécurité des systèmes d'information", "soc", "pentest", "iam", "vulnerability", "audit sécurité", "iso 27001", "durcissement", "sécurité applicative"]):
            family = "cybersecurity"
            reasons.append("cybersecurity signals")
        elif has_signals(["qa", "test automation", "tests unitaires", "tests d'intégration", "cypress", "selenium", "playwright", "jest", "qualité logiciel", "recette technique", "tester un logiciel"]):
            family = "qa_testing"
            reasons.append("qa_testing signals")
        elif has_signals(["administrateur système", "réseau", "infrastructure", "windows server", "active directory", "vmware", "ovh", "supervision", "support n2/n3", "serveurs", "sauvegardes"]):
            family = "systems_network"
            reasons.append("systems_network signals")
        elif has_signals(["as400", "ibm i", "rpg", "cl"]):
            family = "software_development"
            reasons.append("software_development signals")
        elif has_signals(["dba", "base de données", "sql server", "postgresql", "mysql", "mariadb", "oracle", "db2", "pl/sql", "requêtes sql", "performance des requêtes", "reporting data"]):
            family = "database"
            reasons.append("database signals")
        elif has_signals(["salesforce", "apex", "crm", "erp", "sage x3", "peoplesoft", "sap", "odoo", "dynamics", "peoplecode", "sqr", "integration broker"]):
            family = "erp_crm"
            reasons.append("erp_crm signals")
        elif has_signals(["support informatique", "helpdesk", "assistance technique", "poste de travail", "incidents", "tickets"]):
            family = "it_support"
            reasons.append("it_support signals")
        elif has_signals(["chef de projet it", "chef de projet si", "product owner logiciel", "product owner digital", "business analyst si", "analyste fonctionnel it", "amoa si", "moa systèmes d'information", "cahier des charges logiciel", "spécifications fonctionnelles", "erp/crm project", "data product"]):
            family = "it_project_product_analysis"
            reasons.append("it_project_product_analysis signals")
        elif has_signals(["alternance développeur", "contrat apprentissage it", "stage développeur", "stage pfe", "apprentissage cybersécurité", "alternance data", "alternance support informatique", "préparation licence/master informatique", "bac+2", "bac+3", "bac+5 informatique"]):
            # Also check contract fields
            nature_contrat = payload.get("natureContrat", "").upper()
            type_contrat = payload.get("typeContratLibelle", "").upper()
            if "APP" in nature_contrat or "ALTERNANCE" in type_contrat or "STAGE" in type_contrat:
                 family = "it_training_apprenticeship"
                 reasons.append("it_training_apprenticeship signals")
        elif has_signals(["software engineer", "ingénieur logiciel", "ingenieur logiciel", "développeur", "developpeur", "développeuse", "developpeuse", "développeur logiciel", "développeur d'application", "java", "c#", ".net", "php", "python", "backend", "back-end", "api", "architecture logicielle", "application métier", "as400", "ibm i", "rpg", "cl"]):
            family = "software_development"
            reasons.append("software_development signals")
        elif has_signals(["full stack", "full-stack", "frontend", "front-end", "backend web", "mobile", "react", "angular", "vue", "flutter", "swift", "kotlin", "node.js", "typescript", "javascript", "html", "css", "rest api", "rest apis", "graphql", "application web", "prestashop"]):
            family = "web_mobile"
            reasons.append("web_mobile signals")
        else:
            # Fallback to general IT terms
            if has_signals(["informatique", "logiciel", "système d'information"]):
                family = "low_confidence_it"
                reasons.append("low_confidence_it fallback")
            else:
                family = "non_it"
                reasons.append("No IT signals found")

        is_it = family not in ["non_it", "unknown"]
        if is_it:
            if family == "low_confidence_it":
                confidence = "low"
            else:
                confidence = "high"
        else:
            confidence = "excluded"

        return JobITClassificationResult(
            family=family,
            is_it=is_it,
            confidence=confidence,
            reasons=reasons,
            negative_reasons=negative_reasons
        )
