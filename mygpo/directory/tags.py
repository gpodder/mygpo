from collections import defaultdict, namedtuple

from mygpo.core.models import Podcast
from mygpo.decorators import query_if_required
from mygpo.directory.models import Category
from mygpo.utils import multi_request_view


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
    res = multi_request_view(Podcast, 'directory/podcasts_by_tag',
            startkey    = [tag, None],
            endkey      = [tag, 'ZZZZZZ'],
            reduce      = True,
            group       = True,
            group_level = 2
        )

    for r in res:
        yield (r['key'][1], r['value'])


def all_tags():
    res = multi_request_view(Podcast, 'directory/podcasts_by_tag',
            wrap        = False,
            reduce      = True,
            group       = True,
            group_level = 1
        )

    for r in res:
        yield r['key'][0]


TagCloudEntry = namedtuple('TagCloudEntry', 'label weight')


class TagCloud(object):

    def __init__(self, count=100, skip=0, sort_by_name=False):
        self.count = count
        self.skip = skip
        self._entries = None
        self.sort_by_name = sort_by_name

    def _needs_query(self):
        return self._entries is None

    def _query(self):
        db = Category.get_db()
        res = db.view('directory/categories', \
            descending=True, skip=self.skip, limit=self.count)

        mk_entry = lambda r: TagCloudEntry(r['value'], r['key'])
        self._entries = map(mk_entry, res)

        if self.sort_by_name:
            self._entries.sort(key = lambda x: x.label.lower())


    @property
    @query_if_required()
    def entries(self):
        return self._entries


    @property
    @query_if_required()
    def max_weight(self):
        return max([e.weight for e in self._entries] + [0])
