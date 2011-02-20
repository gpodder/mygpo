from collections import defaultdict
from mygpo.core.models import Podcast


# FIXME: this should be moved to User class once it is migrated to CouchDB
def tags_for_user(user, podcast_id=None):
    """
    Returns a dictionary that contains all podcasts tagged by the user as keys.
    For each podcast, a list of tags can be retrieved
    """

    res = Podcast.view('directory/tags_by_user', startkey=[user.id, podcast_id],
        endkey=[user.id, podcast_id or 'ZZZZZZ'])

    tags = defaultdict(list)
    for r in res:
        tags[r['key'][1]].append(r['value'])
    return tags


def podcasts_for_tag(tag):
    res = Podcast.view('directory/podcasts_by_tag', startkey=[tag, None], endkey=[tag, 'ZZZZZZ'], reduce=True, group=True, group_level=2)

    for r in res:
        yield (r['key'][1], r['value'])


def all_tags():
    res = Podcast.view('directory/podcasts_by_tag', reduce=True, group=True, group_level=1)

    for r in res:
        yield r['key'][0]
