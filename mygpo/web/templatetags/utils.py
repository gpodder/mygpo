from django import template
from django.utils.safestring import mark_safe
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
    if max_val == 0:
        return 0
    return max(lower, (float(val) / max_val * upper))

@register.filter
def page_list(cur, start, total, show_max):
    return get_page_list(start, total, cur, show_max)


@register.filter
def filter_dict(dic):
    return [key for key, val in dic.iteritems() if val]


@register.filter
def append(l, item):
    return l + [item]

@register.filter
def remove(l, item):
    return [x for x in l if x != item]

@register.filter
def format_time(time):
    from mygpo.utils import format_time as _format_time
    try:
        return mark_safe(_format_time(time))
    except:
        return mark_safe("")
