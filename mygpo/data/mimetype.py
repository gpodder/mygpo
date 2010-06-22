from mygpo.api.models import Podcast, Episode
from collections import defaultdict
import mimetypes

# If 20% of the episodes of a podcast are of a given type,
# then the podcast is considered to be of that type, too
TYPE_THRESHOLD=.2


_ = lambda s: s

CONTENT_TYPES = (_('image'), _('audio'), _('video'))

def get_podcast_types(podcast):
    """Returns the types of a podcast

    A podcast is considered to be of a given types if the ratio of episodes that are of that type equals TYPE_THRESHOLD
    """
    episodes = Episode.objects.filter(podcast=podcast, mimetype__isnull=False)
    types = defaultdict()
    for e in episodes:
        t = get_type(e.mimetype)
        types[t] = types.get(t, 0) + 1

    max_episodes = sum(types.itervalues())
    l = list(types.iteritems())
    l.sort(key=lambda x: x[1], reverse=True)

    return [x[0] for x in filter(lambda x: max_episodes / float(x[1]) >= TYPE_THRESHOLD, l)]


def get_type(mimetype):
    """Returns the simplified type for the given mimetype

    All "wanted" mimetypes are mapped to one of audio/video/image
    Everything else returns None
    """
    if not mimetype:
        return None

    if '/' in mimetype:
        category, type = mimetype.split('/', 1)
        if category in ('audio', 'video', 'image'):
            return category
        elif type == 'ogg':
            return 'audio'
        elif type == 'x-youtube':
            return 'video'
    return None

def check_mimetype(mimetype):
    """Checks if the given mimetype can be processed by mygpo
    """
    if '/' in mimetype:
        category, type = mimetype.split('/', 1)
        if category in ('audio', 'video', 'image'):
            return True

        # application/ogg is a valid mime type for Ogg files
        # but we do not want to accept all files with application category
        if type in ('ogg', ):
            return True

        return False
    else:
        return False


def get_mimetype(mimetype, url):
    """Returns the mimetype; if None is given it tries to guess it"""

    if not mimetype:
        mimetype, _encoding = mimetypes.guess_type(url)

    return mimetype

