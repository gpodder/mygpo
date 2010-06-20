from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from mygpo.web.utils import get_page_list

register = template.Library()

@register.filter
def lookup(dic, key):
    return mark_safe(dic.get(key, ''))

@register.filter
def lookup_list(dict, keys):
    for key in keys:
        if key in dict:
            yield dict[key]


@register.simple_tag
def smartwidthratio(val, max_val, upper, lower):
    return max(lower, (float(val) / max_val * upper))

@register.filter
def page_list(cur, start, total, show_max):
    return get_page_list(start, total, cur, show_max)

