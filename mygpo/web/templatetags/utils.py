import urllib.parse

from django import template
from django.utils.safestring import mark_safe

from mygpo.web.utils import get_page_list, license_info, hours_to_str
from mygpo.utils import edit_link


register = template.Library()

@register.filter
@mark_safe
def lookup(dic, key):
    return dic.get(key, '')

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
    return [key for key, val in dic.items() if val]


@register.filter
def append(l, item):
    return l + [item]

@register.filter
def remove(l, item):
    return [x for x in l if x != item]

@register.filter
@mark_safe
def format_time(time):
    from mygpo.utils import format_time as _format_time
    return _format_time(time)


@register.filter
def is_tuple(obj):
    return isinstance(obj, tuple)


@register.filter
def markdown(txt):
    import markdown2
    return mark_safe(markdown2.markdown(txt, extras={'nofollow': True}))


@register.filter
def nbsp(s):
    """ collapses multiple whitespaces and replaces them with &nbsp; """
    import re
    return mark_safe(re.sub("\s+", "&nbsp;", s))


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
    if isinstance(s, str):
        s = s.encode('utf-8')
    return mark_safe(urllib.parse.quote_plus(s))


hours_to_str = register.filter(hours_to_str)

@register.simple_tag
def protocol(request):
    return 'http{s}://'.format(s='s' if request.is_secure() else '')


edit_link = register.simple_tag(edit_link)
