from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

register = template.Library()

@register.filter
def lookup(dic, key):
    return mark_safe(dic.get(key, ''))

@register.filter
def lookup_list(dict, keys):
    for key in keys:
        if key in dict:
            yield dict[k]

