BROAD_IT_KEYWORDS = [
    "développeur",
    "ingénieur logiciel",
    "fullstack",
    "backend",
    "frontend",
    "java",
    "python",
    "javascript",
    "typescript",
    "react",
    "angular",
    "node.js",
    "php",
    "django",
    "mobile developer",
    "flutter",
    "kotlin",
    "swift",
    "data analyst",
    "data scientist",
    "data engineer",
    "business intelligence",
    "power bi",
    "devops",
    "sre",
    "cloud",
    "azure",
    "aws",
    "kubernetes",
    "docker",
    "cybersécurité",
    "sécurité informatique",
    "soc",
    "pentest",
    "qa",
    "testeur",
    "test automation",
    "support informatique",
    "technicien informatique",
    "helpdesk",
    "administrateur systèmes",
    "administrateur réseau",
    "réseau informatique",
    "dba",
    "base de données",
    "salesforce",
    "sage x3",
    "erp",
    "crm",
    "business analyst informatique",
    "chef de projet informatique",
    "product owner informatique",
    "amoa informatique",
    "alternance informatique",
    "stage informatique",
    "stage développeur",
    "pfe informatique",
]

# Conservative keyword subset for scheduled (Celery Beat) runs.
# These 8 high-yield keywords cover the main IT job categories without
# overwhelming the France Travail API on a 4-hourly schedule.
SCHEDULED_IT_KEYWORDS = [
    "développeur",
    "ingénieur logiciel",
    "fullstack",
    "data engineer",
    "devops",
    "alternance informatique",
    "stage développeur",
    "cybersécurité",
]


def get_preset_keywords(preset_name: str) -> list[str]:
    """Return keywords for a given preset. Returns empty list if not found."""
    if preset_name == "broad_it":
        return BROAD_IT_KEYWORDS
    return []


def get_scheduled_keywords() -> list[str]:
    """Return the conservative keyword subset for scheduled (Beat) ingestion."""
    return SCHEDULED_IT_KEYWORDS
