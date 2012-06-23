from itertools import islice, imap as map

from mygpo.core.proxy import proxy_object
from mygpo.core.models import Podcast
from mygpo.directory.models import Category


class Topics(object):
    """ Provies topics -- categories """

    def __init__(self, num_categories, podcasts_per_topic):
        self.num_categories = num_categories
        self.podcasts_per_topic = podcasts_per_topic


    def __iter__(self):
        categories = Category.top_categories(self.num_categories)
        categories = map(self._prepare_category, categories)
        return categories


    def _prepare_category(self, category):
        category = proxy_object(category)
        category.podcasts = category.get_podcasts(0, self.podcasts_per_topic)
        return category
