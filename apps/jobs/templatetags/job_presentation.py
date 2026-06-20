from django import template

from apps.jobs.services.presentation import JobPresentationService

register = template.Library()


@register.filter
def card_skill_chips(job):
    return JobPresentationService.get_card_skill_chips(job)

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
    from apps.jobs.services.eligibility import JobEligibilityService
    return JobEligibilityService.reason(job)

@register.filter
def is_pending_analysis(job):
    from apps.jobs.services.eligibility import JobEligibilityService, PublicJobState
    return JobEligibilityService.classify_public_state(job) == PublicJobState.PUBLIC_LIMITED_PENDING_ANALYSIS
