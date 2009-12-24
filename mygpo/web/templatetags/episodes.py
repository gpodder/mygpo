from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

register = template.Library()

@register.filter
def episode_status_icon(action):
    if not action or not action.action:
        s = '<img src="/media/16x16/emblem-new.png" alt="new" title="%s" />' % _('This episode has not yet been played')

    else:
        date_string   = (_(' on %s') % (action.timestamp)) if action.timestamp else ''
        device_string = (_(' on %s') % (action.device.name)) if action.device else ''

        if action.action == 'new':
            s = '<img src="/media/16x16/emblem-new.png" alt="new" title="%s" />' % (_('This episode has been marked new%s%s') % (date_string, device_string))
        elif action.action == 'download':
            s = '<img src="/media/16x16/folder.png" alt="downloaded" title="%s" />' % (_('This episode has been downloaded%s%s') % (date_string, device_string))
        elif action.action == 'play':
            s = '<img src="/media/16x16/media-playback-start.png" alt="played" title="%s" />' % (_('This episode has been played%s%s') % (date_string, device_string))
        elif action.action == 'delete':
            s = '<img src="/media/16x16/user-trash-full.png" alt="deleted" title="%s"/>' %s (_('This episode has been deleted%s%s') % (date_string, device_string))
        else:
            return action.action #this is not marked safe by intention

    return mark_safe(s)

