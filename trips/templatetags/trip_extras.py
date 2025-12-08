import json
from django import template

register = template.Library()

@register.filter
def json_load(value):
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return {}

@register.filter
def split(value, arg):
    return value.split(arg)