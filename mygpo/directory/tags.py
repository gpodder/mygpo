from collections import defaultdict, namedtuple
from operator import itemgetter

from mygpo.core.models import Podcast
from mygpo.decorators import query_if_required
from mygpo.couch import get_main_database
from mygpo.utils import multi_request_view
from mygpo.counter import Counter
from mygpo.core.proxy import proxy_object
from mygpo.directory.models import Category
from mygpo.db.couchdb.podcast import podcasts_for_tag


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

        return podcasts_for_tag(self.tag)



TagCloudEntry = namedtuple('TagCloudEntry', 'label weight')


class Topics(object):

    def __init__(self, total=100, num_cat=10, podcasts_per_cat=10):
        self.total = total
        self.num_cat = num_cat
        self.podcasts_per_cat = podcasts_per_cat
        self._entries = None
        self._tag_cloud = None


    def _needs_query(self):
        return self._entries is None


    def _query(self):
        db = get_main_database()
        res = db.view('categories/by_weight',
                descending = True,
                limit      = self.total,
                stale      = 'update_after',
                include_docs = True,
            )

        self._entries = list(res)


    @property
    @query_if_required()
    def tagcloud(self):
        if not self._tag_cloud:
            self._tag_cloud = map(self._prepare_tagcloud_entry,
                self._entries[self.num_cat:])
            self._tag_cloud.sort(key = lambda x: x.label.lower())

        return self._tag_cloud


    def _prepare_tagcloud_entry(self, r):
        return TagCloudEntry(r['value'], r['key'])


    @query_if_required()
    def max_weight(self):
        return max([e.weight for e in self.tagcloud] + [0])


    @property
    @query_if_required()
    def categories(self):
        categories = map(self._prepare_category, self._entries[:self.num_cat])
        return categories


    def _prepare_category(self, resp):
        category = Category.wrap(resp['doc'])
        category = proxy_object(category)
        category.podcasts = category.get_podcasts(0, self.podcasts_per_cat)
        return category
