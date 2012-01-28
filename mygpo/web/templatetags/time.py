from datetime import time

from django import template


register = template.Library()

@register.filter
def sec_to_time(sec):
    s = int(sec)
    return time(s / 60 / 60, (s / 60) % 60, s % 60)

