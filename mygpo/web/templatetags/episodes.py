from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from mygpo import utils
from mygpo.data.mimetype import get_type, get_mimetype

register = template.Library()

@register.filter
def episode_status_text(episode):
    if not episode or not episode.action:
        return ''

    if episode.action == 'new':
        return _('New episode')
    elif episode.action == 'download':
        if episode.device.name:
            return _('Downloaded to %s') % episode.device.name
        else:
            return _('Downloaded')
    elif episode.action == 'play':
        if episode.device.name:
            return _('Played on %s') % episode.device.name
        else:
            return _('Played')
    elif episode.action == 'delete':
        if episode.device.name:
            return _('Deleted on %s') % episode.device.name
        else:
            return _('Deleted')

    return _('Unknown status')

@register.filter
def episode_status_icon(action):
    if not action or not action.action:
        s = '<img src="/media/nothing.png" alt="nothing" title="%s" />' % _('Unplayed episode')

    else:
        date_string   = (_(' on %s') % (action.timestamp)) if action.timestamp else ''
        device_string = (_(' on %s') % (action.device.name)) if action.device else ''

        if action.action == 'new':
            s = '<img src="/media/new.png" alt="new" title="%s" />' % ('%s%s%s' % (_('This episode has been marked new'),date_string, device_string))
        elif action.action == 'download':
            s = '<img src="/media/download.png" alt="downloaded" title="%s" />' % ('%s%s%s' % (_('This episode has been downloaded'),date_string, device_string))
        elif action.action == 'play':
            if action.playmark is not None:
                if action.started is not None:
                    playback_info = _(' from %(start)s to %(end)s') % { \
                            'start': utils.format_time(action.started), \
                            'end': utils.format_time(action.playmark)}
                else:
                    playback_info = _(' to position %s') % (\
                            utils.format_time(action.playmark),)
            else:
                playback_info = ''
            s = '<img src="/media/playback.png" alt="played" title="%s" />' % ('%s%s%s%s' % (_('This episode has been played'),date_string, device_string, playback_info))
        elif action.action == 'delete':
            s = '<img src="/media/delete.png" alt="deleted" title="%s"/>' % ('%s%s%s' % (_('This episode has been deleted'),date_string, device_string))
        else:
            return action.action #this is not marked safe by intention

    return mark_safe(s)


@register.filter
def is_image(episode):

    mimetype = get_mimetype(episode.mimetype, episode.url)
    return get_type(mimetype) == 'image'

