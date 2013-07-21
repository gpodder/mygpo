import os.path

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.storage import staticfiles_storage

from mygpo.api.constants import DEVICE_TYPES
from mygpo.web.views.device import show


_ = ugettext
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
def device_icon(device):

    ua_str = (device.user_agent or '').lower()

    # TODO: better client detection
    if 'gpodder' in ua_str:
        icon = 'gpodder.png'
        caption = 'gPodder'
    elif 'amarok' in ua_str:
        icon = 'amarok.png'
        caption = 'Amarok'
    elif 'podax' in ua_str:
        icon = 'podax.png'
        caption = 'Podax'

    else:
        device_type = device.type
        icon = DEVICE_TYPE_ICONS.get(device_type, None)
        caption = DEVICE_TYPES_DICT.get(device_type, None)


    if icon is not None and caption is not None:
        caption = ugettext(caption)
        html = '<img src="%(icon)s" alt="%(caption)s" class="device_icon"/>' \
            % dict(icon=staticfiles_storage.url(os.path.join('clients', icon)),
                   caption=caption)
        return mark_safe(html)

    return ''


@register.filter
def target_uid(devices):
    if isinstance(devices, list):
        return devices[0].uid
    else:
        return devices.uid


@register.filter
def device_list(devices):
    links = map(device_link, devices)
    return mark_safe(''.join(links))

def device_link(device):
    return u'<a href="{link}" title="{name}">{icon}</a>'.format(
            link = reverse(show, args=[device.uid]),
            name = device.name,
            icon = device_icon(device),
        )
