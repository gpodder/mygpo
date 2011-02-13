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
