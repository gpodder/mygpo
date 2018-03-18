import hashlib

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from mygpo.web.logo import get_logo_url
from mygpo.constants import PODCAST_LOGO_BIG_SIZE
from mygpo.web.templatetags.podcasts import create_podcast_logo
from mygpo.web.utils import get_episode_link_target, get_podcast_link_target


register = template.Library()

LIKE_BUTTON_STR = """<iframe class="fb_like" src="//www.facebook.com/plugins/like.php?href=%(url)s&amp;layout=button_count&amp;show_faces=false&amp;width=450&amp;action=like&amp;colorscheme=light&amp;height=21" scrolling="no" frameborder="0" style="border:none; overflow:hidden; width:450px; height:21px;" allowTransparency="true"></iframe>"""

#FIXME: remove hardcoded URL
# we could convert the filter to a tag once the takes_context
# paramter to register.simple_tag() is included in a release, see
# http://stackoverflow.com/questions/2160261/access-request-in-django-custom-template-tags
# http://docs.djangoproject.com/en/dev/howto/custom-template-tags/#shortcut-for-simple-tags

@register.simple_tag
@mark_safe
def fb_like_episode(episode, podcast):
    url = 'http://gpodder.net/%s' % get_episode_link_target(episode, podcast)
    s = LIKE_BUTTON_STR % dict(url=url)
    return s


@register.filter
@mark_safe
def fb_like_podcast(podcast):
    url = 'http://gpodder.net%s' % get_podcast_link_target(podcast)
    s = LIKE_BUTTON_STR % dict(url=url)
    return s



OPENGRAPH_STR = """
<meta property="og:title" content="%(title)s"/>
<meta property="og:type" content="%(type)s"/>
<meta property="og:image" content="%(image)s"/>
<meta property="og:url" content="%(url)s"/>
<meta property="og:site_name" content="%(site_name)s"/>
<meta property="og:admins" content="%(admins)s"/>
"""

@register.simple_tag
def opengraph_episode(episode, podcast):
    s = OPENGRAPH_STR % dict(
        title     = episode.title,
        type      = 'episode',
        image     = 'http://gpodder.net%s' % get_logo_url(podcast, PODCAST_LOGO_BIG_SIZE),
        url       = 'http://gpodder.net%s' % get_episode_link_target(episode, podcast),
        site_name = 'gpodder.net',
        admins    = '0'
    )
    return s

@register.filter(is_safe=True)
def opengraph_podcast(podcast):
    s = OPENGRAPH_STR % dict(
        title     = podcast.title,
        type      = 'episode',
        image     = 'http://gpodder.net%s' % get_logo_url(podcast, PODCAST_LOGO_BIG_SIZE),
        url       = 'http://gpodder.net%s' % get_podcast_link_target(podcast),
        site_name = 'gpodder.net',
        admins    = '0'
    )
    return s
