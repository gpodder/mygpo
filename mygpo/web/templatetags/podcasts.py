from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
import hashlib

register = template.Library()

@register.filter
def podcast_logo(podcast):
    if podcast.logo_url:
        sha = hashlib.sha1(podcast.logo_url).hexdigest()
        s = '<img src="/media/logo/%s" alt="%s" />' % (sha, _('Logo'))
    else:
        s = '<img src="/media/logo/default.png" alt="%s" />' % _('No Logo available')

    return mark_safe(s)

