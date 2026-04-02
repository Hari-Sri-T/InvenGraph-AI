"""Custom template filters for AI-First Logistics Management System."""

from django import template
import json

register = template.Library()


@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter."""
    if not value:
        return []
    return value.split(delimiter)


@register.filter
def get_item(list_obj, index):
    """Get item from list by index."""
    try:
        return list_obj[int(index)]
    except (IndexError, ValueError, TypeError):
        return ''


@register.filter
def pprint(value):
    """Pretty print JSON data."""
    try:
        if isinstance(value, str):
            value = json.loads(value)
        return json.dumps(value, indent=2)
    except (json.JSONDecodeError, TypeError):
        return str(value)
