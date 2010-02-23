from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
import hashlib

register = template.Library()

@register.filter
def subtract(value, sub):
    return value - sub


