from django import template
from datetime import time

register = template.Library()

@register.filter
def sec_to_time(sec):
    s = int(sec)
    return time(s / 60 / 60, (s / 60) % 60, s % 60)

