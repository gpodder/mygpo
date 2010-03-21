from django import template
from django.utils.translation import ugettext as _
from datetime import time

register = template.Library()

@register.filter
def sec_to_time(sec):
    s = int(sec)
    return time(s / 60 / 60, (s / 60) % 60, s % 60)

