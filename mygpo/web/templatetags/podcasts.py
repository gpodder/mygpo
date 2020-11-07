import hashlib

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.html import strip_tags, format_html
from django.contrib.staticfiles.storage import staticfiles_storage

from mygpo.web.logo import get_logo_url
from mygpo.constants import (
    PODCAST_LOGO_SIZE,
    PODCAST_LOGO_BIG_SIZE,
    PODCAST_LOGO_MEDIUM_SIZE,
)
from mygpo.web.utils import get_podcast_link_target, get_podcast_group_link_target


register = template.Library()


@mark_safe
def create_podcast_logo(podcast, size):
    if not podcast:
        return ""

    size = int(size)
    return '<img src="%s" alt="" />' % (get_logo_url(podcast, size),)


@register.filter
def podcast_logo(podcast):
    return create_podcast_logo(podcast, PODCAST_LOGO_SIZE)


@register.filter
def podcast_logo_big(podcast):
    return create_podcast_logo(podcast, PODCAST_LOGO_BIG_SIZE)


@register.filter
def podcast_logo_medium(podcast):
    return create_podcast_logo(podcast, PODCAST_LOGO_MEDIUM_SIZE)


@register.filter()
def podcast_status_icon(action):
    s = ""
    if action.action == "subscribe":
        s = '<img src="%s" />' % (staticfiles_storage.url("subscribe.png"),)
    elif action.action == "unsubscribe":
        s = '<img src="%s" />' % (staticfiles_storage.url("unsubscribe.png"),)
    elif action.action == "flattr":
        s = '<img src="https://flattr.com/_img/icons/flattr_logo_16.png" />'
    else:
        s = ""

    return mark_safe(s)


@register.filter
def is_podcast(podcast):
    """ Returns True if the argument is a podcast (esp not a PodcastGroup) """
    from mygpo.podcasts.models import Podcast

    return isinstance(podcast, Podcast)


class PodcastLinkTargetNode(template.Node):
    """ Links to a (view of a) Podcast """

    def __init__(self, podcast, view_name, add_args):
        self.podcast = template.Variable(podcast)
        self.view_name = view_name.replace('"', "")
        self.add_args = [template.Variable(arg) for arg in add_args]

    def render(self, context):
        podcast = self.podcast.resolve(context)
        add_args = [arg.resolve(context) for arg in self.add_args]
        return get_podcast_link_target(podcast, self.view_name, add_args)

    @staticmethod
    def compile(parser, token):
        try:
            contents = token.split_contents()
            tag_name = contents[0]
            podcast = contents[1]
            view_name = contents[2] if len(contents) > 2 else "podcast"
            add_args = contents[3:]

        except ValueError:
            raise template.TemplateSyntaxError(
                "%r tag requires at least one argument" % token.contents.split()[0]
            )

        return PodcastLinkTargetNode(podcast, view_name, add_args)


register.tag("podcast_link_target", PodcastLinkTargetNode.compile)


class PodcastGroupLinkTargetNode(template.Node):
    """ Links to a (view of a) Podcast """

    def __init__(self, group, view_name, add_args):
        self.group = template.Variable(group)
        self.view_name = view_name.replace('"', "")
        self.add_args = [template.Variable(arg) for arg in add_args]

    def render(self, context):
        group = self.group.resolve(context)
        add_args = [arg.resolve(context) for arg in self.add_args]
        return get_podcast_group_link_target(podcast, self.view_name, add_args)

    @staticmethod
    def compile(parser, token):
        try:
            contents = token.split_contents()
            tag_name = contents[0]
            podcast = contents[1]
            view_name = contents[2] if len(contents) > 2 else "podcast"
            add_args = contents[3:]

        except ValueError:
            raise template.TemplateSyntaxError(
                "%r tag requires at least one argument" % token.contents.split()[0]
            )

        return PodcastLinkTargetNode(podcast, view_name, add_args)


register.tag("podcast_group_link_target", PodcastGroupLinkTargetNode.compile)


@register.simple_tag
def podcast_group_link(podcast, title=None):
    """Returns the link strings for Podcast and PodcastGroup objects

    automatically distinguishes between relational Podcast/PodcastGroup"""

    from mygpo.podcasts.models import PodcastGroup

    if isinstance(podcast, PodcastGroup):
        podcasts = list(podcast.podcast_set.all())
    else:
        return podcast_link(podcast, title)

    links = (podcast_link(p, p.group_member_name) for p in podcasts)
    link_text = " ".join(links)
    return "%(title)s (%(links)s)" % dict(title=podcast.title, links=link_text)


@register.simple_tag
def podcast_link(podcast, title=None):
    """ Returns the link for a single Podcast """

    title = title or podcast.display_title

    title = strip_tags(title)

    return format_html(
        '<a href="{target}" title="{title}">{title}</a>',
        target=get_podcast_link_target(podcast),
        title=title,
    )
