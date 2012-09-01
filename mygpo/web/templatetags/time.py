from datetime import time

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django import template


register = template.Library()

@register.filter
def sec_to_time(sec):
    s = int(sec)
    return time(s / 60 / 60, (s / 60) % 60, s % 60)


@register.filter
def format_duration(sec):
    hours = sec / 60 / 60
    minutes = (sec / 60) % 60
    seconds = sec % 60
    return mark_safe(_('{h}h {m}m {s}s').format(h=hours, m=minutes, s=seconds))
