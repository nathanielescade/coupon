from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def is_expiring_soon(value):
    if not value:
        return False
    now = timezone.now()
    soon = now + timezone.timedelta(days=7)
    return now <= value <= soon

@register.filter
def time_until(value):
    if not value:
        return ""
    
    now = timezone.now()
    if value < now:
        return "expired"
    
    diff = value - now
    
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} day{'s' if days != 1 else ''}"
    elif hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        return "less than a minute"

@register.filter
def countdown_from_3_days(value):
    if not value:
        return ""
    
    now = timezone.now()
    if value < now:
        return "expired"
    
    diff = value - now
    
    # Only show countdown if within 3 days
    if diff.days > 3:
        return ""
    
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days} day{'s' if days != 1 else ''}"
    elif hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        return "less than a minute"