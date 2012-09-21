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
from mygpo.db.couchdb.directory import top_categories


class Tag(object):

    def __init__(self, tag):
        self.tag = tag


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
        self._entries = top_categories(self.total, wrap=False)


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
