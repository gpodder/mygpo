from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
import hashlib

register = template.Library()

@register.filter
def vertical_bar(value, max):
    ratio = float(value) / float(max) * 100
    s = '<div class="bar" style="width: %s">%s</div>' % (ratio, value)
    return mark_safe(s)


