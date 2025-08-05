from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def is_expiring_soon(value):
    if not value:
        return False
    now = timezone.now()
    soon = now + timezone.timedelta(days=7)
    return now <= value <= soon