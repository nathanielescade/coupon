from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def json_script(value, element_id):
    """
    Output a value as JSON script, wrapped in a <script> tag.
    """
    if not value:
        return ''
    json_str = json.dumps(value, indent=2)
    return mark_safe(
        f'<script id="{element_id}" type="application/json">{json_str}</script>'
    )