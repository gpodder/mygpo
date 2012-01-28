from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.html import strip_tags

from mygpo.core.models import Episode
from mygpo import utils
from mygpo.data.mimetype import get_type, get_mimetype
from mygpo.web.utils import get_episode_link_target


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
                if getattr(action, 'started', None) is not None:
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

    if isinstance(episode, Episode):
        mimetypes = episode.mimetypes

    else:
        mimetypes = [get_mimetype(episode.mimetype, episode.url)]

    return any(get_type(mimetype) == 'image' for mimetype in mimetypes)


class EpisodeLinkTargetNode(template.Node):
    """ Links to a (view of a) Podcast """

    def __init__(self, episode, podcast, view_name='episode', add_args=[]):
        self.episode = template.Variable(episode)
        self.podcast = template.Variable(podcast)
        self.view_name = view_name.replace('"', '')
        self.add_args = [template.Variable(arg) for arg in add_args]


    def render(self, context):
        episode = self.episode.resolve(context)
        podcast = self.podcast.resolve(context)
        add_args = [arg.resolve(context) for arg in self.add_args]
        return get_episode_link_target(episode, podcast, self.view_name, add_args)


    @staticmethod
    def compile(parser, token):
        try:
            contents  = token.split_contents()
            tag_name  = contents[0]
            episode   = contents[1]
            podcast   = contents[2]
            view_name = contents[3] if len(contents) > 3 else 'episode'
            add_args  = contents[4:]

        except ValueError:
            raise template.TemplateSyntaxError("%r tag requires at least one argument" % token.contents.split()[0])

        return EpisodeLinkTargetNode(episode, podcast, view_name, add_args)


register.tag('episode_link_target', EpisodeLinkTargetNode.compile)



@register.simple_tag
def episode_link(episode, podcast, title=None):
    """ Returns the link for a single Episode """

    title = title or getattr(episode, 'display_title', None) or \
            episode.title or _('Unknown Episode')

    title = strip_tags(title)

    return '<a href="%(target)s" title="%(title)s">%(title)s</a>' % \
        dict(target=get_episode_link_target(episode, podcast), title=title)
