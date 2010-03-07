from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
import hashlib

register = template.Library()

@register.filter
def podcast_logo(podcast, size=32):
    if podcast.logo_url:
        sha = hashlib.sha1(podcast.logo_url).hexdigest()
        s = '<img src="/media/logo/%s" alt="%s" height="%s" width="%s" />' % (sha, _('Logo'), size, size)
    else:
        s = '<img src="/media/podcast-%d.png" alt="%s" height="%s" width="%s" />' % (hash(podcast.title)%5, _('No Logo available'), size, size)

    return mark_safe(s)

@register.filter
def podcast_status_icon(action):
    if action.action == 1:
        s = '<img src="/media/subscribe.png" />'
    else:
        s = '<img src="/media/unsubscribe.png" />'

    return mark_safe(s)


