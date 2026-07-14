from django import template

from apps.jobs.services.presentation import JobPresentationService

register = template.Library()


@register.filter
def card_skill_chips(job):
    return JobPresentationService.get_card_skill_chips(job)


@register.filter
def canonical_job_skills(job):
    return JobPresentationService.get_user_facing_skill_entries(job)


@register.filter
def recommendation_job_skills(recommendation):
    return JobPresentationService.get_subject_skill_entries(recommendation)


@register.filter
def match_job_skills(match):
    return JobPresentationService.get_subject_skill_entries(match)


@register.filter
def canonical_strong_skills(subject):
    return JobPresentationService.get_strong_skill_entries(subject)


@register.filter
def canonical_missing_required_skills(subject):
    return JobPresentationService.get_missing_required_skill_entries(subject)


@register.filter
def canonical_missing_optional_skills(subject):
    return JobPresentationService.get_missing_optional_skill_entries(subject)


@register.filter
def canonical_subject_skills(subject):
    return JobPresentationService.get_subject_skill_entries(subject)


@register.filter
def user_risk_flags(subject):
    from apps.matching.services.presentation import MatchPresentationService

    return MatchPresentationService.get_user_facing_risk_labels(subject)


@register.filter
def user_match_actions(match):
    from apps.matching.services.presentation import MatchPresentationService

    return MatchPresentationService.get_user_facing_actions(match)


@register.filter
def user_recommendation_reason(recommendation):
    from apps.matching.services.presentation import MatchPresentationService

    return MatchPresentationService.get_user_facing_recommendation_reason(recommendation)

@register.filter
def is_valid_badge(value):
    return JobPresentationService.is_valid_badge_value(value)

@register.filter
def job_badges(job):
    return JobPresentationService.get_deduplicated_badges(job)

@register.filter
def is_matchable(job):
    from apps.jobs.services.eligibility import JobEligibilityService
    return JobEligibilityService.is_matchable(job)

@register.filter
def is_publicly_visible(job):
    from apps.jobs.services.eligibility import JobEligibilityService
    return JobEligibilityService.is_publicly_visible(job)

@register.filter
def public_eligibility_reason(job):
    return JobPresentationService.get_safe_public_eligibility_reason(job)

@register.filter
def is_pending_analysis(job):
    from apps.jobs.services.eligibility import JobEligibilityService, PublicJobState
    return JobEligibilityService.classify_public_state(job) == PublicJobState.PUBLIC_LIMITED_PENDING_ANALYSIS


@register.filter
def skill_color(skill_name):
    s = (skill_name or "").lower()
    if any(k in s for k in ("js", "javascript", "ecma")): return "js"
    if any(k in s for k in ("typescript", "ts", "type script")): return "ts"
    if "react" in s or "next" in s: return "react"
    if any(k in s for k in ("node", "nodejs", "node.js", "express")): return "node"
    if any(k in s for k in ("python", "django", "flask", "rest", "api", "graphql", "fastapi")): return "api"
    if any(k in s for k in ("nest", "nestjs")): return "nest"
    if any(k in s for k in ("ai", "ml", "machine learning", "deep learning", "data science", "nlp", "tensorflow", "pytorch")): return "ai"
    if any(k in s for k in ("git", "gitlab", "github", "version control")): return "git"
    if any(k in s for k in ("agile", "scrum", "kanban")): return "agile"
    if any(k in s for k in ("erp", "sap", "crm", "salesforce")): return "erp"
    if any(k in s for k in ("docker", "kubernetes", "k8s", "devops", "ci/cd", "jenkins")): return "git"
    if any(k in s for k in ("sql", "postgresql", "mysql", "mongodb", "database", "db")): return "api"
    if any(k in s for k in ("cloud", "aws", "azure", "gcp")): return "ai"
    if any(k in s for k in ("html", "css", "sass", "tailwind", "bootstrap", "frontend")): return "react"
    if any(k in s for k in ("java", "spring", "kotlin", "android")): return "node"
    if any(k in s for k in ("c#", "dotnet", ".net", "csharp", "unity")): return "ts"
    if any(k in s for k in ("php", "laravel", "symfony", "wordpress")): return "js"
    if any(k in s for k in ("go", "golang", "rust", "cpp", "c++")): return "nest"
    return "api"

@register.filter
def score_bar_class(score):
    if score >= 80: return "good"
    if score >= 65: return "brand"
    if score >= 50: return "warn"
    return "bad"
