from collections import defaultdict, namedtuple
from operator import itemgetter

from mygpo.core.models import Podcast
from mygpo.decorators import query_if_required
from mygpo.directory.models import Category
from mygpo.utils import multi_request_view
from mygpo.counter import Counter



class Tag(object):

    def __init__(self, tag):
        self.tag = tag


    @classmethod
    def for_podcast(cls, podcast):
        """ all tags for the podcast, in decreasing order of importance """

        res = Podcast.view('tags/by_podcast',
                startkey    = [podcast.get_id(), None],
                endkey      = [podcast.get_id(), {}],
                reduce      = True,
                group       = True,
                group_level = 2,
                stale       = 'update_after',
            )

        tags = Counter(dict((x['key'][1], x['value']) for x in res))

        res = Podcast.view('usertags/by_podcast',
                startkey    = [podcast.get_id(), None],
                endkey      = [podcast.get_id(), {}],
                reduce      = True,
                group       = True,
                group_level = 2,
            )

        tags.update(Counter(dict( (x['key'][1], x['value']) for x in res)))

        get_tag = itemgetter(0)
        return map(get_tag, tags.most_common())



    @classmethod
    def for_user(cls, user, podcast_id=None):
        """ mapping of all podcasts tagged by the user with a list of tags """

        res = Podcast.view('tags/by_user',
                startkey = [user._id, podcast_id],
                endkey   = [user._id, podcast_id or {}]
            )

        tags = defaultdict(list)
        for r in res:
            tags[r['key'][1]].append(r['value'])
        return tags


    @classmethod
    def all(cls):
        """ Returns all tags

        Some tags might be returned twice """
        res = multi_request_view(Podcast, 'podcasts/by_tag',
                wrap        = False,
                reduce      = True,
                group       = True,
                group_level = 1
            )

        for r in res:
            yield r['key'][0]

        res = multi_request_view(Podcast, 'usertags/podcasts',
                wrap        = False,
                reduce      = True,
                group       = True,
                group_level = 1
            )

        for r in res:
            yield r['key'][0]




    def get_podcasts(self):
        """ Returns the podcasts with the current tag.

        Some podcasts might be returned twice """

        res = multi_request_view(Podcast, 'podcasts/by_tag',
                wrap        = False,
                startkey    = [self.tag, None],
                endkey      = [self.tag, {}],
                reduce      = True,
                group       = True,
                group_level = 2
            )

        for r in res:
            yield (r['key'][1], r['value'])

        res = multi_request_view(Podcast, 'usertags/podcasts',
                wrap        = False,
                startkey    = [self.tag, None],
                endkey      = [self.tag, {}],
                reduce      = True,
                group       = True,
                group_level = 2
            )

        for r in res:
            yield (r['key'][1], r['value'])




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
        res = db.view('categories/by_weight',
                descending = True,
                skip       = self.skip,
                limit      = self.count,
                stale      = 'update_after',
            )

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
