from collections import defaultdict, namedtuple, Counter
from operator import itemgetter
from datetime import datetime
from random import choice
from itertools import chain

from mygpo.core.models import Podcast
from mygpo.decorators import query_if_required, repeat_on_conflict
from mygpo.core.proxy import proxy_object
from mygpo.directory.models import Category
from mygpo.db.couchdb.podcast import podcasts_for_tag
from mygpo.db.couchdb.directory import top_categories, save_category, \
         category_for_tag_uncached


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
        self._categories = None
        self._tagcloud = None


    def _needs_query(self):
        return self._categories is None


    def _query(self):
        self._categories = []
        if self.num_cat > 0:
            self._categories = top_categories(0, self.num_cat, True)

        self._tagcloud = []
        if self.total-self.num_cat > 0:
            self._tagcloud = top_categories(self.num_cat, self.total-self.num_cat, False)


    @property
    @query_if_required()
    def tagcloud(self):
        self._tagcloud.sort(key = lambda x: x.label.lower())
        return self._tagcloud


    @query_if_required()
    def max_weight(self):
        return max([e.get_weight() for e in self.tagcloud] + [0])

    @query_if_required()
    def min_weight(self):
        return min([e.get_weight() for e in self.tagcloud])


    @property
    @query_if_required()
    def categories(self):
        return self._categories


    def _prepare_category(self, resp):
        category = Category.wrap(resp['doc'])
        category = proxy_object(category)
        category.podcasts = category.get_podcasts(0, self.podcasts_per_cat)
        return category



@repeat_on_conflict()
def update_category(podcast):
    all_tags = list(chain.from_iterable(s for s in podcast.tags.values()))

    if not all_tags:
        return

    random_tag = choice(all_tags)

    category = category_for_tag_uncached(random_tag)
    if not category:
        category = Category(label=random_tag)

    category.updated = datetime.utcnow()

    category.podcasts = category.podcasts[:999]

    # we don't need to CategoryEntry wrapper anymore
    if any(isinstance(x, dict) for x in category.podcasts):
        category.podcasts = filter(lambda x: isinstance(x, dict), category.podcasts)
        category.podcasts = [e['podcast'] for e in category.podcasts]

    if podcast.get_id() in category.podcasts:
        category.podcasts.remove(podcast.get_id())

    category.podcasts.insert(0, podcast.get_id())
    category.label = category.label.strip()

    save_category(category)
