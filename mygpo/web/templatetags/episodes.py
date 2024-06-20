from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.utils.html import strip_tags, format_html
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.safestring import mark_safe
from django.templatetags.static import static

from mygpo import utils
from mygpo.data.mimetype import get_type, get_mimetype
from mygpo.web.utils import get_episode_link_target

register = template.Library()

coverage_data = {}

def initialize_coverage():
    global coverage_data
    coverage_data = {
        'branch_1': 0,
        'branch_2': 0,
        'branch_3': 0,
        'branch_4': 0,
        'branch_5': 0,
        'branch_6': 0,
        'branch_7': 0,
        'branch_8': 0,
    }

def report_coverage():
    global coverage_data
    print("Coverage Report:")
    for branch, count in coverage_data.items():
        print(f"{branch}: {'Hit' if count > 0 else 'Missed'}")


@register.filter
def episode_status_text(episode):
    if not episode or not episode.action:
        return ""

    if episode.action == "new":
        return _("New episode")
    elif episode.action == "download":
        if episode.device.name:
            return _("Downloaded to %s") % episode.device.name
        else:
            return _("Downloaded")
    elif episode.action == "play":
        if episode.device.name:
            return _("Played on %s") % episode.device.name
        else:
            return _("Played")
    elif episode.action == "delete":
        if episode.device.name:
            return _("Deleted on %s") % episode.device.name
        else:
            return _("Deleted")

    return _("Unknown status")


@register.filter()
def episode_status_icon(action):
    global coverage_data

    if not action or not action.action:
        coverage_data['branch_1'] += 1
        s = '<img src="%s" alt="nothing" title="%s" />' % (
            staticfiles_storage.url("nothing.png"),
            _("Unplayed episode"),
        )

    else:
        coverage_data['branch_2'] += 1
        date_string = (_(" on %s") % (action.timestamp)) if action.timestamp else ""
        device_string = (_(" on %s") % (action.client.name)) if action.client else ""

        if action.action == "flattr":
            coverage_data['branch_3'] += 1
            s = (
                '<img src="https://flattr.com/_img/icons/flattr_logo_16.png" alt="flattr" title="%s" />'
                % (_("The episode has been flattr'd"),)
            )

        elif action.action == "new":
            coverage_data['branch_4'] += 1
            s = '<img src="%s" alt="new" title="%s" />' % (
                staticfiles_storage.url("new.png"),
                "%s%s%s"
                % (_("This episode has been marked new"), date_string, device_string),
            )
        elif action.action == "download":
            coverage_data['branch_5'] += 1
            s = '<img src="%s" alt="downloaded" title="%s" />' % (
                staticfiles_storage.url("download.png"),
                "%s%s%s"
                % (_("This episode has been downloaded"), date_string, device_string),
            )
        elif action.action == "play":
            coverage_data['branch_6'] += 1
            if action.stopped is not None:
                coverage_data['branch_7'] += 1
                if getattr(action, "started", None) is not None:
                    playback_info = _(" from %(start)s to %(end)s") % {
                        "start": utils.format_time(action.started),
                        "end": utils.format_time(action.stopped),
                    }
                else:
                    playback_info = _(" to position %s") % (
                        utils.format_time(action.stopped),
                    )
            else:
                coverage_data['branch_8'] += 1
                playback_info = ""
            s = '<img src="%s" alt="played" title="%s" />' % (
                staticfiles_storage.url("playback.png"),
                "%s%s%s%s"
                % (
                    _("This episode has been played"),
                    date_string,
                    device_string,
                    playback_info,
                ),
            )
        elif action.action == "delete":
            s = '<img src="%s" alt="deleted" title="%s"/>' % (
                staticfiles_storage.url("delete.png"),
                "%s%s%s"
                % (_("This episode has been deleted"), date_string, device_string),
            )
        else:
            return action.action  # this is not marked safe by intention

    return mark_safe(s)


@register.filter
def is_image(episode):
    mimetypes = episode.mimetypes.split(",")
    return any(get_type(mimetype) == "image" for mimetype in mimetypes)


class EpisodeLinkTargetNode(template.Node):
    """Links to a (view of a) Podcast"""

    def __init__(self, episode, podcast, view_name="episode", add_args=[]):
        self.episode = template.Variable(episode)
        self.podcast = template.Variable(podcast)
        self.view_name = view_name.replace('"', "")
        self.add_args = [template.Variable(arg) for arg in add_args]

    def render(self, context):
        episode = self.episode.resolve(context)
        podcast = self.podcast.resolve(context)
        add_args = [arg.resolve(context) for arg in self.add_args]
        return get_episode_link_target(episode, podcast, self.view_name, add_args)

    @staticmethod
    def compile(parser, token):
        try:
            contents = token.split_contents()
            tag_name = contents[0]
            episode = contents[1]
            podcast = contents[2]
            view_name = contents[3] if len(contents) > 3 else "episode"
            add_args = contents[4:]

        except ValueError:
            raise template.TemplateSyntaxError(
                "%r tag requires at least one argument" % token.contents.split()[0]
            )

        return EpisodeLinkTargetNode(episode, podcast, view_name, add_args)


register.tag("episode_link_target", EpisodeLinkTargetNode.compile)


@register.simple_tag
def episode_link(episode, podcast, title=None):
    """Returns the link for a single Episode"""

    title = (
        title
        or getattr(episode, "display_title", None)
        or episode.get_short_title(podcast.common_episode_title)
        or episode.title
        or _("Unknown Episode")
    )

    title = strip_tags(title)

    return format_html(
        '<a href="{target}" title="{title}">{title}</a>',
        target=get_episode_link_target(episode, podcast),
        title=title,
    )


@register.simple_tag
def get_id(obj):
    return obj._id


@register.simple_tag
def episode_number(episode, podcast):
    num = episode.get_episode_number(podcast.common_episode_title)
    return num or ""


@register.simple_tag
def episode_short_title(episode, podcast):
    title = episode.get_short_title(podcast.common_episode_title)
    return title or ""
