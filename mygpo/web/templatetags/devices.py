from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
import hashlib

register = template.Library()

@register.filter
def device_icon(device,size=16):
    if device.type == 'desktop':
        s = '<img src="/media/%sx%s/computer.png" alt="%s" />' % (size, size, _('Desktop'))
    elif device.type == 'laptop':
        s = '<img src="/media/%sx%s/pda.png" alt="%s" />' % (size, size, _('Laptop'))
    elif device.type == 'mobile':
        s = '<img src="/media/%sx%s/multimedia-player.png" alt="%s" />' % (size, size, _('Mobile'))
    elif device.type == 'server':
        s = '<img src="/media/%sx%s/server.png" alt="%s" />' % (size, size, _('Server'))
    else:
        s = '<img src="/media/%sx%s/audio-x-generic.png" alt="%s" />' % (size, size, _('Other'))

    return mark_safe(s)

@register.filter
def device_list(devices):
    return mark_safe(', '.join([ '<a href="/device/%s" />%s %s</a>' % (d.id, device_icon(d), d.name) for d in devices]))
        
