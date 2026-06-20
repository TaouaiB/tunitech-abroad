from django import template

from apps.jobs.services.presentation import JobPresentationService

register = template.Library()


@register.filter
def card_skill_chips(job):
    return JobPresentationService.get_card_skill_chips(job)

@register.filter
def is_valid_badge(value):
    return JobPresentationService.is_valid_badge_value(value)
