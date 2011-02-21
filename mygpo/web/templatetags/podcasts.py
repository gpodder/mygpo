from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
import hashlib

from mygpo.constants import PODCAST_LOGO_SIZE, PODCAST_LOGO_BIG_SIZE

register = template.Library()

def create_podcast_logo(podcast, size):
    size = int(size)
    s = '<img src="%s" alt="%s" height="%d" width="%d" />' % (podcast.get_logo_url(size), _('Logo'), size, size)
    return mark_safe(s)

@register.filter
def podcast_logo(podcast):
    return create_podcast_logo(podcast, PODCAST_LOGO_SIZE)

@register.filter
def podcast_logo_big(podcast):
    return create_podcast_logo(podcast, PODCAST_LOGO_BIG_SIZE)

@register.filter
def podcast_status_icon(action):
    if action.action == 1:
        s = '<img src="/media/subscribe.png" />'
    else:
        s = '<img src="/media/unsubscribe.png" />'

    return mark_safe(s)


@register.filter
def is_podcast(podcast):
    """ Returns True if the argument is a podcast (esp not a PodcastGroup) """
    from mygpo.core.models import Podcast
    return isinstance(podcast, Podcast)
