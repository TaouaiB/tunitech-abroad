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
        title_lower = title.lower()
        rome_code = payload.get("romeCode", "")
        rome_libelle = payload.get("romeLibelle", "").lower()
        appellation_libelle = payload.get("appellationlibelle", "").lower()

        reasons = []
        negative_reasons = []

        is_it = False
        family = "unknown"
        confidence = "unknown"

        import re
        def has_signals(signals: List[str], target: str = None) -> bool:
            if target is None:
                target = combined_text
            for sig in signals:
                pattern = rf"\b{re.escape(sig)}\b"
                if re.search(pattern, target) or re.search(pattern, appellation_libelle) or re.search(pattern, title_lower):
                    return True
            return False

        protected_it_title = has_signals(
            [
                "data engineer",
                "tech lead",
                "devops",
                "fullstack",
                "full stack",
                "java/angular",
                ".net",
                "c#",
                "consultant cybersécurité",
                "consultant cybersecurite",
                "ingénieur développement",
                "ingenieur developpement",
                "ingénieur développeur",
                "ingenieur developpeur",
            ],
            title_lower,
        )

        decisive_non_it_patterns = [
            "médiateur scientifique",
            "mediateur scientifique",
            "grand public",
            "ateliers de découverte",
            "ateliers de decouverte",
            "promouvoir la filière",
            "promouvoir la filiere",
            "réseau de franchise",
            "reseau de franchise",
            "franchisés",
            "franchises",
            "points de vente",
            "animer le réseau",
            "animer le reseau",
            "politique commerciale",
        ]
        for sig in decisive_non_it_patterns:
            pattern = rf"\b{re.escape(sig)}\b"
            if re.search(pattern, combined_text) or re.search(pattern, appellation_libelle):
                if protected_it_title and sig in {"grand public", "ateliers de découverte", "ateliers de decouverte"}:
                    continue
                return JobITClassificationResult(
                    family="non_it",
                    is_it=False,
                    confidence="excluded",
                    reasons=["Decisive non-IT outreach/franchise/commercial pattern"],
                    negative_reasons=[f"Decisive non-IT pattern: {sig}"],
                )

        # Strong negative titles that should immediately exclude
        strong_commercial_titles = [
            "sdr", "bdr", "business developer", "chargé d'affaires", "charge d'affaires",
            "médiateur scientifique", "mediateur scientifique", "animateur réseau", "animateur reseau",
            "développeur réseau de franchise", "developpeur reseau de franchise",
            "vendeur", "vendeuse", "photographe", "photographie"
        ]

        for sig in strong_commercial_titles:
            pattern = rf"\b{re.escape(sig)}\b"
            if re.search(pattern, title_lower) or re.search(pattern, appellation_libelle):
                return JobITClassificationResult(
                    family="non_it",
                    is_it=False,
                    confidence="excluded",
                    reasons=["Strong non-IT title"],
                    negative_reasons=[f"Explicit non-IT role title: {sig}"]
                )

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
        elif has_signals(["administrateur système", "réseau informatique", "infrastructure réseau", "systèmes et réseaux", "windows server", "active directory", "vmware", "ovh", "supervision", "support n2/n3", "serveurs", "sauvegardes"]):
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
        elif has_signals(["software engineer", "ingénieur logiciel", "ingenieur logiciel", "développeur", "developpeur", "développeuse", "developpeuse", "développeur logiciel", "développeur d'application", "java", "c#", ".net", "php", "python", "backend", "back-end", "api", "architecture logicielle", "application métier", "algorithme", "algorithmes", "algorithmique", "optimisation logicielle", "outillage r&d", "outil r&d", "programmation", "logiciel de calcul", "interface graphique"]):
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

        # Generic negative signals
        negative_signals = [
            "commercial", "photographe", "photographie", "vendeur", "vendeuse",
            "développement commercial", "business development", "retail",
            "conseiller clientèle", "chargé de projet événementiel",
            "réseau de franchise", "franchisés", "points de vente", "franchise",
            "pédagogie", "pédagogique", "grand public", "ateliers de découverte",
            "promouvoir la filière", "animer le réseau",
            "réseau commercial", "politique commerciale",
            "transformation digitale", "conduite du changement", "performance commerciale"
        ]

        has_negative = False
        for neg in negative_signals:
            pattern = rf"\b{re.escape(neg)}\b"
            if re.search(pattern, combined_text) or re.search(pattern, appellation_libelle):
                negative_reasons.append(f"Contains negative signal: {neg}")
                has_negative = True

        is_it = family not in ["non_it", "unknown"]

        # Conflict resolution
        if has_negative:
            if family in ["low_confidence_it", "non_it"]:
                is_it = False
                family = "non_it"
                confidence = "excluded"
            else:
                # Strong IT signals exist -> ignore negative signal for confidence
                confidence = "high"
        else:
            if is_it:
                confidence = "low" if family == "low_confidence_it" else "high"
            else:
                confidence = "excluded"

        return JobITClassificationResult(
            family=family,
            is_it=is_it,
            confidence=confidence,
            reasons=reasons,
            negative_reasons=negative_reasons
        )
