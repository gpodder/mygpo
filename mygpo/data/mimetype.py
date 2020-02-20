from collections import defaultdict

import mimetypes

from django.utils.translation import gettext_lazy as _


# If 20% of the episodes of a podcast are of a given type,
# then the podcast is considered to be of that type, too
TYPE_THRESHOLD = 0.2


CONTENT_TYPES = (_('image'), _('audio'), _('video'))


def get_podcast_types(episodes):
    """Returns the types of a podcast

    A podcast is considered to be of a given types if the ratio of episodes that are of that type equals TYPE_THRESHOLD
    """
    has_mimetype = lambda e: e.mimetypes
    episodes = filter(has_mimetype, episodes)
    types = defaultdict()
    for e in episodes:
        for mimetype in e.mimetypes:
            t = get_type(mimetype)
            if not t:
                continue
            types[t] = types.get(t, 0) + 1

    max_episodes = sum(types.values())
    l = list(types.items())
    l.sort(key=lambda x: x[1], reverse=True)

    return [
        x[0] for x in filter(lambda x: max_episodes / float(x[1]) >= TYPE_THRESHOLD, l)
    ]


def get_type(mimetype):
    """Returns the simplified type for the given mimetype

    All "wanted" mimetypes are mapped to one of audio/video/image
    Everything else returns None

    >>> get_type('audio/mpeg3')
    'audio'

    >>> get_type('video/mpeg')
    'video'

    >>> get_type('image/jpeg')
    'image'

    >>> get_type('application/ogg')
    'audio'

    >>> get_type('application/x-youtube')
    'video'

    >>> get_type('application/x-vimeo')
    'video'

    >>> get_type('application/octet-stream') == None
    True

    >>> get_type('') == None
    True

    >>> get_type('music') == None
    True
    """
    if not mimetype:
        return None

    if '/' not in mimetype:
        return None

    category, type = mimetype.split('/', 1)
    if category in ('audio', 'video', 'image'):
        return category
    elif type == 'ogg':
        return 'audio'
    elif type == 'x-youtube':
        return 'video'
    elif type == 'x-vimeo':
        return 'video'


def get_mimetype(mimetype, url):
    """Returns the mimetype; if None is given it tries to guess it"""

    if not mimetype:
        mimetype, _encoding = mimetypes.guess_type(url)

    return mimetype
