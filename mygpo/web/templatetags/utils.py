from django import template
from django.utils.safestring import mark_safe

from mygpo.web.utils import get_page_list, license_info, hours_to_str


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
def smartwidthratio(val, min_val, max_val, upper, lower):
    if max_val == 0:
        return 0
    return max(lower, (float(val-min_val) / max_val * upper))

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
    return mark_safe(_format_time(time))


@register.filter
def is_tuple(obj):
    return isinstance(obj, tuple)

@register.filter
def is_list(obj):
    return isinstance(obj, list)

@register.filter
def markdown(txt):
    import markdown2
    html = markdown2.markdown(txt)
    return mark_safe(html)


@register.filter
def nbsp(s):
    """ collapses multiple whitespaces and replaces them with &nbsp; """
    import re
    s = re.sub("\s+", "&nbsp;", s)
    return mark_safe(s)


@register.filter
def license_name(license_url):
    """ returns a "pretty" license name for a license URL """

    info = license_info(license_url)

    if info.name:
        return '%s %s' % (info.name, info.version or '')

    return info.url


@register.filter
def urlquote(s):
    """ makes urllib.quote_plus available as a template filter """
    import urllib
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return mark_safe(urllib.quote_plus(s))


hours_to_str = register.filter(hours_to_str)
