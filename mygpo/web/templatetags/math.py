from django import template

register = template.Library()

@register.filter
def subtract(value, sub):
    return value - sub


