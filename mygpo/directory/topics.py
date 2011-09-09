from itertools import islice, imap as map, chain

from mygpo.core.proxy import proxy_object
from mygpo.core.models import Podcast
from mygpo.share.models import PodcastList
from mygpo.directory.models import Category
from mygpo.users.models import User


class Topics(object):
    """ Provies topics -- either podcast lists or categories """

    def __init__(self, num_lists, num_categories, podcasts_per_topic,
            min_list_rating=5):
        self.num_lists = num_lists
        self.num_categories = num_categories
        self.podcasts_per_topic = podcasts_per_topic
        self.min_list_rating = min_list_rating


    def __iter__(self):
        lists = PodcastList.by_rating(self.min_list_rating)
        lists = islice(lists, 0, self.num_lists)
        lists = map(self._prepare_list, lists)

        categories = Category.top_categories(self.num_categories)
        categories = map(self._prepare_category, categories)

        return chain(lists, categories)


    def _prepare_list(self, l):
        podcasts = Podcast.get_multi(l.podcasts[:self.podcasts_per_topic])
        user = User.get(l.user)
        l = proxy_object(l)
        l.podcasts = podcasts
        l.username = user.username
        l.cls = "PodcastList"
        return l


    def _prepare_category(self, category):
        category = proxy_object(category)
        category.podcasts = category.get_podcasts(0, self.podcasts_per_topic)
        category.cls = "Category"
        return category
