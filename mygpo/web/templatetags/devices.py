from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.core.urlresolvers import reverse

_ = ugettext

from mygpo.api.models import DEVICE_TYPES
from mygpo.web.views.device import show

register = template.Library()

# Create a dictionary of device_type -> caption mappings
DEVICE_TYPES_DICT = dict(DEVICE_TYPES)

# This dictionary maps device types to their icon files
DEVICE_TYPE_ICONS = {
        'desktop': 'computer.png',
        'laptop': 'stock_notebook.png',
        'mobile': 'stock_cell-phone.png',
        'server': 'server.png',
        'other': 'audio-x-generic.png',
}

@register.filter
def device_type(device):
    return DEVICE_TYPES_DICT.get(device.type, _('Unknown'))

@register.filter
def device_icon(device, size=16):
    icon = DEVICE_TYPE_ICONS.get(device.type, None)
    caption = DEVICE_TYPES_DICT.get(device.type, None)

    if icon is not None and caption is not None:
        caption = ugettext(caption)
        html = ('<img src="/media/%(size)dx%(size)d/%(icon)s" '+
                'alt="%(caption)s" class="device_icon"/>') % locals()
        return mark_safe(html)

    return ''

@register.filter
def device_list(devices):
    return mark_safe('<br/>'.join([ '<a href="%s">%s&nbsp;%s</a>' % (reverse(show, args=[d.id]), device_icon(d), d.name.replace(' ', '&nbsp;')) for d in devices]))

