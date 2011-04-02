from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.html import strip_tags

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
    if action.action == 'subscribe':
        s = '<img src="/media/subscribe.png" />'
    else:
        s = '<img src="/media/unsubscribe.png" />'

    return mark_safe(s)


@register.filter
def is_podcast(podcast):
    """ Returns True if the argument is a podcast (esp not a PodcastGroup) """
    from mygpo.core.models import Podcast
    return isinstance(podcast, Podcast)


@register.simple_tag
def podcast_link_target(podcast):
    """ Returns the link-target for a Podcast, preferring slugs over Ids

    automatically distringuishes between relational Podcast objects and
    CouchDB-based Podcasts """

    from mygpo.api.models import Podcast as OldPodcast
    from mygpo.core.models import Podcast
    from django.core.urlresolvers import reverse

    if isinstance(podcast, OldPodcast):
        target = podcast.id
    # we can check for slugs, CouchDB-Ids here, too
    else:
        target = podcast.oldid

    return strip_tags(reverse('podcast', args=[target]))


@register.simple_tag
def podcast_group_link(podcast):
    """ Returns the link strings for Podcast and PodcastGroup objects

    automatically distringuishes between relational Podcast/PodcastGroup
    objects and CouchDB-based Podcast/PodcastGroup objects """

    from mygpo.api.models import PodcastGroup as OldPodcastGroup
    from mygpo.core.models import PodcastGroup

    if isinstance(podcast, OldPodcastGroup):
        podcasts = podcast.podcasts()
    elif isinstance(podcast, PodcastGroup):
        podcasts = list(podcast.podcasts)
    else:
        return podcast_link(podcast)

    links = (podcast_link(p, p.group_member_name) for p in podcasts)
    link_text = ' '.join(links)
    return '%(title)s (%(links)s)' % dict(title=podcast.title, links=link_text)


@register.simple_tag
def podcast_link(podcast, title=None):
    """ Returns the link for a single Podcast """

    title = title or podcast.group_member_name or \
        getattr(podcast, 'display_title', None) or podcast.title

    title = strip_tags(title)

    return '<a href="%(target)s" title="%(title)s">%(title)s</a>' % \
        dict(target=podcast_link_target(podcast), title=title)
