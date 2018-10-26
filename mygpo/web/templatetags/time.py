from datetime import time

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django import template


register = template.Library()


@register.filter
def sec_to_time(sec):
    """ Converts seconds to a time object

    >>> t = sec_to_time(1000)
    >>> (t.hour, t.minute, t.second)
    (0, 16, 40)
    """

    s = int(sec)
    hour = int(s / 60 / 60)
    minute = int((s / 60) % 60)
    sec = int(s % 60)
    return time(hour, minute, sec)


@register.filter
@mark_safe
def format_duration(sec):
    """ Converts seconds into a duration string

    >>> format_duration(1000)
    '16m 40s'

    >>> format_duration(10009)
    '2h 46m 49s'
    """
    hours = int(sec / 60 / 60)
    minutes = int((sec / 60) % 60)
    seconds = int(sec % 60)

    if hours:
        return _('{h}h {m}m {s}s').format(h=hours, m=minutes, s=seconds)
    else:
        return _('{m}m {s}s').format(m=minutes, s=seconds)
