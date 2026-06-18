from dataclasses import dataclass

from apps.jobs.models import NormalizedJob
from apps.skills.models import SkillCategory


TECH_CATEGORIES = {
    SkillCategory.PROGRAMMING_LANGUAGE,
    SkillCategory.FRONTEND,
    SkillCategory.BACKEND,
    SkillCategory.DATABASE,
    SkillCategory.DEVOPS,
    SkillCategory.CLOUD,
    SkillCategory.TESTING,
    SkillCategory.DATA_AI,
    SkillCategory.MOBILE,
    SkillCategory.SECURITY,
    SkillCategory.TOOLS,
}

IT_TERMS = {
    "api",
    "backend",
    "back-end",
    "cloud",
    "cyber",
    "data",
    "database",
    "devops",
    "développeur backend",
    "développeur frontend",
    "développeur full stack",
    "développeur informatique",
    "développeur logiciel",
    "développeur web",
    "engineer",
    "frontend",
    "front-end",
    "full stack",
    "informatique",
    "logiciel",
    "mobile developer",
    "programmer",
    "programmeur",
    "qa",
    "security",
    "software",
    "sre",
    "web developer",
}

LOW_RELEVANCE_TERMS = {
    "commercial",
    "photographe",
    "photographie",
    "photo",
    "retail",
    "sales",
    "vente",
    "vendeur",
    "vendeuse",
}

TECH_SKILL_TERMS = {
    "aws",
    "azure",
    "c#",
    "c++",
    "css",
    "django",
    "docker",
    "flutter",
    "go",
    "html",
    "java",
    "javascript",
    "kubernetes",
    "node",
    "node.js",
    "php",
    "postgresql",
    "python",
    "react",
    "sql",
    "typescript",
    "vue",
}


@dataclass(frozen=True)
class JobITRelevanceResult:
    is_relevant: bool
    score: int
    reasons: list[str]
    technical_skill_count: int


class JobITRelevanceService:
    @classmethod
    def assess(cls, job: NormalizedJob) -> JobITRelevanceResult:
        text = f"{job.title or ''} {job.description or ''}".lower()
        reasons: list[str] = []

        technical_skill_count = 0
        for job_skill in job.job_skills.select_related("skill").all():
            if job_skill.skill.category in TECH_CATEGORIES:
                technical_skill_count += 1

        score = min(70, technical_skill_count * 25)
        if technical_skill_count:
            reasons.append("technical_skills")

        raw_skill_text = " ".join(
            str(skill).lower()
            for skill in ((job.required_skills_json or []) + (job.optional_skills_json or []))
            if isinstance(skill, str)
        )
        if any(term in raw_skill_text for term in TECH_SKILL_TERMS):
            score += 50
            reasons.append("technical_skill_json")

        if any(term in text for term in IT_TERMS):
            score += 30
            reasons.append("it_title_or_description")

        has_low_relevance_term = any(term in text for term in LOW_RELEVANCE_TERMS)
        if has_low_relevance_term:
            score -= 45
            reasons.append("non_it_sales_or_photo_signal")

        if "développeur" in text and not technical_skill_count:
            score -= 20
            reasons.append("developer_word_without_technical_signal")

        score = max(0, min(100, score))
        return JobITRelevanceResult(
            is_relevant=score >= 45 and not (has_low_relevance_term and technical_skill_count == 0),
            score=score,
            reasons=reasons,
            technical_skill_count=technical_skill_count,
        )

    @classmethod
    def is_relevant_for_recommendations(cls, job: NormalizedJob) -> bool:
        return cls.assess(job).is_relevant
