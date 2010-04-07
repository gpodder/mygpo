from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
import hashlib

from mygpo.constants import PODCAST_LOGO_SIZE, PODCAST_LOGO_BIG_SIZE

register = template.Library()

def create_podcast_logo(podcast, size):
    size = int(size)
    if podcast.logo_url:
        sha = hashlib.sha1(podcast.logo_url).hexdigest()
        s = '<img src="/logo/%d/%s.jpg" alt="%s" height="%d" width="%d" />' % (size, sha, _('Logo'), size, size)
    else:
        s = '<img src="/media/podcast-%d.png" alt="%s" height="%d" width="%d" />' % (hash(podcast.title)%5, _('No Logo available'), size, size)

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


