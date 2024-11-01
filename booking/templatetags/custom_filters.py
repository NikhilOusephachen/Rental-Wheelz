# myapp/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def int_convert(value):
    return int(value)

@register.filter
def multiply(value, arg):
    """Multiply the value by the arg."""
    try:
        return value * arg
    except (TypeError, ValueError):
        return ''